"""
=============================================================================
PROYECTO CAYETINO - PESTAÑA MODO BÁSICO (tab_basic.py)
Formas de onda periódicas fundamentales, previsualización dual y guardado LittleFS
=============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QDoubleSpinBox, QSpinBox, QSlider, QLineEdit,
    QPushButton, QProgressBar, QFrame, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import pyqtgraph as pg
import numpy as np

from signal_generator import generate_basic_signal, map_to_dac_8bit
from workers import SaveSignalWorker


class TabBasicWave(QWidget):
    file_saved = pyqtSignal(str)  # Emite cuando se guarda exitosamente un archivo

    def __init__(self, serial_client, parent=None):
        super().__init__(parent)
        self.client = serial_client
        self.save_worker = None
        self._is_updating = False

        # Datos actuales de señal calculada
        self.current_t = np.array([])
        self.current_y = np.array([])
        self.current_dac = np.array([])
        self.current_volt = np.array([])

        self._setup_ui()
        self._setup_plots()
        self._connect_signals()

        # Generar señal inicial
        self.update_signal()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Encabezado
        header_lbl = QLabel("<h3>📊 Generador de Formas de Onda Básicas</h3>")
        header_sub = QLabel("Genera señales periódicas fundamentales y envíalas directamente a la memoria flash del ESP32 para su reproducción analógica.")
        header_sub.setStyleSheet("color: #475569;")
        main_layout.addWidget(header_lbl)
        main_layout.addWidget(header_sub)

        # Panel de controles dividido en 2 columnas
        ctrl_frame = QFrame()
        ctrl_frame.setObjectName("metricCard")
        ctrl_layout = QGridLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(12, 12, 12, 12)
        ctrl_layout.setHorizontalSpacing(20)
        ctrl_layout.setVerticalSpacing(8)

        # Columna 1: Forma y parámetros
        grp1_title = QLabel("<b>1. Tipo y Parámetros de Onda</b>")
        grp1_title.setStyleSheet("color: #1E3A8A;")
        ctrl_layout.addWidget(grp1_title, 0, 0, 1, 2)

        ctrl_layout.addWidget(QLabel("Forma de Onda:"), 1, 0)
        self.cmb_wave = QComboBox()
        self.cmb_wave.addItems([
            "Senoidal",
            "Triángulo",
            "Cuadrada",
            "Diente de Sierra",
            "Diente de Sierra Invertida"
        ])
        ctrl_layout.addWidget(self.cmb_wave, 1, 1)

        ctrl_layout.addWidget(QLabel("Frecuencia (Hz):"), 2, 0)
        self.spn_freq = QDoubleSpinBox()
        self.spn_freq.setRange(0.1, 500.0)
        self.spn_freq.setValue(5.0)
        self.spn_freq.setSingleStep(0.5)
        self.spn_freq.setSuffix(" Hz")
        ctrl_layout.addWidget(self.spn_freq, 2, 1)

        ctrl_layout.addWidget(QLabel("Amplitud normalizada:"), 3, 0)
        amp_layout = QHBoxLayout()
        self.sld_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_amp.setRange(10, 100)
        self.sld_amp.setValue(100)
        self.lbl_amp_val = QLabel("1.00")
        self.lbl_amp_val.setFixedWidth(35)
        amp_layout.addWidget(self.sld_amp)
        amp_layout.addWidget(self.lbl_amp_val)
        ctrl_layout.addLayout(amp_layout, 3, 1)

        ctrl_layout.addWidget(QLabel("Offset / Nivel DC:"), 4, 0)
        off_layout = QHBoxLayout()
        self.sld_offset = QSlider(Qt.Orientation.Horizontal)
        self.sld_offset.setRange(-100, 100)
        self.sld_offset.setValue(0)
        self.lbl_offset_val = QLabel("0.00")
        self.lbl_offset_val.setFixedWidth(35)
        off_layout.addWidget(self.sld_offset)
        off_layout.addWidget(self.lbl_offset_val)
        ctrl_layout.addLayout(off_layout, 4, 1)

        self.lbl_duty = QLabel("Ciclo de trabajo (Duty):")
        self.lbl_duty.setVisible(False)
        ctrl_layout.addWidget(self.lbl_duty, 5, 0)
        self.duty_layout = QHBoxLayout()
        self.sld_duty = QSlider(Qt.Orientation.Horizontal)
        self.sld_duty.setRange(5, 95)
        self.sld_duty.setValue(50)
        self.lbl_duty_val = QLabel("0.50")
        self.lbl_duty_val.setFixedWidth(35)
        self.duty_layout.addWidget(self.sld_duty)
        self.duty_layout.addWidget(self.lbl_duty_val)
        self.duty_container = QWidget()
        self.duty_container.setLayout(self.duty_layout)
        self.duty_container.setVisible(False)
        ctrl_layout.addWidget(self.duty_container, 5, 1)

        # Columna 2: Muestreo y Métricas
        grp2_title = QLabel("<b>2. Parámetros Temporales y Muestreo</b>")
        grp2_title.setStyleSheet("color: #1E3A8A;")
        ctrl_layout.addWidget(grp2_title, 0, 2, 1, 2)

        ctrl_layout.addWidget(QLabel("Frecuencia de muestreo Fs:"), 1, 2)
        self.spn_fs = QSpinBox()
        self.spn_fs.setRange(50, 20000)
        self.spn_fs.setValue(500)
        self.spn_fs.setSingleStep(50)
        self.spn_fs.setSuffix(" Hz")
        ctrl_layout.addWidget(self.spn_fs, 1, 3)

        ctrl_layout.addWidget(QLabel("Tiempo de ventana T:"), 2, 2)
        self.spn_dur = QDoubleSpinBox()
        self.spn_dur.setRange(0.1, 10.0)
        self.spn_dur.setValue(2.0)
        self.spn_dur.setSingleStep(0.5)
        self.spn_dur.setSuffix(" s")
        ctrl_layout.addWidget(self.spn_dur, 2, 3)

        # Tarjetas de Métricas
        self.lbl_samples_metric = QLabel("1,000 muestras")
        self.lbl_samples_metric.setStyleSheet("font-size: 18px; font-weight: bold; color: #2563EB;")
        ctrl_layout.addWidget(QLabel("Total de Muestras a Enviar:"), 3, 2)
        ctrl_layout.addWidget(self.lbl_samples_metric, 3, 3)

        self.lbl_timing_caption = QLabel("⏱️ Período: 2.00 ms | Ciclos en ventana: 10.0")
        self.lbl_timing_caption.setStyleSheet("color: #64748B; font-size: 11px;")
        ctrl_layout.addWidget(self.lbl_timing_caption, 4, 2, 1, 2)

        main_layout.addWidget(ctrl_frame)

        # Contenedor Gráfico (PyQtGraph)
        self.plot_container = QWidget()
        plot_layout = QVBoxLayout(self.plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.plot_container, stretch=1)

        # Panel de Guardado en ESP32
        save_box = QGroupBox("💾 Guardar Señal Básica en LittleFS del ESP32")
        save_layout = QGridLayout(save_box)
        save_layout.setContentsMargins(12, 14, 12, 12)
        save_layout.setHorizontalSpacing(15)

        save_layout.addWidget(QLabel("Nombre del archivo:"), 0, 0)
        self.txt_filename = QLineEdit("senoidal_5hz")
        save_layout.addWidget(self.txt_filename, 0, 1)

        save_layout.addWidget(QLabel("Extensión:"), 0, 2)
        self.cmb_ext = QComboBox()
        self.cmb_ext.addItems([".csv", ".txt", ".dat"])
        save_layout.addWidget(self.cmb_ext, 0, 3)

        self.btn_send = QPushButton("🚀 Enviar y Guardar en ESP32")
        self.btn_send.setObjectName("primaryBtn")
        self.btn_send.setMinimumHeight(34)
        save_layout.addWidget(self.btn_send, 0, 4)

        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        self.prog_bar.setVisible(False)
        save_layout.addWidget(self.prog_bar, 1, 0, 1, 5)

        self.lbl_save_status = QLabel("")
        self.lbl_save_status.setStyleSheet("font-weight: 500;")
        save_layout.addWidget(self.lbl_save_status, 2, 0, 1, 5)

        main_layout.addWidget(save_box)

    def _setup_plots(self):
        pg.setConfigOptions(antialias=True)
        self.win = pg.GraphicsLayoutWidget()
        self.win.setBackground("#FFFFFF")

        # Subgráfico 1: Tensión Analógica DAC (0.0 V - 3.3 V)
        self.p1 = self.win.addPlot(row=0, col=0)
        self.p1.setTitle("<b>Tensión Analógica Generada en DAC (0.0 V - 3.3 V)</b>", color="#1E3A8A", size="11pt")
        self.p1.setLabel("left", "Voltios", units="V", color="#1E293B")
        self.p1.showGrid(x=True, y=True, alpha=0.3)
        self.p1.setYRange(0.0, 3.4, padding=0)
        self.curve_volt = self.p1.plot(pen=pg.mkPen(color="#2563EB", width=2))

        # Subgráfico 2: Cuantización DAC 8 bits (0 - 255)
        self.p2 = self.win.addPlot(row=1, col=0)
        self.p2.setTitle("<b>Valores Cuantizados DAC 8-Bit (0 - 255)</b>", color="#1E3A8A", size="11pt")
        self.p2.setLabel("left", "DAC (0-255)", color="#1E293B")
        self.p2.setLabel("bottom", "Tiempo", units="s", color="#1E293B")
        self.p2.showGrid(x=True, y=True, alpha=0.3)
        self.p2.setYRange(0, 260, padding=0)
        self.curve_dac = self.p2.plot(pen=pg.mkPen(color="#10B981", width=2))

        # Sincronizar ejes X
        self.p2.setXLink(self.p1)

        layout = self.plot_container.layout()
        layout.addWidget(self.win)

    def _connect_signals(self):
        self.cmb_wave.currentIndexChanged.connect(self._on_wave_changed)
        self.spn_freq.valueChanged.connect(self.update_signal)
        self.sld_amp.valueChanged.connect(self._on_amp_slider)
        self.sld_offset.valueChanged.connect(self._on_offset_slider)
        self.sld_duty.valueChanged.connect(self._on_duty_slider)
        self.spn_fs.valueChanged.connect(self.update_signal)
        self.spn_dur.valueChanged.connect(self.update_signal)
        self.btn_send.clicked.connect(self._on_send_clicked)

    def _on_wave_changed(self):
        wave_name = self.cmb_wave.currentText()
        is_sq = (wave_name == "Cuadrada")
        self.lbl_duty.setVisible(is_sq)
        self.duty_container.setVisible(is_sq)
        self._update_default_filename()
        self.update_signal()

    def _on_amp_slider(self, val):
        self.lbl_amp_val.setText(f"{val/100.0:.2f}")
        self.update_signal()

    def _on_offset_slider(self, val):
        self.lbl_offset_val.setText(f"{val/100.0:.2f}")
        self.update_signal()

    def _on_duty_slider(self, val):
        self.lbl_duty_val.setText(f"{val/100.0:.2f}")
        self.update_signal()

    def _update_default_filename(self):
        wave = self.cmb_wave.currentText().lower().replace(" ", "_")
        freq = int(self.spn_freq.value())
        self.txt_filename.setText(f"{wave}_{freq}hz")

    def update_signal(self):
        if self._is_updating:
            return
        self._is_updating = True
        try:
            wave_text = self.cmb_wave.currentText()
            type_map = {
                "Senoidal": "senoidal",
                "Triángulo": "triangulo",
                "Cuadrada": "cuadrada",
                "Diente de Sierra": "diente_sierra",
                "Diente de Sierra Invertida": "diente_sierra_inv"
            }
            sig_type = type_map.get(wave_text, "senoidal")
            freq = self.spn_freq.value()
            amp = self.sld_amp.value() / 100.0
            offset = self.sld_offset.value() / 100.0
            duty = self.sld_duty.value() / 100.0
            fs = self.spn_fs.value()
            dur = self.spn_dur.value()

            # Métrica
            total_samples = int(np.round(fs * dur))
            self.lbl_samples_metric.setText(f"{total_samples:,} muestras")
            period_ms = 1000.0 / fs if fs > 0 else 0
            cycles = freq * dur
            self.lbl_timing_caption.setText(f"⏱️ Período de muestreo: {period_ms:.2f} ms | Ciclos en ventana: {cycles:.1f}")

            t, y = generate_basic_signal(
                signal_type=sig_type,
                freq=freq,
                fs=fs,
                duration=dur,
                amplitude=amp,
                offset=offset,
                duty_cycle=duty
            )

            dac_vals, volt_vals = map_to_dac_8bit(y, auto_scale=True)

            self.current_t = t
            self.current_y = y
            self.current_dac = dac_vals
            self.current_volt = volt_vals

            # Actualizar curvas en gráfico
            self.curve_volt.setData(t, volt_vals)
            self.curve_dac.setData(t, dac_vals)
            self.p1.setXRange(0, dur, padding=0.01)

        finally:
            self._is_updating = False

    def _on_send_clicked(self):
        if not self.client.is_connected():
            self.lbl_save_status.setStyleSheet("color: #DC2626; font-weight: bold;")
            self.lbl_save_status.setText("❌ El ESP32 no está conectado. Conéctalo desde la barra lateral o activa el Modo Simulación.")
            return

        name = self.txt_filename.text().strip()
        if not name:
            name = "senal_basica"
        ext = self.cmb_ext.currentText().strip()
        full_name = name + ext

        self.btn_send.setEnabled(False)
        self.prog_bar.setVisible(True)
        self.prog_bar.setValue(0)
        self.lbl_save_status.setStyleSheet("color: #2563EB;")
        self.lbl_save_status.setText(f"Transmitiendo '{full_name}' hacia LittleFS...")

        self.save_worker = SaveSignalWorker(
            client=self.client,
            filename=full_name,
            fs=self.spn_fs.value(),
            dac_values=self.current_dac
        )
        self.save_worker.progress.connect(self._on_save_progress)
        self.save_worker.finished.connect(self._on_save_finished)
        self.save_worker.start()

    def _on_save_progress(self, percent: int, msg: str):
        self.prog_bar.setValue(percent)
        self.lbl_save_status.setText(msg)

    def _on_save_finished(self, success: bool, msg: str):
        self.btn_send.setEnabled(True)
        if success:
            self.prog_bar.setValue(100)
            self.lbl_save_status.setStyleSheet("color: #059669; font-weight: bold;")
            self.lbl_save_status.setText(f"✅ {msg}")
            self.file_saved.emit(msg)
        else:
            self.lbl_save_status.setStyleSheet("color: #DC2626; font-weight: bold;")
            self.lbl_save_status.setText(f"⚠️ {msg}")
