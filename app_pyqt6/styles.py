"""
=============================================================================
PROYECTO CAYETINO - ESTILOS VISUALES PYQT6 (styles.py)
Diseño moderno, biomédico y profesional inspirado en Streamlit UI
=============================================================================
"""

MODERN_QSS = """
/* Estilos Globales */
QWidget {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QMainWindow, QDialog {
    background-color: #F8FAFC;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #F1F5F9;
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #CBD5E1;
    min-width: 25px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Sidebar / Barra Lateral */
#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

/* Cards y Grupos */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 14px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 10px;
    font-weight: 600;
    color: #1E3A8A;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    background-color: #FFFFFF;
    color: #1E3A8A;
    font-size: 13px;
}

/* Pestañas (QTabWidget) */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background: #F1F5F9;
    color: #475569;
    padding: 10px 18px;
    font-weight: 600;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    border: 1px solid #E2E8F0;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: #FFFFFF;
    color: #1E3A8A;
    border-top: 3px solid #2563EB;
}

QTabBar::tab:hover:!selected {
    background: #E2E8F0;
    color: #1E293B;
}

/* Botones */
QPushButton {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Botón Primario (Azul) */
QPushButton#primaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #1D4ED8;
}
QPushButton#primaryBtn:pressed {
    background-color: #1E40AF;
}
QPushButton#primaryBtn:disabled {
    background-color: #93C5FD;
    color: #E0E7FF;
}

/* Botón Acción Destacada / Play (Rojo/Coral) */
QPushButton#playBtn {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    font-size: 14px;
}
QPushButton#playBtn:hover {
    background-color: #DC2626;
}
QPushButton#playBtn:pressed {
    background-color: #B91C1C;
}

/* Botón Stop / Detener */
QPushButton#stopBtn {
    background-color: #F1F5F9;
    color: #334155;
    border: 1px solid #CBD5E1;
    font-size: 14px;
}
QPushButton#stopBtn:hover {
    background-color: #E2E8F0;
}

/* Botón Peligro / Eliminar / Formatear */
QPushButton#dangerBtn {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
}
QPushButton#dangerBtn:hover {
    background-color: #FEE2E2;
    border-color: #F87171;
}

/* Inputs, SpinBoxes y ComboBoxes */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0F172A;
    selection-background-color: #3B82F6;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
    padding: 4px;
}

/* QSlider */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2563EB;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #1D4ED8;
}

/* CheckBox y RadioButton */
QCheckBox, QRadioButton {
    spacing: 8px;
    font-weight: 500;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

/* Tablas (QTableWidget) */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 600;
    padding: 8px 6px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}

/* Barra de Progreso */
QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    background-color: #F1F5F9;
    text-align: center;
    color: #1E293B;
    font-weight: 600;
    min-height: 20px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #10B981);
    border-radius: 5px;
}

/* Métricas / Stat Box */
QFrame#metricCard {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px;
}

/* Banner de Estado Activo */
QFrame#statusActive {
    background-color: #DCFCE7;
    border-left: 6px solid #22C55E;
    border-radius: 6px;
    padding: 12px;
}

/* Banner de Estado Inactivo */
QFrame#statusIdle {
    background-color: #F1F5F9;
    border-left: 6px solid #94A3B8;
    border-radius: 6px;
    padding: 12px;
}

/* Banner de Notificación Éxito */
QFrame#toastSuccess {
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-left: 5px solid #3B82F6;
    border-radius: 6px;
    padding: 10px 14px;
}
"""
