"""
=============================================================================
PROYECTO CAYETINO - APLICACIÓN STREAMLIT
Generador de Señales Analógicas Biomédicas y Sintéticas para ESP32
=============================================================================
"""

import time
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from signal_generator import (
    generate_basic_signal,
    generate_biomedical_signal,
    contaminate_signal,
    map_to_dac_8bit,
    format_file_content
)
from serial_comm import CayetinoSerial, list_available_ports

# Configuración general de la página Streamlit
st.set_page_config(
    page_title="Cayetino - Generador de Señales ESP32",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para mejorar el diseño
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .file-card {
        background-color: #F8FAFC;
        border: 2px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .status-badge-active {
        background-color: #DCFCE7;
        color: #166534;
        border-left: 5px solid #22C55E;
        padding: 0.8rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .status-badge-idle {
        background-color: #F1F5F9;
        color: #475569;
        border-left: 5px solid #94A3B8;
        padding: 0.8rem;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# INICIALIZACIÓN DEL ESTADO DE SESIÓN (SESSION STATE)
# =============================================================================
if "client" not in st.session_state:
    st.session_state.client = CayetinoSerial(simulation_mode=False)

if "files_list" not in st.session_state:
    st.session_state.files_list = []

if "connected" not in st.session_state:
    st.session_state.connected = False

if "last_save_msg" not in st.session_state:
    st.session_state.last_save_msg = None

if "current_status" not in st.session_state:
    st.session_state.current_status = {"playing": False, "filename": "", "fs": 0}

if "preview_data" not in st.session_state:
    st.session_state.preview_data = None


# =============================================================================
# BARRA LATERAL (SIDEBAR): CONEXIÓN SERIAL Y HARDWARE
# =============================================================================
with st.sidebar:
    st.markdown("## ⚡ **CAYETINO ESP32**")
    st.caption("Plataforma de Señales para Ingeniería Biomédica")
    st.markdown("---")

    st.subheader("🔌 Enlace de Comunicación")
    
    sim_mode = st.toggle("🧪 Modo Simulación (Sin hardware)", value=False, help="Permite probar toda la plataforma y simular el ESP32 sin conectar placa física.")
    st.session_state.client.simulation_mode = sim_mode

    if not sim_mode:
        available_ports = list_available_ports()
        port_options = [p["device"] for p in available_ports]
        port_labels = {p["device"]: f"{p['device']} - {p['description']}" for p in available_ports}

        # Intentar preseleccionar puerto CP210x / USB-UART si existe (e.g. COM7)
        default_index = 0
        for i, p in enumerate(available_ports):
            if "CP210" in p["description"] or "USB" in p["description"] or "COM7" in p["device"]:
                default_index = i
                break

        if port_options:
            selected_port = st.selectbox(
                "Puerto Serial COM:",
                options=port_options,
                index=default_index,
                format_func=lambda x: port_labels.get(x, x)
            )
        else:
            selected_port = None
            st.warning("⚠️ No se detectaron puertos COM. Conecta el ESP32 por USB o activa el modo simulación.")

        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            baud_rate = st.selectbox("Baudrate:", options=[115200, 921600, 57600], index=0)
        with col_c2:
            st.write("")
            st.write("")
            refresh_ports = st.button("🔄 Refrescar", use_container_width=True)
            if refresh_ports:
                st.rerun()

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if not st.session_state.connected:
                if st.button("🔗 Conectar", type="primary", use_container_width=True, disabled=(selected_port is None)):
                    with st.spinner("Conectando con ESP32..."):
                        try:
                            ok = st.session_state.client.connect(selected_port, baudrate=baud_rate)
                            if ok:
                                st.session_state.connected = True
                                st.session_state.files_list = st.session_state.client.list_files()
                                st.success("¡Conectado exitosamente!")
                                st.rerun()
                            else:
                                st.error("El ESP32 no respondió a PING. Verifica que el sketch Cayetino esté cargado.")
                        except Exception as e:
                            st.error(f"Error de conexión: {str(e)}")
            else:
                if st.button("❌ Desconectar", use_container_width=True):
                    st.session_state.client.disconnect()
                    st.session_state.connected = False
                    st.info("Desconectado.")
                    st.rerun()
                    
        with col_b2:
            if st.session_state.connected:
                st.markdown("<p style='color:green;font-weight:bold;margin-top:8px;'>🟢 Conectado</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:gray;font-weight:bold;margin-top:8px;'>⚪ Desconectado</p>", unsafe_allow_html=True)
    else:
        st.session_state.connected = True
        st.info("🧪 Modo Simulación Activo. Todas las operaciones se ejecutan de forma virtual.")
        if len(st.session_state.files_list) == 0:
            st.session_state.files_list = st.session_state.client.list_files()

    st.markdown("---")
    st.subheader("⚙️ Configuración del DAC")
    dac_pin_choice = st.radio(
        "Pin de salida analógica DAC:",
        options=[25, 26],
        index=0,
        format_func=lambda x: f"GPIO {x} (DAC Channel {1 if x==25 else 2})",
        help="Los ESP32 WROOM disponen de dos DACs de 8 bits en GPIO 25 y GPIO 26."
    )
    if st.button("Aplicar Pin DAC", use_container_width=True):
        st.session_state.client.set_dac_pin(dac_pin_choice)
        st.success(f"Pin de salida configurado en GPIO {dac_pin_choice}.")

    st.markdown("---")
    with st.expander("🛠️ Mantenimiento LittleFS"):
        st.caption("Formatea la memoria Flash interna del ESP32 borrando todos los archivos guardados.")
        if st.button("⚠️ Formatear LittleFS", type="secondary", use_container_width=True):
            if st.session_state.connected:
                ok = st.session_state.client.format_fs()
                if ok:
                    st.session_state.files_list = []
                    st.success("Memoria formateada correctamente.")
                    st.rerun()
                else:
                    st.error("No se pudo formatear la memoria.")
            else:
                st.warning("Debes conectar el ESP32 primero.")


# =============================================================================
# ENCABEZADO PRINCIPAL
# =============================================================================
st.markdown('<div class="main-title">⚡ Proyecto CAYETINO</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Generador de Señales Sintéticas y Biomédicas con almacenamiento en LittleFS y salida analógica por DAC del ESP32</div>',
    unsafe_allow_html=True
)

# Mensaje de confirmación flotante si se guardó un archivo recientemente
if st.session_state.last_save_msg:
    st.success(st.session_state.last_save_msg)
    if st.button("Cerrar notificación"):
        st.session_state.last_save_msg = None
        st.rerun()

# Pestañas de la aplicación
tab_basic, tab_adv, tab_manager, tab_guide = st.tabs([
    "📊 Modo Básico (Ondas Periódicas)",
    "🧬 Modo Avanzado (Biomédico & NeuroKit2)",
    "💾 Gestor de Archivos & DAC ESP32",
    "🔌 Hardware & Guía Biomédica"
])


# =============================================================================
# PESTAÑA 1: MODO BÁSICO
# =============================================================================
with tab_basic:
    st.markdown("### 📊 Generador de Formas de Onda Básicas")
    st.write("Genera señales periódicas fundamentales y envíalas directamente a la memoria flash del ESP32 para su reproducción analógica.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 1. Tipo y Parámetros de Onda")
        wave_type = st.selectbox(
            "Forma de Onda:",
            options=[
                "Senoidal",
                "Triángulo",
                "Cuadrada",
                "Diente de Sierra",
                "Diente de Sierra Invertida"
            ]
        )

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            sig_freq = st.number_input("Frecuencia de señal (Hz):", min_value=0.1, max_value=500.0, value=5.0, step=0.5)
        with col_w2:
            sig_amp = st.slider("Amplitud normalizada:", min_value=0.1, max_value=1.0, value=1.0, step=0.05)

        col_w3, col_w4 = st.columns(2)
        with col_w3:
            sig_offset = st.slider("Offset / Nivel DC:", min_value=-1.0, max_value=1.0, value=0.0, step=0.05)
        with col_w4:
            duty = 0.5
            if wave_type == "Cuadrada":
                duty = st.slider("Ciclo de trabajo (Duty):", min_value=0.05, max_value=0.95, value=0.5, step=0.05)

    with col2:
        st.markdown("#### 2. Parámetros Temporales y Muestreo")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fs_basic = st.number_input("Frecuencia de muestreo Fs (Hz):", min_value=50, max_value=20000, value=500, step=50, key="fs_basic")
        with col_t2:
            duration_basic = st.number_input("Tiempo de ventana T (segundos):", min_value=0.1, max_value=10.0, value=2.0, step=0.5, key="dur_basic")

        total_samples_basic = int(np.round(fs_basic * duration_basic))
        st.metric("Total de Muestras a Enviar", f"{total_samples_basic:,} muestras")
        st.caption(f"⏱️ Período de muestreo: {1000.0/fs_basic:.2f} ms | Ciclos en ventana: {sig_freq * duration_basic:.1f}")

    # Mapeo a tipo para la función
    type_map = {
        "Senoidal": "senoidal",
        "Triángulo": "triangulo",
        "Cuadrada": "cuadrada",
        "Diente de Sierra": "diente_sierra",
        "Diente de Sierra Invertida": "diente_sierra_inv"
    }

    t_basic, y_basic = generate_basic_signal(
        signal_type=type_map[wave_type],
        freq=sig_freq,
        fs=fs_basic,
        duration=duration_basic,
        amplitude=sig_amp,
        offset=sig_offset,
        duty_cycle=duty
    )

    # Conversión a DAC de 8 bits (0 - 255)
    dac_basic, volt_basic = map_to_dac_8bit(y_basic, auto_scale=True)

    # Gráfica interactiva con Plotly
    fig_basic = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Tensión Analógica Generada en DAC (0.0 V - 3.3 V)", "Valores Cuantizados DAC 8-Bit (0 - 255)")
    )

    fig_basic.add_trace(
        go.Scatter(x=t_basic, y=volt_basic, mode="lines", name="Tensión DAC (V)", line=dict(color="#2563EB", width=2)),
        row=1, col=1
    )
    fig_basic.add_trace(
        go.Scatter(x=t_basic, y=dac_basic, mode="lines", name="Valor DAC (0-255)", line=dict(color="#10B981", width=2)),
        row=2, col=1
    )

    fig_basic.update_layout(
        height=420,
        margin=dict(l=40, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_basic.update_xaxes(title_text="Tiempo (s)", row=2, col=1)
    fig_basic.update_yaxes(title_text="Voltios (V)", range=[0.0, 3.4], row=1, col=1)
    fig_basic.update_yaxes(title_text="DAC (0-255)", range=[0, 260], row=2, col=1)

    st.plotly_chart(fig_basic, use_container_width=True)

    # Sección de Guardado en ESP32 LittleFS
    st.markdown("---")
    st.markdown("#### 💾 Guardar Señal Básica en LittleFS del ESP32")
    
    col_s1, col_s2, col_s3 = st.columns([2, 1, 2])
    with col_s1:
        default_basic_name = f"{wave_type.lower().replace(' ', '_')}_{int(sig_freq)}hz"
        basic_filename = st.text_input("Nombre del archivo:", value=default_basic_name, key="fname_basic")
    with col_s2:
        basic_ext = st.selectbox("Extensión:", options=[".csv", ".txt", ".dat"], index=0, key="ext_basic")
    with col_s3:
        st.write("")
        st.write("")
        full_basic_name = basic_filename.strip() + basic_ext
        send_basic_btn = st.button("🚀 Enviar y Guardar en ESP32", type="primary", use_container_width=True, key="send_basic")

    if send_basic_btn:
        if not st.session_state.connected:
            st.error("❌ El ESP32 no está conectado. Conéctalo desde la barra lateral o activa el Modo Simulación.")
        else:
            prog_bar = st.progress(0, text="Iniciando transmisión hacia LittleFS...")
            try:
                def update_prog(p):
                    prog_bar.progress(p, text=f"Transmitiendo datos a LittleFS: {int(p*100)}%")

                success = st.session_state.client.save_file(
                    filename=full_basic_name,
                    fs=fs_basic,
                    dac_values=dac_basic,
                    progress_callback=update_prog
                )
                if success:
                    st.session_state.last_save_msg = f"✅ ¡El archivo '{full_basic_name}' se ha grabado correctamente en LittleFS del ESP32! ({total_samples_basic} muestras guardadas)"
                    st.session_state.files_list = st.session_state.client.list_files()
                    prog_bar.empty()
                    st.rerun()
                else:
                    prog_bar.empty()
                    st.error("⚠️ Falló la confirmación de guardado en el ESP32.")
            except Exception as e:
                prog_bar.empty()
                st.error(f"Error al enviar archivo: {str(e)}")


# =============================================================================
# PESTAÑA 2: MODO AVANZADO (NEUROKIT2 & CONTAMINACIÓN)
# =============================================================================
with tab_adv:
    st.markdown("### 🧬 Modo Avanzado: Señales Biomédicas Sintéticas (NeuroKit2)")
    st.write(
        "Genera señales fisiológicas realistas mediante la librería especializada **NeuroKit2** "
        "e incorpora fuentes reales de contaminación (ruido blanco, armónico de red eléctrica a 60 Hz y ruido impulsional)."
    )

    col_a1, col_a2 = st.columns([1, 1])

    with col_a1:
        st.markdown("#### 1. Configuración de Señal Fisiológica")
        bio_type_label = st.selectbox(
            "Tipo de Señal Biomédica:",
            options=[
                "EKG / ECG (Electrocardiograma)",
                "EMG (Electromiografía)",
                "EEG (Electroencefalograma - Ritmos cerebrales)",
                "RSP (Señal Respiratoria)",
                "PPG (Fotopletismografía / Pulso de Oximetría)"
            ]
        )

        bio_key_map = {
            "EKG / ECG (Electrocardiograma)": "ekg",
            "EMG (Electromiografía)": "emg",
            "EEG (Electroencefalograma - Ritmos cerebrales)": "eeg",
            "RSP (Señal Respiratoria)": "rsp",
            "PPG (Fotopletismografía / Pulso de Oximetría)": "ppg"
        }
        selected_bio = bio_key_map[bio_type_label]

        if selected_bio in ["ekg", "ppg"]:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                heart_rate = st.slider("Frecuencia Cardíaca (BPM):", min_value=40, max_value=180, value=72, step=1)
            with col_b2:
                ecg_method = st.selectbox("Modelo de síntesis:", options=["ecgsyn (Dinámico McSharry)", "simple"], index=0)
                burst_num, burst_dur = 3, 0.5
        elif selected_bio == "emg":
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                burst_num = st.slider("Número de contracciones (bursts):", min_value=1, max_value=10, value=3)
            with col_b2:
                burst_dur = st.slider("Duración de contracción (s):", min_value=0.2, max_value=2.0, value=0.6, step=0.1)
            heart_rate = 72
            ecg_method = "simple"
        else:
            heart_rate = 72
            ecg_method = "simple"
            burst_num, burst_dur = 3, 0.5

    with col_a2:
        st.markdown("#### 2. Ventana de Tiempo y Frecuencia de Muestreo")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            fs_adv = st.selectbox(
                "Frecuencia de muestreo Fs (Hz):",
                options=[250, 500, 1000, 2000],
                index=0,
                help="250 Hz o 500 Hz son estándares clínicos para EKG de diagnóstico."
            )
        with col_m2:
            duration_adv = st.number_input("Ventana en bucle T (segundos):", min_value=1.0, max_value=15.0, value=5.0, step=1.0)

        total_samples_adv = int(np.round(fs_adv * duration_adv))
        st.metric("Muestras de la Ventana", f"{total_samples_adv:,} muestras")
        st.caption(f"💾 Tamaño estimado en Flash: ~{(total_samples_adv * 6) / 1024:.1f} KB")

    # Módulo de Contaminación de Señal
    st.markdown("---")
    st.markdown("#### 🌫️ Opciones de Contaminación y Ruido")
    st.write("Añade interferencias típicas que enfrentan los equipos biomédicos para prácticas de filtrado digital:")

    c_noise1, c_noise2, c_noise3 = st.columns(3)

    with c_noise1:
        st.markdown("##### ⚡ Interferencia de Red (Seno)")
        use_sine_noise = st.checkbox("Activar ruido de red eléctrica", value=False)
        if use_sine_noise:
            sine_f = st.number_input("Frecuencia de red (Hz):", min_value=10.0, max_value=200.0, value=60.0, step=1.0, help="60 Hz en Perú y América, 50 Hz en Europa.")
            sine_amp = st.slider("Amplitud de interferencia:", min_value=0.01, max_value=0.8, value=0.25, step=0.02)
        else:
            sine_f, sine_amp = 60.0, 0.0

    with c_noise2:
        st.markdown("##### 🌫️ Ruido Blanco Gaussiano")
        use_white_noise = st.checkbox("Activar ruido blanco térmico", value=False)
        if use_white_noise:
            white_amp = st.slider("Desviación estándar (σ):", min_value=0.01, max_value=0.5, value=0.08, step=0.01)
        else:
            white_amp = 0.0

    with c_noise3:
        st.markdown("##### 📍 Ruido Impulsional (Spikes)")
        use_impulse_noise = st.checkbox("Activar artefactos de movimiento", value=False)
        if use_impulse_noise:
            impulse_prob = st.slider("Probabilidad de spikes (%):", min_value=0.1, max_value=5.0, value=0.8, step=0.1) / 100.0
            impulse_amp = st.slider("Amplitud de artefacto:", min_value=0.2, max_value=2.0, value=0.8, step=0.1)
        else:
            impulse_prob, impulse_amp = 0.0, 0.0

    # Generación de la señal limpia y contaminada
    t_adv, y_clean = generate_biomedical_signal(
        bio_type=selected_bio,
        fs=fs_adv,
        duration=duration_adv,
        heart_rate=heart_rate,
        burst_number=burst_num,
        burst_duration=burst_dur,
        method="ecgsyn" if "ecgsyn" in ecg_method else "simple"
    )

    y_contaminated = contaminate_signal(
        signal=y_clean,
        fs=fs_adv,
        white_noise_amp=white_amp,
        sine_noise_amp=sine_amp,
        sine_noise_freq=sine_f,
        impulse_noise_prob=impulse_prob,
        impulse_noise_amp=impulse_amp
    )

    # Conversión a DAC
    dac_adv, volt_adv = map_to_dac_8bit(y_contaminated, auto_scale=True)

    # Gráficos interactivos
    fig_adv = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Comparativa: Señal Sintética Limpia vs. Contaminada", "Señal Analógica Cuantizada de Salida DAC (0.0 V - 3.3 V)")
    )

    fig_adv.add_trace(
        go.Scatter(x=t_adv, y=y_clean, mode="lines", name="Señal Limpia", line=dict(color="#059669", width=1.8)),
        row=1, col=1
    )
    if (sine_amp > 0 or white_amp > 0 or impulse_amp > 0):
        fig_adv.add_trace(
            go.Scatter(x=t_adv, y=y_contaminated, mode="lines", name="Señal Contaminada", line=dict(color="#DC2626", width=1.5, dash="solid")),
            row=1, col=1
        )

    fig_adv.add_trace(
        go.Scatter(x=t_adv, y=volt_adv, mode="lines", name="Salida DAC Real (V)", line=dict(color="#2563EB", width=1.8)),
        row=2, col=1
    )

    fig_adv.update_layout(
        height=480,
        margin=dict(l=40, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_adv.update_xaxes(title_text="Tiempo (s)", row=2, col=1)
    fig_adv.update_yaxes(title_text="Amplitud Fisiológica", row=1, col=1)
    fig_adv.update_yaxes(title_text="Tensión DAC (V)", range=[0.0, 3.4], row=2, col=1)

    st.plotly_chart(fig_adv, use_container_width=True)

    # Análisis espectral opcional FFT
    with st.expander("📊 Ver Análisis Espectral en Frecuencia (FFT)"):
        # Cálculo de FFT
        n_fft = len(y_contaminated)
        freqs = np.fft.rfftfreq(n_fft, d=1.0/fs_adv)
        mag_clean = np.abs(np.fft.rfft(y_clean)) / n_fft
        mag_noisy = np.abs(np.fft.rfft(y_contaminated)) / n_fft

        fig_fft = go.Figure()
        fig_fft.add_trace(go.Scatter(x=freqs, y=mag_clean, mode="lines", name="Espectro Señal Limpia", line=dict(color="#059669")))
        if (sine_amp > 0 or white_amp > 0 or impulse_amp > 0):
            fig_fft.add_trace(go.Scatter(x=freqs, y=mag_noisy, mode="lines", name="Espectro Señal Contaminada", line=dict(color="#DC2626")))
        fig_fft.update_layout(
            title="Densidad Espectral de Amplitud (FFT)",
            xaxis_title="Frecuencia (Hz)",
            yaxis_title="Magnitud",
            xaxis=dict(range=[0, min(120, fs_adv/2)]),
            height=320,
            margin=dict(l=40, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_fft, use_container_width=True)

    # Panel de Guardado de Señal Biomédica
    st.markdown("---")
    st.markdown("#### 💾 Guardar Señal Biomédica en LittleFS del ESP32")
    
    col_sa1, col_sa2, col_sa3 = st.columns([2, 1, 2])
    with col_sa1:
        suffix_noise = ""
        if sine_amp > 0: suffix_noise += f"_ruido{int(sine_f)}hz"
        if white_amp > 0: suffix_noise += "_blanco"
        if impulse_amp > 0: suffix_noise += "_spikes"
        default_bio_name = f"{selected_bio}_{int(duration_adv)}s{suffix_noise}"
        adv_filename = st.text_input("Nombre del archivo:", value=default_bio_name, key="fname_adv")
    with col_sa2:
        adv_ext = st.selectbox("Extensión:", options=[".csv", ".txt", ".dat"], index=0, key="ext_adv")
    with col_sa3:
        st.write("")
        st.write("")
        full_adv_name = adv_filename.strip() + adv_ext
        send_adv_btn = st.button("🚀 Enviar y Guardar en ESP32", type="primary", use_container_width=True, key="send_adv")

    if send_adv_btn:
        if not st.session_state.connected:
            st.error("❌ El ESP32 no está conectado. Conéctalo desde la barra lateral o activa el Modo Simulación.")
        else:
            prog_bar_adv = st.progress(0, text="Iniciando transmisión hacia LittleFS...")
            try:
                def update_prog_adv(p):
                    prog_bar_adv.progress(p, text=f"Transmitiendo datos a LittleFS: {int(p*100)}%")

                success = st.session_state.client.save_file(
                    filename=full_adv_name,
                    fs=fs_adv,
                    dac_values=dac_adv,
                    progress_callback=update_prog_adv
                )
                if success:
                    st.session_state.last_save_msg = f"✅ ¡El archivo '{full_adv_name}' se ha grabado correctamente en LittleFS del ESP32! ({total_samples_adv} muestras guardadas)"
                    st.session_state.files_list = st.session_state.client.list_files()
                    prog_bar_adv.empty()
                    st.rerun()
                else:
                    prog_bar_adv.empty()
                    st.error("⚠️ Falló la confirmación de guardado en el ESP32.")
            except Exception as e:
                prog_bar_adv.empty()
                st.error(f"Error al enviar archivo: {str(e)}")


# =============================================================================
# PESTAÑA 3: GESTOR DE ARCHIVOS Y REPRODUCTOR DAC EN ESP32
# =============================================================================
with tab_manager:
    st.markdown("### 💾 Gestor de Archivos en LittleFS y Control DAC")
    st.write("Visualiza todos los archivos de señales grabados en la memoria Flash del ESP32 y selecciona cuál emitir por el DAC.")

    # Estado actual en vivo del ESP32
    if st.session_state.connected:
        st.session_state.current_status = st.session_state.client.get_status()

    stat = st.session_state.current_status
    if stat.get("playing", False):
        st.markdown(
            f'<div class="status-badge-active">▶️ REPRODUCIENDO EN VIVO POR DAC: '
            f'<b>{stat.get("filename")}</b> | Fs: {stat.get("fs")} Hz | '
            f'Pin: GPIO {dac_pin_choice} (Bucle Continuo Activo)</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="status-badge-idle">⏹️ ESP32 EN ESPERA: DAC en nivel neutro (~1.65 V) | Pin: GPIO {dac_pin_choice}</div>',
            unsafe_allow_html=True
        )

    st.write("")

    # Card / Cuadrado de Archivos en LittleFS
    st.markdown('<div class="file-card">', unsafe_allow_html=True)
    col_fh1, col_fh2 = st.columns([3, 1])
    with col_fh1:
        st.markdown("#### 📁 Archivos Disponibles en Memoria Flash (LittleFS)")
    with col_fh2:
        if st.button("🔄 Actualizar Lista", use_container_width=True, key="refresh_files"):
            if st.session_state.connected:
                with st.spinner("Leyendo LittleFS..."):
                    st.session_state.files_list = st.session_state.client.list_files()
                    st.rerun()

    files = st.session_state.files_list

    if not files:
        st.info("ℹ️ No hay archivos guardados en LittleFS todavía. Ve al Modo Básico o Modo Avanzado para generar y guardar una señal.")
    else:
        df_files = pd.DataFrame([
            {
                "Archivo": f["name"],
                "Fs (Hz)": f["fs"],
                "Muestras": f"{f['samples']:,}",
                "Duración (s)": f"{f['duration']} s",
                "Tamaño Flash": f"{f['size_bytes'] / 1024:.2f} KB"
            }
            for f in files
        ])
        st.dataframe(df_files, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### 🎛️ Seleccionar Archivo para Controlar:")
        file_names = [f["name"] for f in files]
        selected_file_name = st.selectbox("Archivo a emitir por el DAC:", options=file_names, key="sel_file")

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            if st.button("▶️ REPRODUCIR (PLAY)", type="primary", use_container_width=True, key="play_btn"):
                if not st.session_state.connected:
                    st.error("Conecta el ESP32 primero.")
                else:
                    with st.spinner(f"Cargando {selected_file_name} en memoria del ESP32..."):
                        res = st.session_state.client.play_file(selected_file_name)
                        if res.get("success", False):
                            st.success(f"¡Reproduciendo {selected_file_name}! ({res.get('samples', 0)} muestras cargadas a {res.get('fs', 0)} Hz por DAC)")
                            st.session_state.current_status = st.session_state.client.get_status()
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"No se pudo iniciar la reproducción: {res.get('error', 'Fallo desconocido')}")

        with col_p2:
            if st.button("⏹️ DETENER (STOP)", use_container_width=True, key="stop_btn"):
                if st.session_state.connected:
                    st.session_state.client.stop_playback()
                    st.info("Reproducción detenida.")
                    st.session_state.current_status = st.session_state.client.get_status()
                    st.rerun()

        with col_p3:
            if st.button("🗑️ Eliminar Archivo", type="secondary", use_container_width=True, key="del_btn"):
                if st.session_state.connected:
                    ok = st.session_state.client.delete_file(selected_file_name)
                    if ok:
                        st.warning(f"Archivo {selected_file_name} eliminado de LittleFS.")
                        st.session_state.files_list = st.session_state.client.list_files()
                        st.rerun()
                    else:
                        st.error("Error al eliminar archivo.")

    st.markdown("---")
    st.markdown("##### 🔬 Diagnóstico y Verificación de Hardware Directa:")
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.caption("Genera una onda senoidal pura de 5 Hz (0 - 3.3V) directamente desde la RAM del ESP32 sin leer archivos de memoria Flash, ideal para comprobar el cableado con el osciloscopio o Raspberry Pi Pico.")
    with col_t2:
        if st.button("🧪 Probar DAC con Seno 5 Hz", use_container_width=True):
            if not st.session_state.connected:
                st.error("Conecta el ESP32 primero.")
            else:
                res = st.session_state.client.play_test_sine()
                if res.get("success", False):
                    st.success("¡Señal de prueba de 5 Hz activada en el DAC!")
                    st.session_state.current_status = st.session_state.client.get_status()
                    st.rerun()
                else:
                    st.error("Error al iniciar prueba.")

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# PESTAÑA 4: HARDWARE & GUÍA BIOMÉDICA
# =============================================================================
with tab_guide:
    st.markdown("### 🔌 Conexión de Hardware y Circuito Atenuador Biomédico")
    st.write("Aprende a conectar el ESP32 a amplificadores de biopotenciales y osciloscopios de forma segura.")

    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.markdown("#### 1. Salida Directa del DAC del ESP32")
        st.markdown("""
        - **Resolución**: 8 bits (256 niveles discretos: $0$ a $255$).
        - **Tensión de salida**: $0.0\\text{ V}$ a $3.3\\text{ V}$.
        - **Pines DAC integrados**:
          - **DAC 1**: `GPIO 25` (predeterminado)
          - **DAC 2**: `GPIO 26`
          - **Tierra / Referencia**: `GND`
        - Para conectar directamente a un osciloscopio o entrada ADC, se conecta la sonda positiva al pin `GPIO 25` y la tierra al pin `GND`.
        """)

        st.markdown("#### 2. Circuito Atenuador para Amplificadores Biomédicos")
        st.info("""
        **¿Por qué atenuar?**
        Las señales fisiológicas reales tienen amplitudes muy pequeñas:
        - **EKG / ECG**: $1\\text{ mV} - 3\\text{ mV}$
        - **EMG**: $0.1\\text{ mV} - 5\\text{ mV}$
        - **EEG**: $10\\,\\mu\\text{V} - 100\\,\\mu\\text{V}$

        Dado que el DAC del ESP32 emite $3.3\\text{ V}$, si se conecta directamente a un amplificador de instrumentación (ej. AD620 con ganancia $G = 1000$), saturaría de inmediato. Se requiere un **divisor resistivo pasivo**.
        """)

    with col_g2:
        st.markdown("#### 3. Diagrama Esquemático del Divisor Resistivo")
        st.markdown("""
        ```
        ESP32 GPIO 25 (0 - 3.3V)
               │
              ┌┴┐
              │ │  R1 = 10 kΩ  (o 100 kΩ)
              └┬┘
               │
               ├───────────────────> Salida Atenuada (+) hacia electrodo EKG / AD620
               │
              ┌┴┐
              │ │  R2 = 10 Ω   (Atenuación ~ 1:1000 -> 0 - 3.3 mV)
              └┬┘
               │
        ESP32 GND ─────────────────> Salida de Referencia (-) GND
        ```
        """)

        st.markdown("#### 4. Relación de Atenuación:")
        st.latex(r"V_{out} = V_{DAC} \times \frac{R_2}{R_1 + R_2}")
        st.markdown("""
        Con $R_1 = 10\\text{ k}\\Omega$ y $R_2 = 10\\,\\Omega$:
        """)
        st.latex(r"V_{out} \approx 3.3\text{ V} \times \frac{10}{10010} \approx 3.3\text{ mV}")
        st.caption("¡Convierte el ESP32 en un simulador de paciente perfecto para calibrar equipos de electrocardiografía!")

    st.markdown("---")
    st.markdown("### 📋 Protocolo Serial Cayetino")
    st.markdown("""
    | Comando Serial | Parámetros | Respuesta ESP32 | Descripción |
    | :--- | :--- | :--- | :--- |
    | `PING` | Ninguno | `PONG:CAYETINO_ESP32_OK` | Prueba de vida del firmware. |
    | `LIST` | Ninguno | `FILES_START` ... `FILES_END` | Lista todos los archivos y metadatos en LittleFS. |
    | `SAVE_START:<name>:<fs>:<n>` | Nombre, Fs, muestras | `READY_CHUNKS` | Prepara archivo en LittleFS para escritura. |
    | `CHUNK:<v1,v2,...>` | Muestras 8-bit | `ACK_CHUNK` | Escribe bloque con control de flujo para evitar desbordamiento. |
    | `SAVE_END` | Ninguno | `OK_SAVE:<name>:<n>` | Cierra el archivo en LittleFS. |
    | `PLAY:<name>` | Nombre de archivo | `OK_PLAY:<name>:<fs>:<n>` | Carga el archivo en RAM e inicia el temporizador analógico DAC. |
    | `STOP` | Ninguno | `OK_STOP` | Detiene el temporizador y deja el DAC en reposo. |
    | `STATUS` | Ninguno | `STATUS:PLAYING:...` o `STATUS:IDLE` | Consulta si el DAC está reproduciendo. |
    | `DELETE:<name>` | Nombre de archivo | `OK_DELETE:<name>` | Borra el archivo de LittleFS. |
    | `FORMAT` | Ninguno | `OK_FORMAT` | Formatea el sistema de archivos Flash. |
    """)
