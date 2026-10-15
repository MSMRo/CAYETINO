"""
=============================================================================
PROYECTO CAYETINO - PUNTO DE ENTRADA APLICACIÓN ESCRITORIO (main.py)
Generador de Señales Biomédicas y Sintéticas para ESP32 en PyQt6
=============================================================================
"""

import sys
import os

# Asegurar que el directorio de la aplicación esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from styles import MODERN_QSS
from main_window import MainWindow


def main():
    # Soporte para pantallas High-DPI
    app = QApplication(sys.argv)
    app.setApplicationName("Cayetino ESP32")
    app.setOrganizationName("UPCH - Cayetano Heredia")
    app.setStyleSheet(MODERN_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
