"""
=============================================================================
PROYECTO CAYETINO - VENTANA PRINCIPAL (main_window.py)
Integración de barra lateral, pestañas de control, gráficas y notificaciones
=============================================================================
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QTabWidget, QFrame, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt

from serial_comm import CayetinoSerial
from sidebar import SidebarWidget
from tab_basic import TabBasicWave
from tab_advanced import TabAdvancedBio
from tab_manager import TabManager
from tab_guide import TabGuide


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cayetino - Generador de Señales Biomédicas ESP32")
        self.resize(1280, 850)
        self.setMinimumSize(1024, 680)

        # Cliente de comunicación Serial compartido
        self.serial_client = CayetinoSerial(simulation_mode=False)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter principal para permitir redimensionar la barra lateral
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Barra lateral izquierda
        self.sidebar = SidebarWidget(self.serial_client, self)
        self.sidebar.setMinimumWidth(260)
        self.sidebar.setMaximumWidth(320)
        splitter.addWidget(self.sidebar)

        # Contenedor derecho (Header + Pestañas)
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #F8FAFC;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(10)

        # Notificación flotante / Toast (inicialmente oculta)
        self.toast_frame = QFrame()
        self.toast_frame.setObjectName("toastSuccess")
        self.toast_frame.setVisible(False)
        toast_layout = QHBoxLayout(self.toast_frame)
        toast_layout.setContentsMargins(10, 8, 10, 8)
        self.lbl_toast = QLabel("")
        self.lbl_toast.setStyleSheet("font-weight: 600; color: #1E3A8A;")
        self.btn_close_toast = QPushButton("✕")
        self.btn_close_toast.setFixedSize(24, 24)
        self.btn_close_toast.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #64748B;")
        self.btn_close_toast.clicked.connect(lambda: self.toast_frame.setVisible(False))
        toast_layout.addWidget(self.lbl_toast, stretch=1)
        toast_layout.addWidget(self.btn_close_toast)
        right_layout.addWidget(self.toast_frame)

        # Encabezado Principal
        header_title = QLabel("⚡ Proyecto CAYETINO")
        header_title.setStyleSheet("font-size: 26px; font-weight: 800; color: #1E3A8A;")
        header_subtitle = QLabel(
            "Generador de Señales Sintéticas y Biomédicas con almacenamiento en LittleFS "
            "y salida analógica por DAC del ESP32"
        )
        header_subtitle.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 4px;")
        right_layout.addWidget(header_title)
        right_layout.addWidget(header_subtitle)

        # Pestañas principales
        self.tabs = QTabWidget()

        # Instanciar cada pestaña
        self.tab_basic = TabBasicWave(self.serial_client, self)
        self.tab_adv = TabAdvancedBio(self.serial_client, self)
        self.tab_manager = TabManager(
            self.serial_client,
            get_dac_pin_func=self.sidebar.get_active_dac_pin,
            parent=self
        )
        self.tab_guide = TabGuide(self)

        self.tabs.addTab(self.tab_basic, "📊 Modo Básico (Ondas Periódicas)")
        self.tabs.addTab(self.tab_adv, "🧬 Modo Avanzado (Biomédico & NeuroKit2)")
        self.tabs.addTab(self.tab_manager, "💾 Gestor de Archivos & DAC ESP32")
        self.tabs.addTab(self.tab_guide, "🔌 Hardware & Guía Biomédica")

        right_layout.addWidget(self.tabs, stretch=1)

        splitter.addWidget(right_container)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        # Eventos de guardado de archivo en las pestañas -> refrescar lista en gestor y mostrar notificación
        self.tab_basic.file_saved.connect(self._on_file_saved)
        self.tab_adv.file_saved.connect(self._on_file_saved)

        # Eventos de conexión en sidebar
        self.sidebar.connection_changed.connect(self._on_connection_changed)
        self.sidebar.dac_pin_changed.connect(self._on_dac_pin_changed)
        self.sidebar.fs_formatted.connect(self._on_fs_formatted)

    def _on_file_saved(self, msg: str):
        self.lbl_toast.setText(msg)
        self.toast_frame.setVisible(True)
        # Actualizar lista de archivos en el gestor
        self.tab_manager.refresh_file_list()

    def _on_connection_changed(self, connected: bool):
        if connected:
            self.tab_manager.refresh_file_list()
        else:
            self.tab_manager.table.setRowCount(0)
            self.tab_manager.cmb_files.clear()
            self.tab_manager._update_banner({"playing": False, "filename": "", "fs": 0})

    def _on_dac_pin_changed(self, pin: int):
        self.tab_manager._poll_status()

    def _on_fs_formatted(self):
        self.tab_manager.refresh_file_list()
        self.lbl_toast.setText("ℹ️ Memoria LittleFS formateada. Todos los archivos han sido eliminados.")
        self.toast_frame.setVisible(True)
