"""
=============================================================================
PROYECTO CAYETINO - GESTOR DE ARCHIVOS Y REPRODUCTOR DAC (tab_manager.py)
Explorador de LittleFS, emisión analógica en bucle y diagnóstico directo
=============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QPushButton, QFrame, QGroupBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from workers import (
    ListFilesWorker, PlayFileWorker, StopWorker,
    DeleteFileWorker, TestSineWorker
)


class TabManager(QWidget):
    status_updated = pyqtSignal(dict)

    def __init__(self, serial_client, get_dac_pin_func, parent=None):
        super().__init__(parent)
        self.client = serial_client
        self.get_dac_pin = get_dac_pin_func

        self.files_cache = []
        self.current_status = {"playing": False, "filename": "", "fs": 0}

        # Subprocesos activos
        self.list_worker = None
        self.play_worker = None
        self.stop_worker = None
        self.del_worker = None
        self.test_worker = None

        self._setup_ui()
        self._connect_signals()

        # Timer para consulta periódica de estado si está conectado
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2000)
        self.poll_timer.timeout.connect(self._poll_status)
        self.poll_timer.start()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Encabezado
        header_lbl = QLabel("<h3>💾 Gestor de Archivos en LittleFS y Control DAC</h3>")
        header_sub = QLabel("Visualiza todos los archivos de señales grabados en la memoria Flash del ESP32 y selecciona cuál emitir por el DAC.")
        header_sub.setStyleSheet("color: #475569;")
        main_layout.addWidget(header_lbl)
        main_layout.addWidget(header_sub)

        # Banner de Estado en Vivo
        self.status_banner = QFrame()
        self.status_banner.setObjectName("statusIdle")
        banner_layout = QHBoxLayout(self.status_banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        self.lbl_status = QLabel("⏹️ ESP32 EN ESPERA: DAC en nivel neutro (~1.65 V) | Pin: GPIO 25")
        self.lbl_status.setStyleSheet("font-weight: 600; font-size: 13px;")
        banner_layout.addWidget(self.lbl_status)
        main_layout.addWidget(self.status_banner)

        # Card de Archivos en LittleFS
        file_box = QGroupBox("📁 Archivos Disponibles en Memoria Flash (LittleFS)")
        file_box_layout = QVBoxLayout(file_box)
        file_box_layout.setContentsMargins(12, 14, 12, 12)
        file_box_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_refresh = QPushButton("🔄 Actualizar Lista")
        top_bar.addWidget(self.btn_refresh)
        file_box_layout.addLayout(top_bar)

        # Tabla de Archivos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Archivo", "Fs (Hz)", "Muestras", "Duración (s)", "Tamaño Flash"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        file_box_layout.addWidget(self.table, stretch=1)

        # Panel de Controles de Reproducción
        ctrl_section = QFrame()
        ctrl_layout = QVBoxLayout(ctrl_section)
        ctrl_layout.setContentsMargins(0, 5, 0, 0)
        ctrl_layout.setSpacing(8)

        sel_lbl = QLabel("<b>🎛️ Seleccionar Archivo para Controlar:</b>")
        sel_lbl.setStyleSheet("color: #1E3A8A;")
        ctrl_layout.addWidget(sel_lbl)

        sel_bar = QHBoxLayout()
        sel_bar.addWidget(QLabel("Archivo a emitir por el DAC:"))
        self.cmb_files = QComboBox()
        self.cmb_files.setMinimumWidth(250)
        sel_bar.addWidget(self.cmb_files, stretch=1)
        ctrl_layout.addLayout(sel_bar)

        # Botones de Acción
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        self.btn_play = QPushButton("▶️ REPRODUCIR (PLAY)")
        self.btn_play.setObjectName("playBtn")
        self.btn_play.setMinimumHeight(36)
        btn_bar.addWidget(self.btn_play, stretch=2)

        self.btn_stop = QPushButton("⏹️ DETENER (STOP)")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setMinimumHeight(36)
        btn_bar.addWidget(self.btn_stop, stretch=1)

        self.btn_del = QPushButton("🗑️ Eliminar Archivo")
        self.btn_del.setObjectName("dangerBtn")
        self.btn_del.setMinimumHeight(36)
        btn_bar.addWidget(self.btn_del, stretch=1)

        ctrl_layout.addLayout(btn_bar)
        file_box_layout.addWidget(ctrl_section)

        main_layout.addWidget(file_box, stretch=1)

        # Sección de Diagnóstico
        diag_box = QGroupBox("🔬 Diagnóstico y Verificación de Hardware Directa")
        diag_layout = QHBoxLayout(diag_box)
        diag_layout.setContentsMargins(12, 12, 12, 12)
        diag_layout.setSpacing(15)

        diag_desc = QLabel(
            "Genera una onda senoidal pura de 5 Hz (0 - 3.3V) directamente desde la RAM del ESP32 "
            "sin leer archivos de memoria Flash, ideal para comprobar el cableado con el osciloscopio o Raspberry Pi Pico."
        )
        diag_desc.setWordWrap(True)
        diag_desc.setStyleSheet("color: #475569;")
        diag_layout.addWidget(diag_desc, stretch=3)

        self.btn_test_sine = QPushButton("🧪 Probar DAC con Seno 5 Hz")
        self.btn_test_sine.setMinimumHeight(36)
        diag_layout.addWidget(self.btn_test_sine, stretch=1)

        main_layout.addWidget(diag_box)

    def _connect_signals(self):
        self.btn_refresh.clicked.connect(self.refresh_file_list)
        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_del.clicked.connect(self._on_delete_clicked)
        self.btn_test_sine.clicked.connect(self._on_test_sine_clicked)
        self.table.itemSelectionChanged.connect(self._on_table_row_selected)

    def _on_table_row_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            filename_item = self.table.item(row, 0)
            if filename_item:
                fname = filename_item.text()
                idx = self.cmb_files.findText(fname)
                if idx >= 0:
                    self.cmb_files.setCurrentIndex(idx)

    def refresh_file_list(self):
        if not self.client.is_connected():
            self.table.setRowCount(0)
            self.cmb_files.clear()
            return

        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("🔄 Leyendo...")

        self.list_worker = ListFilesWorker(self.client)
        self.list_worker.finished.connect(self._on_files_listed)
        self.list_worker.start()

    def _on_files_listed(self, success: bool, files: list, msg: str):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Actualizar Lista")

        if success:
            self.files_cache = files
            self._render_table(files)
        self._poll_status()

    def _render_table(self, files: list):
        self.table.setRowCount(len(files))
        self.cmb_files.clear()

        for row, f in enumerate(files):
            fname = f.get("name", "")
            self.cmb_files.addItem(fname)

            # Columnas
            item_name = QTableWidgetItem(fname)
            item_fs = QTableWidgetItem(str(f.get("fs", 0)))
            item_samples = QTableWidgetItem(f"{f.get('samples', 0):,}")
            item_dur = QTableWidgetItem(f"{f.get('duration', 0.0):.2f} s")
            size_kb = f.get("size_bytes", 0) / 1024.0
            item_size = QTableWidgetItem(f"{size_kb:.2f} KB")

            # Centrar números
            item_fs.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_samples.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_fs)
            self.table.setItem(row, 2, item_samples)
            self.table.setItem(row, 3, item_dur)
            self.table.setItem(row, 4, item_size)

    def _on_play_clicked(self):
        if not self.client.is_connected():
            QMessageBox.warning(self, "Aviso", "Conecta el ESP32 primero o activa el Modo Simulación.")
            return

        fname = self.cmb_files.currentText().strip()
        if not fname:
            QMessageBox.information(self, "Aviso", "No hay ningún archivo seleccionado para reproducir.")
            return

        self.btn_play.setEnabled(False)
        self.play_worker = PlayFileWorker(self.client, fname)
        self.play_worker.finished.connect(self._on_play_finished)
        self.play_worker.start()

    def _on_play_finished(self, success: bool, res: dict, msg: str):
        self.btn_play.setEnabled(True)
        if success:
            self.current_status = {
                "playing": True,
                "filename": res.get("filename", ""),
                "fs": res.get("fs", 0)
            }
            self._update_banner(self.current_status)
        else:
            QMessageBox.critical(self, "Error de Reproducción", msg)

    def _on_stop_clicked(self):
        if not self.client.is_connected():
            return

        self.btn_stop.setEnabled(False)
        self.stop_worker = StopWorker(self.client)
        self.stop_worker.finished.connect(self._on_stop_finished)
        self.stop_worker.start()

    def _on_stop_finished(self, success: bool, msg: str):
        self.btn_stop.setEnabled(True)
        self.current_status = {"playing": False, "filename": "", "fs": 0}
        self._update_banner(self.current_status)

    def _on_delete_clicked(self):
        if not self.client.is_connected():
            QMessageBox.warning(self, "Aviso", "Conecta el ESP32 primero.")
            return

        fname = self.cmb_files.currentText().strip()
        if not fname:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente '{fname}' de LittleFS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.del_worker = DeleteFileWorker(self.client, fname)
            self.del_worker.finished.connect(self._on_delete_finished)
            self.del_worker.start()

    def _on_delete_finished(self, success: bool, msg: str):
        if success:
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "Error al eliminar", msg)

    def _on_test_sine_clicked(self):
        if not self.client.is_connected():
            QMessageBox.warning(self, "Aviso", "Conecta el ESP32 primero.")
            return

        self.btn_test_sine.setEnabled(False)
        self.test_worker = TestSineWorker(self.client)
        self.test_worker.finished.connect(self._on_test_sine_finished)
        self.test_worker.start()

    def _on_test_sine_finished(self, success: bool, res: dict, msg: str):
        self.btn_test_sine.setEnabled(True)
        if success:
            self.current_status = {
                "playing": True,
                "filename": "TEST_SENO_5HZ",
                "fs": res.get("fs", 500)
            }
            self._update_banner(self.current_status)
        else:
            QMessageBox.critical(self, "Error en Test Sine", msg)

    def _poll_status(self):
        if not self.client.is_connected():
            self._update_banner({"playing": False, "filename": "", "fs": 0})
            return

        try:
            stat = self.client.get_status()
            self.current_status = stat
            self._update_banner(stat)
        except Exception:
            pass

    def _update_banner(self, stat: dict):
        pin = self.get_dac_pin()
        if stat.get("playing", False):
            self.status_banner.setObjectName("statusActive")
            self.lbl_status.setText(
                f"▶️ REPRODUCIENDO EN VIVO POR DAC: <b>{stat.get('filename')}</b> | "
                f"Fs: {stat.get('fs')} Hz | Pin: GPIO {pin} (Bucle Continuo Activo)"
            )
            self.lbl_status.setStyleSheet("color: #166534; font-weight: 600; font-size: 13px;")
        else:
            self.status_banner.setObjectName("statusIdle")
            self.lbl_status.setText(
                f"⏹️ ESP32 EN ESPERA: DAC en nivel neutro (~1.65 V) | Pin: GPIO {pin}"
            )
            self.lbl_status.setStyleSheet("color: #475569; font-weight: 600; font-size: 13px;")

        # Refrescar estilo de QSS dinámico
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)
