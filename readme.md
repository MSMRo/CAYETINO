# ⚡ Proyecto CAYETINO

Dispositivo generador de biopotenciales y señales sintéticas (EKG, EMG, EEG, RSP, PPG y ondas básicas) para entrenamiento y docencia de estudiantes de Ingeniería Biomédica.

![](./IMGS/Screenshot%202026-10-12%20232222.png)

![](./IMGS/Screenshot%202026-10-12%20232209.png)


El sistema se compone de dos módulos interconectados:
1. **Frontend / Interfaz de Control (Streamlit)**: Aplicación interactiva en Python que permite diseñar ondas básicas, sintetizar señales fisiológicas avanzadas con la librería **NeuroKit2**, inyectar fuentes de ruido clínico (interferencia electromagnética a 60 Hz, ruido térmico blanco y artefactos de movimiento), transferir los archivos vía Serial y gestionar la reproducción del hardware.
2. **Firmware de Adquisición y Emisión DAC (ESP32 en Arduino)**: Programa embebido que recibe los datos por comunicación serial por bloques con ACK, los almacena en el sistema de archivos no volátil **LittleFS**, y los reproduce en bucle continuo a través de su convertidor digital-analógico interno de 8 bits (**GPIO 25 / GPIO 26**) mediante un temporizador por hardware de 64 bits (`esp_timer`).

---

## 📁 Estructura del Repositorio

```
CAYETINO/
├── app_streamlit/                    # Interfaz gráfica de usuario y control
│   ├── app.py                       # Aplicación principal de Streamlit
│   ├── signal_generator.py          # Síntesis matemática, NeuroKit2 y ruido
│   ├── serial_comm.py               # Driver de comunicación serial y LittleFS
│   └── requirements.txt             # Dependencias en Python
├── firmware_esp32/
│   └── cayetino_esp32/
│       ├── cayetino_esp32.ino       # Código Arduino/C++ para ESP32
│       └── README.md                # Guía de compilación y flasheo
├── CIRCUITO_KICAD/                  # Archivos de hardware y PCB
├── run_app.bat                      # Lanzador directo de Streamlit para Windows
└── README.md                        # Documentación general
```

---

## 🚀 Inicio Rápido

### 1. Instalación de dependencias de Python
En una terminal con Python instalado:
```powershell
pip install -r app_streamlit/requirements.txt
```

Funciona con uv mejor.

### 2. Carga del Firmware en el ESP32
1. Conecta la placa ESP32 por USB a tu computadora.
2. Abre Arduino IDE y carga el archivo:
   `firmware_esp32/cayetino_esp32/cayetino_esp32.ino`
3. Selecciona tu placa (ej. **ESP32 Dev Module**) y el puerto COM asignado.
4. Presiona **Subir** (Upload).

### 3. Ejecución de la Interfaz Streamlit
Haz doble clic en `run_app.bat` o ejecuta:
```powershell
python -m streamlit run app_streamlit/app.py
```

---

## 🌟 Funcionalidades Detalladas

### 1. 📊 Modo Básico
- **Formas de onda disponibles**:
  - Senoidal
  - Triángulo
  - Cuadrada (con ciclo de trabajo ajustable)
  - Diente de sierra
  - Diente de sierra invertida
- **Parámetros configurables**:
  - Frecuencia de la señal ($f$ en Hz)
  - Frecuencia de muestreo ($F_s$ en Hz)
  - Duración de la ventana temporal ($T$ en segundos)
  - Amplitud y nivel de offset DC
- **Previsualización en tiempo real**: Visualización con **Plotly** de la forma de onda continua, la tensión de salida analógica ($0.0 - 3.3\text{ V}$) y el código digital cuantizado DAC ($0 - 255$).
- **Exportación**: Envío directo a la memoria flash LittleFS del ESP32 con selector de formato (`.csv`, `.txt`, `.dat`).

### 2. 🧬 Modo Avanzado (NeuroKit2 & Simulación Fisiológica)
- **Señales biomédicas sintéticas**:
  - **EKG / ECG**: Modelo dinámico de McSharry (*ecgsyn*) o modelo estándar, con ritmo cardíaco ajustable (BPM).
  - **EMG**: Electromiografía con ráfagas de activación y duración de contracción configurables.
  - **EEG**: Ondas electroencefalográficas con mezcla de ritmos fisiológicos (Alpha, Beta, Theta y componente estocástico 1/f).
  - **RSP**: Dinámica respiratoria sinusoidal con variabilidad.
  - **PPG**: Pulso arterial y fotopletismografía.
