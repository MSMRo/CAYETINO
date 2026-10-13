"""
=============================================================================
PROYECTO CAYETINO - GENERADOR DE SEÑALES BIOMÉDICAS Y SINTÉTICAS
Módulo de Generación y Contaminación de Señales (signal_generator.py)
=============================================================================
"""

import numpy as np
from scipy import signal as sp_signal
import neurokit2 as nk

def generate_basic_signal(
    signal_type: str,
    freq: float = 1.0,
    fs: int = 500,
    duration: float = 2.0,
    amplitude: float = 1.0,
    offset: float = 0.0,
    duty_cycle: float = 0.5
):
    """
    Genera señales básicas periódicas.
    
    Tipos:
      - 'senoidal': Onda senoidal pura
      - 'triangulo': Onda triangular simétrica
      - 'cuadrada': Onda cuadrada con ciclo de trabajo configurable
      - 'diente_sierra': Onda rampa ascendente
      - 'diente_sierra_inv': Onda rampa descendente
    """
    n_samples = int(np.round(fs * duration))
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    sig_type_clean = signal_type.lower().strip()
    
    if sig_type_clean in ['senoidal', 'seno', 'sine']:
        y = np.sin(2 * np.pi * freq * t)
    elif sig_type_clean in ['cuadrada', 'square']:
        y = sp_signal.square(2 * np.pi * freq * t, duty=duty_cycle)
    elif sig_type_clean in ['triangulo', 'triangular', 'triangle']:
        y = sp_signal.sawtooth(2 * np.pi * freq * t, width=0.5)
    elif sig_type_clean in ['diente_sierra', 'sawtooth']:
        y = sp_signal.sawtooth(2 * np.pi * freq * t, width=1.0)
    elif sig_type_clean in ['diente_sierra_inv', 'diente_sierra_invertida', 'inverted_sawtooth']:
        y = sp_signal.sawtooth(2 * np.pi * freq * t, width=0.0)
    else:
        raise ValueError(f"Tipo de señal desconocido: {signal_type}")
        
    y = amplitude * y + offset
    return t, y


def generate_biomedical_signal(
    bio_type: str,
    fs: int = 250,
    duration: float = 5.0,
    heart_rate: int = 70,
    burst_number: int = 3,
    burst_duration: float = 0.5,
    method: str = "ecgsyn"
):
    """
    Genera señales fisiológicas sintéticas con NeuroKit2 o modelos paramétricos.
    
    Tipos:
      - 'ekg' o 'ecg': Electrocardiograma sintético
      - 'emg': Electromiografía sintética con ráfagas de activación muscular
      - 'ppg': Fotopletismografía sintética (pulso arterial de oximetría)
      - 'rsp': Señal respiratoria
      - 'eeg': Electroencefalograma sintético con ritmos alpha, beta, theta, delta
    """
    bio_clean = bio_type.lower().strip()
    n_samples = int(np.round(fs * duration))
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    if bio_clean in ['ekg', 'ecg']:
        # NeuroKit2 simula ECG
        try:
            ecg_series = nk.ecg_simulate(
                duration=duration,
                sampling_rate=fs,
                heart_rate=heart_rate,
                method=method,
                random_state=42
            )
            y = np.array(ecg_series)
            if len(y) != n_samples:
                # Interpolar si hubiera mínima discrepancia por cálculo de neurokit2
                t_orig = np.linspace(0, duration, len(y))
                y = np.interp(t, t_orig, y)
        except Exception:
            # Fallback a método estándar si ecgsyn tuviera problemas
            ecg_series = nk.ecg_simulate(
                duration=duration,
                sampling_rate=fs,
                heart_rate=heart_rate,
                method="simple"
            )
            y = np.array(ecg_series)
            t_orig = np.linspace(0, duration, len(y))
            y = np.interp(t, t_orig, y)
            
    elif bio_clean == 'emg':
        emg_series = nk.emg_simulate(
            duration=duration,
            sampling_rate=fs,
            burst_number=burst_number,
            burst_duration=burst_duration,
            random_state=42
        )
        y = np.array(emg_series)
        if len(y) != n_samples:
            t_orig = np.linspace(0, duration, len(y))
            y = np.interp(t, t_orig, y)
            
    elif bio_clean in ['rsp', 'respiracion']:
        rsp_series = nk.rsp_simulate(
            duration=duration,
            sampling_rate=fs,
            respiratory_rate=15,
            random_state=42
        )
        y = np.array(rsp_series)
        if len(y) != n_samples:
            t_orig = np.linspace(0, duration, len(y))
            y = np.interp(t, t_orig, y)
            
    elif bio_clean == 'ppg':
        ppg_series = nk.ppg_simulate(
            duration=duration,
            sampling_rate=fs,
            heart_rate=heart_rate,
            random_state=42
        )
        y = np.array(ppg_series)
        if len(y) != n_samples:
            t_orig = np.linspace(0, duration, len(y))
            y = np.interp(t, t_orig, y)
            
    elif bio_clean == 'eeg':
        # Simulación de EEG por superposición de bandas fisiológicas
        # Alpha (8-12 Hz), Beta (13-28 Hz), Theta (4-7 Hz), Ruido 1/f
        np.random.seed(42)
        alpha = 0.5 * np.sin(2 * np.pi * 10.0 * t + np.random.rand())
        beta = 0.25 * np.sin(2 * np.pi * 20.0 * t + np.random.rand())
        theta = 0.35 * np.sin(2 * np.pi * 6.0 * t + np.random.rand())
        pink_noise = np.cumsum(np.random.randn(n_samples)) * 0.05
        pink_noise -= np.mean(pink_noise)
        y = alpha + beta + theta + pink_noise
    else:
        raise ValueError(f"Tipo biomédico desconocido: {bio_type}")
        
    return t, y


