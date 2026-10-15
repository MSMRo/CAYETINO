"""
=============================================================================
PROYECTO CAYETINO - GESTOR DE COMUNICACIÓN SERIAL CON ESP32 (serial_comm.py)
Protocolo de enlace por puerto COM y gestión de archivos LittleFS
=============================================================================
"""

import time
import re
from typing import List, Dict, Optional, Callable
import numpy as np

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


def list_available_ports() -> List[Dict[str, str]]:
    """
    Retorna la lista de puertos COM disponibles en la computadora.
    """
    ports = []
    if not SERIAL_AVAILABLE:
        return ports
        
    for p in serial.tools.list_ports.comports():
        ports.append({
            "device": p.device,
            "description": p.description or p.device,
            "hwid": p.hwid or ""
        })
    return ports


class CayetinoSerial:
    """
    Controlador de comunicación Serial con el firmware Cayetino ESP32.
    Soporta modo físico por Serial y modo simulación virtual.
    """
    def __init__(self, simulation_mode: bool = False):
        self.simulation_mode = simulation_mode
        self.ser: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self.baudrate: int = 115200
        
        # Estado en modo simulación
        self.sim_files: Dict[str, Dict] = {
            "demo_ekg_normal.csv": {
                "name": "demo_ekg_normal.csv",
                "fs": 250,
                "samples": 1250,
                "duration": 5.0,
                "size_bytes": 14200,
                "data": np.full(1250, 128, dtype=np.uint8)
            },
            "demo_seno_10hz.txt": {
                "name": "demo_seno_10hz.txt",
                "fs": 500,
                "samples": 1000,
                "duration": 2.0,
                "size_bytes": 8400,
                "data": np.full(1000, 128, dtype=np.uint8)
            }
        }
        self.sim_status = {"playing": False, "filename": "", "fs": 0}

    def connect(self, port: str, baudrate: int = 115200, timeout: float = 1.5) -> bool:
        """Abre la conexión Serial con el ESP32."""
        if self.simulation_mode:
            self.port = "VIRTUAL_ESP32"
            self.baudrate = baudrate
            return True
            
        if not SERIAL_AVAILABLE:
            raise RuntimeError("La librería pyserial no está instalada.")
            
        self.disconnect()
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout
            )
            # Esperar a que el ESP32 se reinicie o estabilice DTR/RTS
            time.sleep(1.2)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.port = port
            self.baudrate = baudrate
            
            # Verificar con PING
            return self.ping()
        except Exception as e:
            self.disconnect()
            raise ConnectionError(f"Error al abrir puerto {port}: {str(e)}")

    def disconnect(self):
        """Cierra la conexión serial."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def is_connected(self) -> bool:
        if self.simulation_mode:
            return True
        return self.ser is not None and self.ser.is_open

    def _send_cmd(self, cmd: str) -> str:
        """Envía un comando y lee la primera línea de respuesta."""
        if not self.is_connected():
            raise ConnectionError("No hay conexión con el ESP32.")
            
        cmd_clean = cmd.strip() + "\n"
        self.ser.write(cmd_clean.encode('utf-8'))
        self.ser.flush()
        
        resp = self.ser.readline().decode('utf-8', errors='ignore').strip()
        return resp

    def ping(self) -> bool:
        """Comprueba conectividad con el firmware."""
        if self.simulation_mode:
            return True
            
        try:
            # Enviar PING dos veces si hay basura en buffer de inicio
            self.ser.reset_input_buffer()
            for _ in range(2):
                self.ser.write(b"PING\n")
                self.ser.flush()
                time.sleep(0.15)
                while self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if "PONG" in line or "CAYETINO" in line:
                        return True
            return False
        except Exception:
            return False

    def list_files(self) -> List[Dict]:
        """
        Consulta la lista de archivos almacenados en LittleFS del ESP32.
        Retorna lista de diccionarios con info de cada archivo.
        """
        if self.simulation_mode:
            return list(self.sim_files.values())
            
        if not self.is_connected():
            return []
            
        files = []
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"LIST\n")
            self.ser.flush()
            
            timeout_start = time.time()
            in_list = False
            
            while time.time() - timeout_start < 3.0:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    if "FILES_START" in line:
                        in_list = True
                        continue
                    if "FILES_END" in line:
                        break
                    if in_list and line.startswith("FILE:"):
                        # Formato: FILE:<nombre>:<fs>:<samples>:<bytes>
                        parts = line.split(":")
                        if len(parts) >= 5:
                            name = parts[1].lstrip("/")
                            fs = int(parts[2]) if parts[2].isdigit() else 250
                            samples = int(parts[3]) if parts[3].isdigit() else 0
                            size_bytes = int(parts[4]) if parts[4].isdigit() else 0
                            duration = round(samples / fs, 2) if fs > 0 else 0.0
                            files.append({
                                "name": name,
                                "fs": fs,
                                "samples": samples,
                                "duration": duration,
                                "size_bytes": size_bytes
                            })
                else:
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error list_files: {e}")
            
        return files

    def save_file(
        self,
        filename: str,
        fs: int,
        dac_values: np.ndarray,
        chunk_size: int = 64,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Envía una señal al ESP32 para grabarla en LittleFS.
        Usa transmisión por bloques (chunks) con confirmación (ACK) para evitar saturación de buffer.
        """
        clean_name = filename.strip().lstrip("/")
        num_samples = len(dac_values)
        
        if self.simulation_mode:
            # Simular guardado
            for i in range(0, num_samples, chunk_size):
                time.sleep(0.01)
                if progress_callback:
                    progress_callback(min(1.0, (i + chunk_size) / num_samples))
                    
            self.sim_files[clean_name] = {
                "name": clean_name,
                "fs": fs,
                "samples": num_samples,
                "duration": round(num_samples / fs, 2),
                "size_bytes": num_samples * 4,
                "data": np.array(dac_values, dtype=np.uint8)
            }
            if progress_callback:
                progress_callback(1.0)
            return True
            
        if not self.is_connected():
            raise ConnectionError("ESP32 desconectado.")
            
        self.ser.reset_input_buffer()
        # 1. Iniciar guardado
        start_cmd = f"SAVE_START:{clean_name}:{fs}:{num_samples}\n"
        self.ser.write(start_cmd.encode('utf-8'))
        self.ser.flush()
        
        # Esperar confirmación READY_CHUNKS
        ready = False
        t0 = time.time()
        while time.time() - t0 < 3.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "READY_CHUNKS" in line:
                    ready = True
                    break
            time.sleep(0.02)
            
        if not ready:
            raise TimeoutError("El ESP32 no respondió a SAVE_START.")
            
        # 2. Enviar chunks con ACK
        for i in range(0, num_samples, chunk_size):
            chunk = dac_values[i:i + chunk_size]
            chunk_csv = ",".join(str(int(v)) for v in chunk)
            chunk_cmd = f"CHUNK:{chunk_csv}\n"
            
            self.ser.write(chunk_cmd.encode('utf-8'))
            self.ser.flush()
            
            # Esperar ACK_CHUNK
            ack = False
            t_ack = time.time()
            while time.time() - t_ack < 2.0:
                if self.ser.in_waiting > 0:
                    ack_line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if "ACK_CHUNK" in ack_line:
                        ack = True
                        break
                time.sleep(0.005)
                
            if not ack:
                raise IOError(f"Fallo en ACK de bloque en muestra {i}.")
                
            if progress_callback:
                progress_callback(min(0.95, (i + chunk_size) / num_samples))
                
        # 3. Finalizar guardado
        self.ser.write(b"SAVE_END\n")
        self.ser.flush()
        
        # Esperar OK_SAVE
        t_end = time.time()
        saved = False
        while time.time() - t_end < 3.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "OK_SAVE" in line:
                    saved = True
                    break
            time.sleep(0.02)
            
        if progress_callback:
            progress_callback(1.0)
            
        return saved

    def play_file(self, filename: str) -> Dict:
        """Ordena al ESP32 reproducir continuamente el archivo indicado por su DAC."""
        clean_name = filename.strip().lstrip("/")
        
        if self.simulation_mode:
            if clean_name in self.sim_files:
                finfo = self.sim_files[clean_name]
                self.sim_status = {
                    "playing": True,
                    "filename": clean_name,
                    "fs": finfo["fs"],
                    "samples": finfo["samples"]
                }
                return {"success": True, "filename": clean_name, "fs": finfo["fs"], "samples": finfo["samples"]}
            return {"success": False, "error": "Archivo no encontrado en simulación"}
            
        if not self.is_connected():
            return {"success": False, "error": "ESP32 no conectado"}
            
        self.ser.reset_input_buffer()
        cmd = f"PLAY:{clean_name}\n"
        self.ser.write(cmd.encode('utf-8'))
        self.ser.flush()
        
        t0 = time.time()
        while time.time() - t0 < 4.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "OK_PLAY:" in line:
                    # Formato: OK_PLAY:<path>:<fs>:<samples>
                    parts = line.split(":")
                    fs = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 250
                    samples = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                    self.sim_status = {"playing": True, "filename": clean_name, "fs": fs, "samples": samples}
                    return {"success": True, "filename": clean_name, "fs": fs, "samples": samples}
                elif "ERR_PLAY" in line:
                    return {"success": False, "error": line}
            time.sleep(0.05)
        return {"success": False, "error": "Timeout esperando respuesta de PLAY"}

    def play_test_sine(self) -> Dict:
        """Activa una señal senoidal pura de 5 Hz generada internamente en el ESP32 para verificar el hardware DAC."""
        if self.simulation_mode:
            self.sim_status = {"playing": True, "filename": "TEST_SENO_5HZ", "fs": 500, "samples": 100}
            return {"success": True, "filename": "TEST_SENO_5HZ", "fs": 500, "samples": 100}
            
        if not self.is_connected():
            return {"success": False, "error": "ESP32 no conectado"}
            
        self.ser.reset_input_buffer()
        self.ser.write(b"TEST_SINE\n")
        self.ser.flush()
        
        t0 = time.time()
        while time.time() - t0 < 3.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "OK_TEST_SINE:" in line:
                    parts = line.split(":")
                    fs = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 500
                    samples = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 100
                    self.sim_status = {"playing": True, "filename": "TEST_SENO_5HZ", "fs": fs, "samples": samples}
                    return {"success": True, "filename": "TEST_SENO_5HZ", "fs": fs, "samples": samples}
            time.sleep(0.05)
        return {"success": False, "error": "Timeout en TEST_SINE"}

    def stop_playback(self) -> bool:
        """Detiene la reproducción activa del DAC."""
        if self.simulation_mode:
            self.sim_status["playing"] = False
            return True
            
        if not self.is_connected():
            return False
            
        self.ser.reset_input_buffer()
        self.ser.write(b"STOP\n")
        self.ser.flush()
        
        t0 = time.time()
        while time.time() - t0 < 2.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "OK_STOP" in line:
                    return True
            time.sleep(0.05)
        return False

    def delete_file(self, filename: str) -> bool:
        """Elimina un archivo de LittleFS en el ESP32."""
        clean_name = filename.strip().lstrip("/")
        
        if self.simulation_mode:
            if clean_name in self.sim_files:
                del self.sim_files[clean_name]
                return True
            return False
            
        if not self.is_connected():
            return False
            
        self.ser.reset_input_buffer()
        cmd = f"DELETE:{clean_name}\n"
        self.ser.write(cmd.encode('utf-8'))
        self.ser.flush()
        
        t0 = time.time()
        while time.time() - t0 < 2.0:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "OK_DELETE" in line:
                    return True
            time.sleep(0.05)
        return False

    def get_status(self) -> Dict:
        """Consulta el estado actual de reproducción en el ESP32."""
        if self.simulation_mode:
            return self.sim_status
            
        if not self.is_connected():
            return {"playing": False, "filename": "", "fs": 0}
            
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"STATUS\n")
            self.ser.flush()
            
            t0 = time.time()
            while time.time() - t0 < 1.5:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("STATUS:PLAYING:"):
                        parts = line.split(":")
                        return {
                            "playing": True,
                            "filename": parts[2] if len(parts) > 2 else "",
                            "fs": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                        }
                    elif "STATUS:IDLE" in line:
                        return {"playing": False, "filename": "", "fs": 0}
                time.sleep(0.05)
        except Exception:
            pass
            
        return {"playing": False, "filename": "", "fs": 0}

    def set_dac_pin(self, pin: int = 25) -> bool:
        """Configura el pin DAC activo (GPIO 25 o GPIO 26)."""
        if self.simulation_mode:
            return True
        if not self.is_connected():
            return False
            
        self.ser.write(f"SET_DAC_PIN:{pin}\n".encode('utf-8'))
        self.ser.flush()
        return True

    def format_fs(self) -> bool:
        """Formatea la memoria Flash (LittleFS) del ESP32."""
        if self.simulation_mode:
            self.sim_files.clear()
            self.sim_status = {"playing": False, "filename": "", "fs": 0}
            return True
            
        if not self.is_connected():
            return False
            
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"FORMAT\n")
            self.ser.flush()
            
            t0 = time.time()
            while time.time() - t0 < 8.0:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if "OK_FORMAT" in line:
                        return True
                time.sleep(0.05)
        except Exception:
            pass
        return False
