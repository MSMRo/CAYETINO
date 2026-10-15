"""
=============================================================================
PROYECTO CAYETINO - PESTAÑA MODO AVANZADO BIOMÉDICO (tab_advanced.py)
Síntesis fisiológica con NeuroKit2, contaminación y análisis espectral FFT
=============================================================================
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QDoubleSpinBox, QSpinBox, QSlider, QLineEdit,
    QPushButton, QProgressBar, QFrame, QGroupBox, QCheckBox,
    QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import pyqtgraph as pg
import numpy as np

from signal_generator import generate_biomedical_signal, contaminate_signal, map_to_dac_8bit
from workers import SaveSignalWorker


class TabAdvancedBio(QWidget):
    file_saved = pyqtSignal(str)

    def __init__(self, serial_client, parent=None):
        super().__init__(parent)
        self.client = serial_client
        self.save_worker = None
        self._is_updating = False

        # Timer debounce para cálculo fluido
        self.calc_timer = QTimer(self)
        self.calc_timer.setSingleShot(True)
        self.calc_timer.setInterval(200)
        self.calc_timer.timeout.connect(self._compute_and_render)

        # Datos en memoria
        self.current_t = np.array([])
        self.current_clean = np.array([])
        self.current_noisy = np.array([])
        self.current_dac = np.array([])
        self.current_volt = np.array([])

        self._setup_ui()
        self._setup_plots()
        self._connect_signals()

        self._update_contextual_controls()
        self.schedule_update()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Encabezado
        header_lbl = QLabel("<h3>🧬 Modo Avanzado: Señales Biomédicas Sintéticas (NeuroKit2)</h3>")
        header_sub = QLabel(
            "Genera señales fisiológicas realistas mediante la librería especializada <b>NeuroKit2</b> "
            "e incorpora fuentes reales de contaminación (ruido blanco, armónico de red a 60 Hz y spikes)."
        )
        header_sub.setStyleSheet("color: #475569;")
        main_layout.addWidget(header_lbl)
        main_layout.addWidget(header_sub)

        # Parámetros superiores en 2 columnas
        param_frame = QFrame()
        param_frame.setObjectName("metricCard")
        param_layout = QGridLayout(param_frame)
        param_layout.setContentsMargins(12, 12, 12, 12)
        param_layout.setHorizontalSpacing(20)
        param_layout.setVerticalSpacing(8)

        # Columna 1: Configuración Fisiológica
        bio_title = QLabel("<b>1. Configuración de Señal Fisiológica</b>")
        bio_title.setStyleSheet("color: #1E3A8A;")
        param_layout.addWidget(bio_title, 0, 0, 1, 2)

        param_layout.addWidget(QLabel("Tipo de Señal:"), 1, 0)
        self.cmb_bio_type = QComboBox()
        self.cmb_bio_type.addItems([
            "EKG / ECG (Electrocardiograma)",
            "EMG (Electromiografía)",
            "EEG (Electroencefalograma - Ritmos cerebrales)",
            "RSP (Señal Respiratoria)",
            "PPG (Fotopletismografía / Pulso de Oximetría)"
        ])
        param_layout.addWidget(self.cmb_bio_type, 1, 1)

        # Parámetros EKG/PPG
        self.lbl_hr = QLabel("Frecuencia Cardíaca (BPM):")
        param_layout.addWidget(self.lbl_hr, 2, 0)
        self.hr_layout = QHBoxLayout()
        self.sld_hr = QSlider(Qt.Orientation.Horizontal)
        self.sld_hr.setRange(40, 180)
        self.sld_hr.setValue(72)
        self.lbl_hr_val = QLabel("72")
        self.lbl_hr_val.setFixedWidth(30)
        self.hr_layout.addWidget(self.sld_hr)
        self.hr_layout.addWidget(self.lbl_hr_val)
        self.hr_container = QWidget()
        self.hr_container.setLayout(self.hr_layout)
        param_layout.addWidget(self.hr_container, 2, 1)

        self.lbl_method = QLabel("Modelo de síntesis:")
        param_layout.addWidget(self.lbl_method, 3, 0)
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["ecgsyn (Dinámico McSharry)", "simple"])
        param_layout.addWidget(self.cmb_method, 3, 1)

        # Parámetros EMG
        self.lbl_bursts = QLabel("N° contracciones (bursts):")
        param_layout.addWidget(self.lbl_bursts, 2, 0)
        self.spn_bursts = QSpinBox()
        self.spn_bursts.setRange(1, 10)
        self.spn_bursts.setValue(3)
        param_layout.addWidget(self.spn_bursts, 2, 1)

        self.lbl_burst_dur = QLabel("Duración contracción (s):")
        param_layout.addWidget(self.lbl_burst_dur, 3, 0)
        self.spn_burst_dur = QDoubleSpinBox()
        self.spn_burst_dur.setRange(0.2, 2.0)
        self.spn_burst_dur.setValue(0.6)
        self.spn_burst_dur.setSingleStep(0.1)
        self.spn_burst_dur.setSuffix(" s")
        param_layout.addWidget(self.spn_burst_dur, 3, 1)

        # Columna 2: Frecuencia de muestreo y duración
        win_title = QLabel("<b>2. Ventana de Tiempo y Frecuencia de Muestreo</b>")
        win_title.setStyleSheet("color: #1E3A8A;")
        param_layout.addWidget(win_title, 0, 2, 1, 2)

        param_layout.addWidget(QLabel("Frecuencia de muestreo Fs:"), 1, 2)
        self.cmb_fs = QComboBox()
        self.cmb_fs.addItems(["250 Hz", "500 Hz", "1000 Hz", "2000 Hz"])
        param_layout.addWidget(self.cmb_fs, 1, 3)

        param_layout.addWidget(QLabel("Ventana en bucle T:"), 2, 2)
        self.spn_dur = QDoubleSpinBox()
        self.spn_dur.setRange(1.0, 15.0)
        self.spn_dur.setValue(5.0)
        self.spn_dur.setSingleStep(1.0)
        self.spn_dur.setSuffix(" s")
        param_layout.addWidget(self.spn_dur, 2, 3)

        # Métricas
        self.lbl_samples_metric = QLabel("1,250 muestras")
        self.lbl_samples_metric.setStyleSheet("font-size: 17px; font-weight: bold; color: #2563EB;")
        param_layout.addWidget(QLabel("Muestras de la Ventana:"), 3, 2)
        param_layout.addWidget(self.lbl_samples_metric, 3, 3)

        self.lbl_flash_size = QLabel("💾 Tamaño estimado en Flash: ~7.3 KB")
        self.lbl_flash_size.setStyleSheet("color: #64748B; font-size: 11px;")
        param_layout.addWidget(self.lbl_flash_size, 4, 2, 1, 2)

        main_layout.addWidget(param_frame)

        # Panel de Contaminación y Ruido (3 columnas)
        noise_box = QGroupBox("🌫️ Opciones de Contaminación y Ruido")
        noise_layout = QHBoxLayout(noise_box)
        noise_layout.setContentsMargins(10, 10, 10, 10)
        noise_layout.setSpacing(15)

        # 1. Ruido Senoidal de Red
        col_n1 = QFrame()
        col_n1.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        l1 = QVBoxLayout(col_n1)
        self.chk_sine_noise = QCheckBox("⚡ Interferencia de Red Eléctrica")
        l1.addWidget(self.chk_sine_noise)
        self.frame_n1 = QWidget()
        fl1 = QGridLayout(self.frame_n1)
        fl1.setContentsMargins(0, 0, 0, 0)
        fl1.addWidget(QLabel("Frecuencia:"), 0, 0)
        self.spn_sine_f = QDoubleSpinBox()
        self.spn_sine_f.setRange(10.0, 200.0)
        self.spn_sine_f.setValue(60.0)
        self.spn_sine_f.setSuffix(" Hz")
        fl1.addWidget(self.spn_sine_f, 0, 1)
        fl1.addWidget(QLabel("Amplitud:"), 1, 0)
        self.sld_sine_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_sine_amp.setRange(1, 80)
        self.sld_sine_amp.setValue(25)
        self.lbl_sine_amp = QLabel("0.25")
        fl1.addWidget(self.sld_sine_amp, 1, 1)
        fl1.addWidget(self.lbl_sine_amp, 1, 2)
        l1.addWidget(self.frame_n1)
        self.frame_n1.setEnabled(False)
        noise_layout.addWidget(col_n1)

        # 2. Ruido Blanco
        col_n2 = QFrame()
        col_n2.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        l2 = QVBoxLayout(col_n2)
        self.chk_white_noise = QCheckBox("🌫️ Ruido Blanco Gaussiano")
        l2.addWidget(self.chk_white_noise)
        self.frame_n2 = QWidget()
        fl2 = QGridLayout(self.frame_n2)
        fl2.setContentsMargins(0, 0, 0, 0)
        fl2.addWidget(QLabel("Desviación (σ):"), 0, 0)
        self.sld_white_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_white_amp.setRange(1, 50)
        self.sld_white_amp.setValue(8)
        self.lbl_white_amp = QLabel("0.08")
        fl2.addWidget(self.sld_white_amp, 0, 1)
        fl2.addWidget(self.lbl_white_amp, 0, 2)
        l2.addWidget(self.frame_n2)
        self.frame_n2.setEnabled(False)
        noise_layout.addWidget(col_n2)

        # 3. Ruido Impulsional
        col_n3 = QFrame()
        col_n3.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        l3 = QVBoxLayout(col_n3)
        self.chk_impulse_noise = QCheckBox("📍 Ruido Impulsional (Spikes)")
        l3.addWidget(self.chk_impulse_noise)
        self.frame_n3 = QWidget()
        fl3 = QGridLayout(self.frame_n3)
        fl3.setContentsMargins(0, 0, 0, 0)
        fl3.addWidget(QLabel("Probabilidad:"), 0, 0)
        self.sld_impulse_prob = QSlider(Qt.Orientation.Horizontal)
        self.sld_impulse_prob.setRange(1, 50)
        self.sld_impulse_prob.setValue(8)
        self.lbl_impulse_prob = QLabel("0.8%")
        fl3.addWidget(self.sld_impulse_prob, 0, 1)
        fl3.addWidget(self.lbl_impulse_prob, 0, 2)
        fl3.addWidget(QLabel("Amplitud:"), 1, 0)
        self.sld_impulse_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_impulse_amp.setRange(20, 200)
        self.sld_impulse_amp.setValue(80)
        self.lbl_impulse_amp = QLabel("0.80")
        fl3.addWidget(self.sld_impulse_amp, 1, 1)
        fl3.addWidget(self.lbl_impulse_amp, 1, 2)
        l3.addWidget(self.frame_n3)
        self.frame_n3.setEnabled(False)
        noise_layout.addWidget(col_n3)

        main_layout.addWidget(noise_box)

        # Pestañas de Gráficas: Temporal y Espectral (FFT)
        self.plot_tabs = QTabWidget()
        self.tab_time_plots = QWidget()
        self.tab_fft_plot = QWidget()
        self.plot_tabs.addTab(self.tab_time_plots, "📈 Trazado Temporal (Limpia, Contaminada & DAC)")
        self.plot_tabs.addTab(self.tab_fft_plot, "📊 Análisis Espectral en Frecuencia (FFT)")
        main_layout.addWidget(self.plot_tabs, stretch=1)

        # Guardado en ESP32
        save_box = QGroupBox("💾 Guardar Señal Biomédica en LittleFS del ESP32")
        save_layout = QGridLayout(save_box)
        save_layout.setContentsMargins(12, 14, 12, 12)
        save_layout.setHorizontalSpacing(15)

        save_layout.addWidget(QLabel("Nombre del archivo:"), 0, 0)
        self.txt_filename = QLineEdit("ekg_5s")
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

        # Pestaña Temporal
        time_layout = QVBoxLayout(self.tab_time_plots)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.win_time = pg.GraphicsLayoutWidget()
        self.win_time.setBackground("#FFFFFF")

        self.p_comp = self.win_time.addPlot(row=0, col=0)
        self.p_comp.setTitle("<b>Comparativa: Señal Sintética Limpia vs. Contaminada</b>", color="#1E3A8A", size="11pt")
        self.p_comp.setLabel("left", "Amplitud Fisiológica", color="#1E293B")
        self.p_comp.showGrid(x=True, y=True, alpha=0.3)
        self.p_comp.addLegend(offset=(10, 10))
        self.curve_clean = self.p_comp.plot(pen=pg.mkPen(color="#059669", width=2), name="Señal Limpia")
        self.curve_noisy = self.p_comp.plot(pen=pg.mkPen(color="#DC2626", width=1.5), name="Señal Contaminada")

        self.p_dac = self.win_time.addPlot(row=1, col=0)
        self.p_dac.setTitle("<b>Señal Analógica Cuantizada de Salida DAC (0.0 V - 3.3 V)</b>", color="#1E3A8A", size="11pt")
        self.p_dac.setLabel("left", "Voltios", units="V", color="#1E293B")
        self.p_dac.setLabel("bottom", "Tiempo", units="s", color="#1E293B")
        self.p_dac.showGrid(x=True, y=True, alpha=0.3)
        self.p_dac.setYRange(0.0, 3.4, padding=0)
        self.curve_dac = self.p_dac.plot(pen=pg.mkPen(color="#2563EB", width=2), name="Salida DAC")

        self.p_dac.setXLink(self.p_comp)
        time_layout.addWidget(self.win_time)

        # Pestaña FFT
        fft_layout = QVBoxLayout(self.tab_fft_plot)
        fft_layout.setContentsMargins(0, 0, 0, 0)
        self.win_fft = pg.GraphicsLayoutWidget()
        self.win_fft.setBackground("#FFFFFF")

        self.p_fft = self.win_fft.addPlot(row=0, col=0)
        self.p_fft.setTitle("<b>Densidad Espectral de Amplitud (FFT)</b>", color="#1E3A8A", size="11pt")
        self.p_fft.setLabel("left", "Magnitud", color="#1E293B")
        self.p_fft.setLabel("bottom", "Frecuencia", units="Hz", color="#1E293B")
        self.p_fft.showGrid(x=True, y=True, alpha=0.3)
        self.p_fft.addLegend(offset=(10, 10))
        self.curve_fft_clean = self.p_fft.plot(pen=pg.mkPen(color="#059669", width=2), name="Espectro Limpio")
        self.curve_fft_noisy = self.p_fft.plot(pen=pg.mkPen(color="#DC2626", width=1.5), name="Espectro Contaminado")

        fft_layout.addWidget(self.win_fft)

    def _connect_signals(self):
        self.cmb_bio_type.currentIndexChanged.connect(self._on_bio_type_changed)
        self.sld_hr.valueChanged.connect(self._on_hr_changed)
        self.cmb_method.currentIndexChanged.connect(self.schedule_update)
        self.spn_bursts.valueChanged.connect(self.schedule_update)
        self.spn_burst_dur.valueChanged.connect(self.schedule_update)
        self.cmb_fs.currentIndexChanged.connect(self.schedule_update)
        self.spn_dur.valueChanged.connect(self.schedule_update)

        # Ruidos
        self.chk_sine_noise.toggled.connect(self._on_sine_toggled)
        self.spn_sine_f.valueChanged.connect(self.schedule_update)
        self.sld_sine_amp.valueChanged.connect(self._on_sine_amp_changed)

        self.chk_white_noise.toggled.connect(self._on_white_toggled)
        self.sld_white_amp.valueChanged.connect(self._on_white_amp_changed)

        self.chk_impulse_noise.toggled.connect(self._on_impulse_toggled)
        self.sld_impulse_prob.valueChanged.connect(self._on_impulse_prob_changed)
        self.sld_impulse_amp.valueChanged.connect(self._on_impulse_amp_changed)

        self.btn_send.clicked.connect(self._on_send_clicked)

    def _on_bio_type_changed(self):
        self._update_contextual_controls()
        self._update_default_filename()
        self.schedule_update()

    def _update_contextual_controls(self):
        text = self.cmb_bio_type.currentText()
        is_cardio = ("EKG" in text or "PPG" in text)
        is_emg = ("EMG" in text)

        self.lbl_hr.setVisible(is_cardio)
        self.hr_container.setVisible(is_cardio)
        self.lbl_method.setVisible(is_cardio)
        self.cmb_method.setVisible(is_cardio)

        self.lbl_bursts.setVisible(is_emg)
        self.spn_bursts.setVisible(is_emg)
        self.lbl_burst_dur.setVisible(is_emg)
        self.spn_burst_dur.setVisible(is_emg)

    def _on_hr_changed(self, val):
        self.lbl_hr_val.setText(str(val))
        self.schedule_update()

    def _on_sine_toggled(self, checked):
        self.frame_n1.setEnabled(checked)
        self._update_default_filename()
        self.schedule_update()

    def _on_sine_amp_changed(self, val):
        self.lbl_sine_amp.setText(f"{val/100.0:.2f}")
        self.schedule_update()

    def _on_white_toggled(self, checked):
        self.frame_n2.setEnabled(checked)
        self._update_default_filename()
        self.schedule_update()

    def _on_white_amp_changed(self, val):
        self.lbl_white_amp.setText(f"{val/100.0:.2f}")
        self.schedule_update()

    def _on_impulse_toggled(self, checked):
        self.frame_n3.setEnabled(checked)
        self._update_default_filename()
        self.schedule_update()

    def _on_impulse_prob_changed(self, val):
        self.lbl_impulse_prob.setText(f"{val/10.0:.1f}%")
        self.schedule_update()

    def _on_impulse_amp_changed(self, val):
        self.lbl_impulse_amp.setText(f"{val/100.0:.2f}")
        self.schedule_update()

    def _get_fs_value(self) -> int:
        txt = self.cmb_fs.currentText()
        return int(txt.replace(" Hz", "").strip())

    def _get_bio_key(self) -> str:
        text = self.cmb_bio_type.currentText()
        if "EKG" in text: return "ekg"
        if "EMG" in text: return "emg"
        if "EEG" in text: return "eeg"
        if "RSP" in text: return "rsp"
        if "PPG" in text: return "ppg"
        return "ekg"

    def _update_default_filename(self):
        bio = self._get_bio_key()
        dur = int(self.spn_dur.value())
        suffix = ""
        if self.chk_sine_noise.isChecked():
            suffix += f"_ruido{int(self.spn_sine_f.value())}hz"
        if self.chk_white_noise.isChecked():
            suffix += "_blanco"
        if self.chk_impulse_noise.isChecked():
            suffix += "_spikes"
        self.txt_filename.setText(f"{bio}_{dur}s{suffix}")

    def schedule_update(self):
        self.calc_timer.start()

    def _compute_and_render(self):
        if self._is_updating:
            return
        self._is_updating = True

        try:
            bio_key = self._get_bio_key()
            fs = self._get_fs_value()
            dur = self.spn_dur.value()
            hr = self.sld_hr.value()
            burst_n = self.spn_bursts.value()
            burst_d = self.spn_burst_dur.value()
            method = "ecgsyn" if "ecgsyn" in self.cmb_method.currentText() else "simple"

            # Ruido
            sine_amp = (self.sld_sine_amp.value() / 100.0) if self.chk_sine_noise.isChecked() else 0.0
            sine_f = self.spn_sine_f.value()
            white_amp = (self.sld_white_amp.value() / 100.0) if self.chk_white_noise.isChecked() else 0.0
            impulse_prob = (self.sld_impulse_prob.value() / 1000.0) if self.chk_impulse_noise.isChecked() else 0.0
            impulse_amp = (self.sld_impulse_amp.value() / 100.0) if self.chk_impulse_noise.isChecked() else 0.0

            # Métricas
            total_samples = int(np.round(fs * dur))
            self.lbl_samples_metric.setText(f"{total_samples:,} muestras")
            est_kb = (total_samples * 6) / 1024.0
            self.lbl_flash_size.setText(f"💾 Tamaño estimado en Flash: ~{est_kb:.1f} KB")

            # Síntesis
            t, y_clean = generate_biomedical_signal(
                bio_type=bio_key,
                fs=fs,
                duration=dur,
                heart_rate=hr,
                burst_number=burst_n,
                burst_duration=burst_d,
                method=method
            )

            y_noisy = contaminate_signal(
                signal=y_clean,
                fs=fs,
                white_noise_amp=white_amp,
                sine_noise_amp=sine_amp,
                sine_noise_freq=sine_f,
                impulse_noise_prob=impulse_prob,
                impulse_noise_amp=impulse_amp
            )

            dac_vals, volt_vals = map_to_dac_8bit(y_noisy, auto_scale=True)

            self.current_t = t
            self.current_clean = y_clean
            self.current_noisy = y_noisy
            self.current_dac = dac_vals
            self.current_volt = volt_vals

            # Curvas temporales
            self.curve_clean.setData(t, y_clean)
            has_noise = (sine_amp > 0 or white_amp > 0 or impulse_amp > 0)
            if has_noise:
                self.curve_noisy.setData(t, y_noisy)
                self.curve_noisy.setVisible(True)
            else:
                self.curve_noisy.clear()
                self.curve_noisy.setVisible(False)

            self.curve_dac.setData(t, volt_vals)
            self.p_comp.setXRange(0, dur, padding=0.01)

            # FFT
            n_fft = len(y_noisy)
            freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
            mag_clean = np.abs(np.fft.rfft(y_clean)) / n_fft
            mag_noisy = np.abs(np.fft.rfft(y_noisy)) / n_fft

            max_f = min(120.0, fs / 2.0)
            mask = freqs <= max_f

            self.curve_fft_clean.setData(freqs[mask], mag_clean[mask])
            if has_noise:
                self.curve_fft_noisy.setData(freqs[mask], mag_noisy[mask])
                self.curve_fft_noisy.setVisible(True)
            else:
                self.curve_fft_noisy.clear()
                self.curve_fft_noisy.setVisible(False)

            self.p_fft.setXRange(0, max_f, padding=0.02)

        finally:
            self._is_updating = False

    def _on_send_clicked(self):
        if not self.client.is_connected():
            self.lbl_save_status.setStyleSheet("color: #DC2626; font-weight: bold;")
            self.lbl_save_status.setText("❌ El ESP32 no está conectado. Conéctalo desde la barra lateral o activa el Modo Simulación.")
            return

        name = self.txt_filename.text().strip()
        if not name:
            name = "bio_signal"
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
            fs=self._get_fs_value(),
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