def contaminate_signal(
    signal: np.ndarray,
    fs: int,
    white_noise_amp: float = 0.0,
    sine_noise_amp: float = 0.0,
    sine_noise_freq: float = 60.0,
    impulse_noise_prob: float = 0.0,
    impulse_noise_amp: float = 0.0,
    seed: int = 42
):
    """
    Contamina una señal con fuentes de ruido típicas en ingeniería biomédica:
      - Ruido blanco (Gaussiano térmico / instrumental)
      - Interferencia de red eléctrica (60 Hz o 50 Hz acoplado por campo electromagnético)
      - Ruido impulsional (artefactos de movimiento, desconexión momentánea de electrodos)
    """
    np.random.seed(seed)
    n = len(signal)
    t = np.arange(n) / fs
    noisy = signal.copy()
    
    # 1. Ruido Senoidal (Interferencia de red a 60 Hz u otra frecuencia)
    if sine_noise_amp > 0:
        sine_noise = sine_noise_amp * np.sin(2 * np.pi * sine_noise_freq * t)
        noisy += sine_noise
        
    # 2. Ruido Blanco Gaussiano
    if white_noise_amp > 0:
        white_noise = np.random.normal(0, white_noise_amp, size=n)
        noisy += white_noise
        
    # 3. Ruido Impulsional (Spikes esporádicos)
    if impulse_noise_prob > 0 and impulse_noise_amp > 0:
        mask = np.random.rand(n) < impulse_noise_prob
        signs = np.random.choice([-1.0, 1.0], size=n)
        spikes = signs * impulse_noise_amp
        noisy[mask] += spikes[mask]
        
    return noisy


def map_to_dac_8bit(
    signal: np.ndarray,
    auto_scale: bool = True,
    target_min_val: float = None,
    target_max_val: float = None,
    margin_percent: float = 2.0
):
    """
    Convierte la señal flotante a valores enteros de 8 bits (0 - 255) para el DAC del ESP32.
    También devuelve la tensión analógica estimada en voltios (0 a 3.3V).
    """
    sig = np.array(signal, dtype=np.float64)
    
    if auto_scale:
        s_min = np.min(sig)
        s_max = np.max(sig)
        
        if np.isclose(s_min, s_max):
            dac_vals = np.full(len(sig), 128, dtype=np.uint8)
            voltages = dac_vals * (3.3 / 255.0)
            return dac_vals, voltages
            
        # Margen para evitar clipping por saturación de los extremos
        span = s_max - s_min
        s_min_m = s_min - span * (margin_percent / 100.0)
        s_max_m = s_max + span * (margin_percent / 100.0)
        
        norm = (sig - s_min_m) / (s_max_m - s_min_m)
        dac_vals = np.clip(np.round(norm * 255.0), 0, 255).astype(np.uint8)
    else:
        # Escala fija manual
        if target_min_val is None:
            target_min_val = 0.0
        if target_max_val is None:
            target_max_val = 3.3
            
        norm = (sig - target_min_val) / (target_max_val - target_min_val)
        dac_vals = np.clip(np.round(norm * 255.0), 0, 255).astype(np.uint8)
        
    voltages = dac_vals * (3.3 / 255.0)
    return dac_vals, voltages


def format_file_content(dac_values: np.ndarray, fs: int, ext: str = "csv") -> str:
    """
    Genera el formato de texto legible (.csv o .txt) para almacenar en LittleFS del ESP32.
    Incluye encabezado con metadatos:
      #FS:<fs>
      #COUNT:<muestras>
      #DAC_BITS:8
      #VOLT_REF:3.3
    Seguido de las muestras.
    """
    count = len(dac_values)
    ext_clean = ext.lower().replace(".", "").strip()
    
    lines = [
        f"# CAYETINO SIGNAL FILE",
        f"# FS:{fs}",
        f"# COUNT:{count}",
        f"# FORMAT:{ext_clean.upper()}",
    ]
    
    if ext_clean == "csv":
        # Formato CSV: muestra, valor_dac, voltios_estimados
        lines.append("index,dac_val,voltage_v")
        for i, val in enumerate(dac_values):
            v = round(val * (3.3 / 255.0), 3)
            lines.append(f"{i},{val},{v}")
    else:
        # Formato TXT/DAT: valores separados por comas o uno por línea
        lines.append("# DATA")
        # Agrupados por 10 valores por línea para legibilidad
        chunk_strs = []
        for i in range(0, count, 10):
            chunk = dac_values[i:i+10]
            chunk_strs.append(",".join(map(str, chunk)))
        lines.extend(chunk_strs)
        
    return "\n".join(lines) + "\n"
