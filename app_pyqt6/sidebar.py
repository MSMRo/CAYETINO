"""
=============================================================================
PROYECTO CAYETINO - BARRA LATERAL (sidebar.py)
Enlace de comunicación serial, selección de pin DAC y mantenimiento LittleFS
=============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from serial_comm import list_available_ports
from workers import ConnectWorker, FormatFSWorker


class SidebarWidget(QWidget):
    connection_changed = pyqtSignal(bool)
    dac_pin_changed = pyqtSignal(int)
    fs_formatted = pyqtSignal()

    def __init__(self, serial_client, parent=None):
        super().__init__(parent)
        self.client = serial_client
        self.connect_worker = None
        self.format_worker = None
        self.setObjectName("sidebar")

        self._setup_ui()
        self._connect_signals()
        self.refresh_ports()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 18, 15, 18)
        layout.setSpacing(14)

        # Branding
        title_lbl = QLabel("<h2>⚡ CAYETINO ESP32</h2>")
        title_lbl.setStyleSheet("color: #1E3A8A; margin-bottom: 0px;")
        sub_lbl = QLabel("Plataforma de Señales para<br>Ingeniería Biomédica")
        sub_lbl.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(line1)

        # Enlace de Comunicación
        link_title = QLabel("<b>🔌 Enlace de Comunicación</b>")
        link_title.setStyleSheet("font-size: 14px; color: #1E293B;")
        layout.addWidget(link_title)

        # Modo Simulación
        self.chk_simulation = QCheckBox("🧪 Modo Simulación (Sin hardware)")
        self.chk_simulation.setToolTip("Permite probar toda la plataforma y simular el ESP32 sin conectar placa física.")
        layout.addWidget(self.chk_simulation)

        # Puerto COM
        self.lbl_port = QLabel("Puerto Serial COM:")
        layout.addWidget(self.lbl_port)

        port_row = QHBoxLayout()
        self.cmb_ports = QComboBox()
        self.cmb_ports.setMinimumWidth(160)
        self.btn_refresh_ports = QPushButton("🔄")
        self.btn_refresh_ports.setToolTip("Refrescar lista de puertos COM")
        self.btn_refresh_ports.setFixedWidth(36)
        port_row.addWidget(self.cmb_ports, stretch=1)
        port_row.addWidget(self.btn_refresh_ports)
        layout.addLayout(port_row)

        # Baudrate
        self.lbl_baud = QLabel("Baudrate:")
        layout.addWidget(self.lbl_baud)
        self.cmb_baud = QComboBox()
        self.cmb_baud.addItems(["115200", "921600", "57600"])
        layout.addWidget(self.cmb_baud)

        # Botón Conectar / Desconectar
        self.btn_connect = QPushButton("🔗 Conectar")
        self.btn_connect.setObjectName("primaryBtn")
        self.btn_connect.setMinimumHeight(34)
        layout.addWidget(self.btn_connect)

        # Indicador de Estado
        status_row = QHBoxLayout()
        self.lbl_status_icon = QLabel("⚪")
        self.lbl_status_text = QLabel("Desconectado")
        self.lbl_status_text.setStyleSheet("font-weight: bold; color: #64748B;")
        status_row.addWidget(self.lbl_status_icon)
        status_row.addWidget(self.lbl_status_text)
        status_row.addStretch()
        layout.addLayout(status_row)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(line2)

        # Configuración DAC
        dac_box = QGroupBox("⚙️ Configuración del DAC")
        dac_layout = QVBoxLayout(dac_box)
        dac_layout.setSpacing(8)

        dac_sub = QLabel("Pin de salida analógica:")
        dac_sub.setStyleSheet("color: #475569; font-size: 11px;")
        dac_layout.addWidget(dac_sub)

        self.rb_gpio25 = QRadioButton("GPIO 25 (DAC Canal 1)")
        self.rb_gpio26 = QRadioButton("GPIO 26 (DAC Canal 2)")
        self.rb_gpio25.setChecked(True)

        self.btn_group_dac = QButtonGroup(self)
        self.btn_group_dac.addButton(self.rb_gpio25, 25)
        self.btn_group_dac.addButton(self.rb_gpio26, 26)

        dac_layout.addWidget(self.rb_gpio25)
        dac_layout.addWidget(self.rb_gpio26)

        self.btn_apply_dac = QPushButton("Aplicar Pin DAC")
        dac_layout.addWidget(self.btn_apply_dac)
        layout.addWidget(dac_box)

        # Mantenimiento LittleFS
        maint_box = QGroupBox("🛠️ Mantenimiento LittleFS")
        maint_layout = QVBoxLayout(maint_box)
        maint_layout.setSpacing(8)

        maint_sub = QLabel("Formatea la memoria Flash interna del ESP32 borrando todos los archivos guardados.")
        maint_sub.setWordWrap(True)
        maint_sub.setStyleSheet("color: #64748B; font-size: 11px;")
        maint_layout.addWidget(maint_sub)

        self.btn_format = QPushButton("⚠️ Formatear LittleFS")
        self.btn_format.setObjectName("dangerBtn")
        maint_layout.addWidget(self.btn_format)
        layout.addWidget(maint_box)

        layout.addStretch()

    def _connect_signals(self):
        self.chk_simulation.toggled.connect(self._on_sim_toggled)
        self.btn_refresh_ports.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self._on_connect_toggle)
        self.btn_apply_dac.clicked.connect(self._on_apply_dac)
        self.btn_format.clicked.connect(self._on_format_clicked)

    def refresh_ports(self):
        self.cmb_ports.clear()
        ports = list_available_ports()
        default_idx = 0
        for i, p in enumerate(ports):
            dev = p.get("device", "")
            desc = p.get("description", "")
            label = f"{dev} - {desc}" if desc and desc != dev else dev
            self.cmb_ports.addItem(label, userData=dev)
            if "CP210" in desc or "USB" in desc or "COM7" in dev:
                default_idx = i

        if ports:
            self.cmb_ports.setCurrentIndex(default_idx)
            self.btn_connect.setEnabled(True)
        else:
            self.cmb_ports.addItem("No hay puertos COM detectados", userData=None)
            if not self.chk_simulation.isChecked():
                self.btn_connect.setEnabled(False)

    def _on_sim_toggled(self, checked: bool):
        self.client.simulation_mode = checked
        self.lbl_port.setEnabled(not checked)
        self.cmb_ports.setEnabled(not checked)
        self.btn_refresh_ports.setEnabled(not checked)
        self.lbl_baud.setEnabled(not checked)
        self.cmb_baud.setEnabled(not checked)

        if checked:
            self.btn_connect.setEnabled(True)
            # Auto-conectar en simulación
            self.client.connect("VIRTUAL_ESP32")
            self._set_connected_state(True)
            self.connection_changed.emit(True)
        else:
            if self.client.port == "VIRTUAL_ESP32":
                self.client.disconnect()
                self._set_connected_state(False)
                self.connection_changed.emit(False)
            self.refresh_ports()

    def _on_connect_toggle(self):
        if self.client.is_connected():
            # Desconectar
            self.client.disconnect()
            self._set_connected_state(False)
            self.connection_changed.emit(False)
        else:
            # Conectar
            if self.chk_simulation.isChecked():
                self.client.connect("VIRTUAL_ESP32")
                self._set_connected_state(True)
                self.connection_changed.emit(True)
                return

            port = self.cmb_ports.currentData()
            if not port:
                QMessageBox.warning(self, "Aviso", "No se ha seleccionado ningún puerto COM válido.")
                return

            baud = int(self.cmb_baud.currentText())
            self.btn_connect.setEnabled(False)
            self.btn_connect.setText("Conectando...")

            self.connect_worker = ConnectWorker(self.client, port, baud)
            self.connect_worker.finished.connect(self._on_connect_finished)
            self.connect_worker.start()

    def _on_connect_finished(self, success: bool, msg: str):
        self.btn_connect.setEnabled(True)
        if success:
            self._set_connected_state(True)
            self.connection_changed.emit(True)
        else:
            self._set_connected_state(False)
            self.connection_changed.emit(False)
            QMessageBox.critical(self, "Error de Conexión", msg)

    def _set_connected_state(self, connected: bool):
        if connected:
            self.btn_connect.setText("❌ Desconectar")
            self.btn_connect.setObjectName("stopBtn")
            self.btn_connect.style().unpolish(self.btn_connect)
            self.btn_connect.style().polish(self.btn_connect)
            self.lbl_status_icon.setText("🟢")
            self.lbl_status_text.setText("Conectado")
            self.lbl_status_text.setStyleSheet("font-weight: bold; color: #166534;")
        else:
            self.btn_connect.setText("🔗 Conectar")
            self.btn_connect.setObjectName("primaryBtn")
            self.btn_connect.style().unpolish(self.btn_connect)
            self.btn_connect.style().polish(self.btn_connect)
            self.lbl_status_icon.setText("⚪")
            self.lbl_status_text.setText("Desconectado")
            self.lbl_status_text.setStyleSheet("font-weight: bold; color: #64748B;")

    def _on_apply_dac(self):
        pin = self.get_active_dac_pin()
        if self.client.is_connected():
            self.client.set_dac_pin(pin)
            QMessageBox.information(self, "Éxito", f"Pin de salida analógica configurado en GPIO {pin}.")
        else:
            QMessageBox.information(self, "Aviso", f"Pin seleccionado: GPIO {pin} (se aplicará al conectar).")
        self.dac_pin_changed.emit(pin)

    def _on_format_clicked(self):
        if not self.client.is_connected():
            QMessageBox.warning(self, "Aviso", "Debes conectar el ESP32 primero.")
            return

        reply = QMessageBox.warning(
            self,
            "⚠️ Formatear LittleFS",
            "¿Estás seguro de que deseas formatear toda la memoria Flash interna del ESP32?\n\n"
            "Esta acción borrará de forma irreversible todos los archivos de señales grabados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.btn_format.setEnabled(False)
            self.btn_format.setText("Formateando...")
            self.format_worker = FormatFSWorker(self.client)
            self.format_worker.finished.connect(self._on_format_finished)
            self.format_worker.start()

    def _on_format_finished(self, success: bool, msg: str):
        self.btn_format.setEnabled(True)
        self.btn_format.setText("⚠️ Formatear LittleFS")
        if success:
            QMessageBox.information(self, "Memoria Formateada", msg)
            self.fs_formatted.emit()
        else:
            QMessageBox.critical(self, "Error al Formatear", msg)

    def get_active_dac_pin(self) -> int:
        return self.btn_group_dac.checkedId()
