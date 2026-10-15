"""
=============================================================================
PROYECTO CAYETINO - SUBPROCESOS Y HILOS ASÍNCRONOS (workers.py)
Previene el bloqueo del frontend PyQt6 durante operaciones Serial y cálculo
=============================================================================
"""

from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
from typing import Dict, List, Any


class ConnectWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, client, port: str, baudrate: int):
        super().__init__()
        self.client = client
        self.port = port
        self.baudrate = baudrate

    def run(self):
        try:
            ok = self.client.connect(self.port, baudrate=self.baudrate)
            if ok:
                self.finished.emit(True, "Conectado exitosamente al ESP32.")
            else:
                self.finished.emit(False, "El ESP32 no respondió a PING. Verifica que el firmware Cayetino esté cargado.")
        except Exception as e:
            self.finished.emit(False, f"Error de conexión: {str(e)}")


class SaveSignalWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, client, filename: str, fs: int, dac_values: np.ndarray):
        super().__init__()
        self.client = client
        self.filename = filename
        self.fs = fs
        self.dac_values = dac_values

    def run(self):
        try:
            def update_cb(p: float):
                percent = int(p * 100)
                self.progress.emit(percent, f"Transmitiendo datos a LittleFS: {percent}%")

            self.progress.emit(0, "Iniciando transmisión hacia LittleFS...")
            success = self.client.save_file(
                filename=self.filename,
                fs=self.fs,
                dac_values=self.dac_values,
                progress_callback=update_cb
            )
            if success:
                self.finished.emit(True, f"¡El archivo '{self.filename}' se ha grabado correctamente en LittleFS! ({len(self.dac_values)} muestras)")
            else:
                self.finished.emit(False, "Falló la confirmación de guardado en el ESP32.")
        except Exception as e:
            self.finished.emit(False, f"Error al enviar archivo: {str(e)}")


class ListFilesWorker(QThread):
    finished = pyqtSignal(bool, list, str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            files = self.client.list_files()
            self.finished.emit(True, files, "Archivos leídos correctamente.")
        except Exception as e:
            self.finished.emit(False, [], f"Error al listar archivos: {str(e)}")


class PlayFileWorker(QThread):
    finished = pyqtSignal(bool, dict, str)

    def __init__(self, client, filename: str):
        super().__init__()
        self.client = client
        self.filename = filename

    def run(self):
        try:
            res = self.client.play_file(self.filename)
            if res.get("success", False):
                self.finished.emit(True, res, f"Reproduciendo '{self.filename}' ({res.get('samples', 0)} muestras a {res.get('fs', 0)} Hz por DAC)")
            else:
                self.finished.emit(False, res, f"No se pudo reproducir: {res.get('error', 'Fallo desconocido')}")
        except Exception as e:
            self.finished.emit(False, {}, f"Error al iniciar reproducción: {str(e)}")


class StopWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            ok = self.client.stop_playback()
            if ok:
                self.finished.emit(True, "Reproducción DAC detenida.")
            else:
                self.finished.emit(False, "No se pudo confirmar la detención de reproducción.")
        except Exception as e:
            self.finished.emit(False, f"Error al detener: {str(e)}")


class DeleteFileWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, client, filename: str):
        super().__init__()
        self.client = client
        self.filename = filename

    def run(self):
        try:
            ok = self.client.delete_file(self.filename)
            if ok:
                self.finished.emit(True, f"Archivo '{self.filename}' eliminado de LittleFS.")
            else:
                self.finished.emit(False, f"Error al eliminar '{self.filename}'.")
        except Exception as e:
            self.finished.emit(False, f"Error al eliminar: {str(e)}")


class FormatFSWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            ok = self.client.format_fs()
            if ok:
                self.finished.emit(True, "Memoria Flash LittleFS formateada correctamente.")
            else:
                self.finished.emit(False, "No se pudo formatear la memoria Flash.")
        except Exception as e:
            self.finished.emit(False, f"Error al formatear: {str(e)}")


class TestSineWorker(QThread):
    finished = pyqtSignal(bool, dict, str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            res = self.client.play_test_sine()
            if res.get("success", False):
                self.finished.emit(True, res, "¡Señal de prueba de 5 Hz activada en el DAC!")
            else:
                self.finished.emit(False, res, f"Error al iniciar prueba: {res.get('error', 'Fallo')}")
        except Exception as e:
            self.finished.emit(False, {}, f"Error en prueba senoidal: {str(e)}")