- **Módulo de Contaminación de Señales (Inyección de Ruido)**:
  - ⚡ **Interferencia de Red Eléctrica**: Onda senoidal armónica (60 Hz por defecto en Perú/América o 50 Hz) con amplitud graduable.
  - 🌫️ **Ruido Blanco Térmico**: Distribución Gaussiana $\mathcal{N}(0, \sigma^2)$ para modelar ruido de electrodo y circuitería analógica.
  - 📍 **Ruido Impulsional**: Artefactos de movimiento y desacople de electrodos (spikes aleatorios bipolares).
- **Análisis en Frecuencia (FFT)**: Espectro de potencia en tiempo real para verificar la presencia de armónicos contaminantes (pico a 60 Hz).

### 3. 💾 Gestor de Archivos en LittleFS y Control del DAC
- **Explorador Flash**: Muestra un cuadro/tarjeta con todos los archivos guardados en la memoria del ESP32, indicando:
  - Nombre del archivo
  - Frecuencia de muestreo original ($F_s$)
  - Cantidad total de muestras
  - Duración de la ventana en segundos
  - Tamaño ocupado en memoria Flash
- **Controles de Reproducción**:
  - ▶ **Reproducir (PLAY)**: El ESP32 carga la señal en memoria RAM y comienza la emisión analógica ininterrumpida en bucle por su DAC.
  - ⏹ **Detener (STOP)**: Detiene la emisión analógica y coloca la salida en nivel seguro de reposo ($\sim 1.65\text{ V}$).
  - 🗑 **Eliminar**: Borra el archivo seleccionado del sistema de archivos LittleFS.
  - 🔄 **Actualizar**: Lee el estado actual y archivos de la memoria del ESP32.
- **Modo Simulación**: Permite probar la interfaz, generación y gestión de archivos incluso si no tienes un ESP32 conectado en ese momento.

---

## 🔌 Conexión de Hardware y Salida Analógica

El microcontrolador ESP32 dispone de convertidores digital-analógicos internos de 8 bits en los siguientes pines:
- **DAC Canal 1**: `GPIO 25` (predeterminado)
- **DAC Canal 2**: `GPIO 26`
- **Referencia**: `GND`

### Divisor de Tensión para Amplificadores Biomédicos
Para conectar la salida del ESP32 a la entrada de un amplificador de biopotenciales (ej. AD620, INA128, frontend ADS1299) sin saturar las etapas de ganancia:

```
ESP32 GPIO 25 (0 - 3.3V)
       │
      ┌┴┐
      │ │  R1 = 10 kΩ
      └┬┘
       │
       ├───────────────────> Salida Atenuada (+) hacia entrada del amplificador
       │
      ┌┴┐
      │ │  R2 = 10 Ω   (Atenuación 1:1000 -> 0 - 3.3 mV)
      └┬┘
       │
ESP32 GND ─────────────────> Referencia de Tierra (-) GND
```

$$V_{out} = V_{DAC} \cdot \frac{R_2}{R_1 + R_2} \approx 3.3\text{ V} \cdot \frac{10}{10010} \approx 3.3\text{ mV}$$

---

## 📡 Protocolo de Comunicación Serial

La comunicación entre Streamlit y el ESP32 se realiza a **115200 baudios** mediante comandos de texto estructurados:

| Comando | Respuesta ESP32 | Descripción |
| :--- | :--- | :--- |
| `PING` | `PONG:CAYETINO_ESP32_OK` | Test de enlace serial. |
| `LIST` | `FILES_START` ... `FILES_END` | Lista los archivos en LittleFS con metadatos. |
| `SAVE_START:<nombre>:<fs>:<n>` | `READY_CHUNKS` | Inicia creación de archivo en LittleFS. |
| `CHUNK:<v1,v2,...>` | `ACK_CHUNK` | Envía bloque de muestras con confirmación de flujo. |
| `SAVE_END` | `OK_SAVE:<nombre>:<n>` | Finaliza y cierra el archivo en LittleFS. |
| `PLAY:<nombre>` | `OK_PLAY:<nombre>:<fs>:<n>` | Carga el archivo en RAM y activa el temporizador DAC. |
| `STOP` | `OK_STOP` | Detiene la generación analógica DAC. |
| `STATUS` | `STATUS:PLAYING:...` / `STATUS:IDLE` | Reporta el estado actual del DAC. |
| `DELETE:<nombre>` | `OK_DELETE:<nombre>` | Elimina un archivo de LittleFS. |
| `FORMAT` | `OK_FORMAT` | Formatea la memoria flash LittleFS. |
| `SET_DAC_PIN:<pin>` | `OK_DAC_PIN:<pin>` | Configura el pin DAC activo (25 o 26). |

![](./IMGS/Screenshot%202026-10-12%20232245.png)

![](./IMGS/Screenshot%202026-10-12%20232310.png)