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
├── app_pyqt6/                        # Interfaz nativa de escritorio en PyQt6
│   ├── main.py                      # Punto de entrada de la aplicación de escritorio
│   ├── main_window.py               # Ventana principal e integración de pestañas
│   ├── sidebar.py                   # Enlace serial, simulación y control DAC
│   ├── tab_basic.py                 # Modo básico: formas de onda periódicas
│   ├── tab_advanced.py              # Modo avanzado: biopotenciales y NeuroKit2
│   ├── tab_manager.py               # Explorador de archivos LittleFS y reproducción DAC
│   ├── tab_guide.py                 # Guía de hardware, circuito atenuador y protocolo
│   ├── styles.py                    # Hoja de estilos moderna inspirada en Streamlit
│   ├── workers.py                   # Subprocesos QThread asíncronos para Serial
│   ├── signal_generator.py          # Motor de síntesis fisiológica y ruido
│   └── serial_comm.py               # Driver de comunicación UART y LittleFS
├── app_streamlit/                    # Interfaz web de usuario y control (Streamlit)
│   ├── app.py                       # Aplicación principal de Streamlit
│   ├── signal_generator.py          # Síntesis matemática, NeuroKit2 y ruido
│   ├── serial_comm.py               # Driver de comunicación serial y LittleFS
│   └── requirements.txt             # Dependencias en Python
├── dist/
│   └── Cayetino_ESP32/              # Carpeta de distribución del ejecutable Windows
│       └── Cayetino_ESP32.exe       # Ejecutable nativo (.exe) para PC
├── firmware_esp32/
│   └── cayetino_esp32/
│       ├── cayetino_esp32.ino       # Código Arduino/C++ para ESP32
│       └── README.md                # Guía de compilación y flasheo
├── CIRCUITO_KICAD/                  # Archivos de hardware y PCB
├── run_cayetino_exe.bat             # Lanzador directo del ejecutable .exe compilado
├── run_app_pyqt.bat                 # Lanzador de la app PyQt6 en Python
├── run_app.bat                      # Lanzador de la app Streamlit
└── README.md                        # Documentación general
```

---

## 🚀 Inicio Rápido

### 1. Ejecutar el Ejecutable .EXE (Instalable/Portable en PC)
No requiere tener Python instalado:
- Haz doble clic en **`run_cayetino_exe.bat`** o abre directamente:
  `dist\Cayetino_ESP32\Cayetino_ESP32.exe`

### 2. Ejecutar la versión PyQt6 en Python
```powershell
.\run_app_pyqt.bat
```
O directamente con Python:
```powershell
python app_pyqt6/main.py
```

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
---

## 🏛️ Arquitectura del Sistema y Diagramas Técnicos (Mermaid)

Para comprender en profundidad el funcionamiento integral de la plataforma Cayetino (desde el diseño en el frontend de escritorio hasta la síntesis en tiempo real por interrupción en el microcontrolador), se detallan a continuación los diagramas arquitectónicos del proyecto:

---

### 1. 📐 Modelo C4 de Arquitectura

El modelo C4 permite descomponer la arquitectura en diferentes niveles de abstracción jerárquica:

#### Nivel 1: Diagrama de Contexto del Sistema (System Context)
Muestra cómo interactúa el usuario (estudiante o investigador biomédico) con la plataforma Cayetino y los equipos de instrumentación clínica externos.

```mermaid
flowchart TB
  subgraph Contexto ["C4 - Nivel 1: Contexto del Sistema CAYETINO"]
    User["👨‍🔬 Usuario Biomédico<br>[Estudiante / Investigador / Docente]<br>Diseña ondas, inyecta ruido clínico y controla reproducción"]
    
    CayetinoSystem["⚡ <b>Sistema CAYETINO</b><br>[Generador de Biopotenciales y Ondas Sintéticas]<br>Plataforma de software y hardware embebido basada en ESP32"]
    
    BioAmp["🩺 Amplificador de Biopotenciales<br>[AD620 / INA128 / ADS1299]<br>Captación de señales en rango de microvoltios/milivoltios"]
    
    Oscilloscope["📈 Instrumental de Diagnóstico<br>[Osciloscopio / DAQ / Raspberry Pi Pico ADC]<br>Medición y análisis directo en dominio temporal y espectral"]
    
    PC_Host["💻 Computadora Personal Windows<br>[Host PC]<br>Alimentación USB y canal UART bidireccional (115200 bps)"]

    User -->|"Configura parámetros y gestiona memoria Flash"| CayetinoSystem
    CayetinoSystem -->|"Emite señal atenuada segura (0.1 a 3.3 mV)"| BioAmp
    CayetinoSystem -->|"Emite señal DAC pura (0.0 a 3.3 V)"| Oscilloscope
    PC_Host <-->|"Enlace USB-UART Serial (CP210x)"| CayetinoSystem
  end
```

#### Nivel 2: Diagrama de Contenedores (Containers)
Describe las aplicaciones ejecutables, el firmware embebido en el ESP32, el almacenamiento Flash y el circuito atenuador pasivo.

```mermaid
flowchart TB
  subgraph Containers ["C4 - Nivel 2: Diagrama de Contenedores"]
    User["👨‍🔬 Usuario Biomédico"]

    subgraph HostPC ["Computadora Personal (Entorno Windows)"]
      PyQtApp["🖥️ <b>Aplicación de Escritorio PyQt6</b><br>[Python 3.12 / PyQt6 / PyInstaller .EXE]<br>Interfaz gráfica nativa de alto rendimiento con pyqtgraph y workers QThread"]
      StreamlitApp["🌐 <b>Aplicación Web Streamlit</b><br>[Python / Streamlit / Plotly]<br>Panel web interactivo accesible vía navegador local"]
    end

    subgraph EmbeddedESP32 ["Módulo Embebido ESP32 (Hardware Microcontrolador)"]
      FirmwareCore["⚙️ <b>Firmware C++ Cayetino</b><br>[Arduino Core / FreeRTOS / UART Driver]<br>Intérprete de comandos seriales, parser de chunks y despachador"]
      TimerEngine["⏱️ <b>Temporizador de Hardware</b><br>[esp_timer 64-bit]<br>Genera interrupciones periódicas a frecuencia exacta Fs"]
      FlashStorage[("💾 <b>Sistema de Archivos Flash</b><br>[LittleFS non-volatile]<br>Almacena archivos .csv, .txt y .dat de señales")]
      DACModule["⚡ <b>Convertidor DAC 8-bit</b><br>[Hardware DAC interno ESP32]<br>Emisión analógica por GPIO 25 o GPIO 26"]
    end

    subgraph CircuitPCB ["Placa de Acondicionamiento (Circuito KiCad)"]
      Attenuator["🎛️ <b>Divisor Atenuador Pasivo 1000:1</b><br>[R1 = 10 kΩ, R2 = 10 Ω]<br>Reduce la tensión de 3.3 V a niveles fisiológicos seguros"]
    end

    BioAmpExternal["🩺 Amplificador / Electrocardiógrafo Externo"]

    User -->|"Control interactivo nativo"| PyQtApp
    User -->|"Control web"| StreamlitApp
    PyQtApp <-->|"Comandos de texto y datos UART (115200 bps)"| FirmwareCore
    StreamlitApp <-->|"Comandos de texto y datos UART (115200 bps)"| FirmwareCore

    FirmwareCore <-->|"Lectura y escritura por bloques"| FlashStorage
    FirmwareCore -->|"Carga buffer a RAM y configura periodo"| TimerEngine
    TimerEngine -->|"Interrupción periódica dacWrite()"| DACModule
    DACModule -->|"Tensión analógica (0.0 V - 3.3 V)"| Attenuator
    Attenuator -->|"Tensión biomédica (0.1 mV - 3.3 mV)"| BioAmpExternal
  end
```

#### Nivel 3: Diagrama de Componentes (Components)
Detalla los módulos internos del frontend PyQt6 y las rutinas del firmware Arduino/C++.

```mermaid
flowchart TB
  subgraph ComponentsDiagram ["C4 - Nivel 3: Componentes de Software y Firmware"]
    subgraph FrontendPyQt6 ["Contenedor: Aplicación de Escritorio (app_pyqt6)"]
      MainWindow["<b>MainWindow</b><br>Ventana principal, control de pestañas y notificaciones flotantes"]
      Sidebar["<b>SidebarWidget</b><br>Gestión de puertos COM, modo simulación, selección DAC y formateo"]
      TabBasic["<b>TabBasicWave</b><br>Generador de ondas sintéticas, previsualización dual y guardado"]
      TabAdv["<b>TabAdvancedBio</b><br>Modelado NeuroKit2, inyector de 3 ruidos clínicos y FFT"]
      TabMgr["<b>TabManager</b><br>Tabla LittleFS, reproductor PLAY/STOP y prueba senoidal 5Hz"]
      TabGde["<b>TabGuide</b><br>Documentación interactiva y tabla del protocolo serial"]
      SignalGen["<b>signal_generator.py</b><br>Motor numérico: scipy.signal, neurokit2 y cuantización 8-bit"]
      Workers["<b>workers.py (QThreads)</b><br>ConnectWorker, SaveSignalWorker, PlayWorker, ListWorker, etc."]
      SerialDriver["<b>serial_comm.py (CayetinoSerial)</b><br>Controlador de comunicación física pyserial y virtual"]
    end

    subgraph FirmwareESP32 ["Contenedor: Firmware ESP32 (cayetino_esp32.ino)"]
      CmdParser["<b>Command Parser</b><br>Lectura de líneas UART, extracción de comandos y argumentos"]
      FsManager["<b>LittleFS File Manager</b><br>Lectura de encabezados, escritura incremental y borrado"]
      DacController["<b>Playback Controller</b><br>Carga de muestras a RAM estática y gestión de estados"]
      TimerService["<b>esp_timer Service</b><br>Configuración de alarma de microsegundos"]
      DacOutput["<b>DAC Hardware Output</b><br>Escritura analógica directa en registro DAC"]
    end

    MainWindow --> Sidebar
    MainWindow --> TabBasic
    MainWindow --> TabAdv
    MainWindow --> TabMgr
    MainWindow --> TabGde

    TabBasic --> SignalGen
    TabAdv --> SignalGen

    Sidebar --> Workers
    TabBasic --> Workers
    TabAdv --> Workers
    TabMgr --> Workers

    Workers --> SerialDriver
    SerialDriver <-->|"Línea Serial UART (TX/RX)"| CmdParser

    CmdParser --> FsManager
    CmdParser --> DacController
    DacController --> FsManager
    DacController --> TimerService
    TimerService --> DacOutput
  end
```

---

### 2. 🔄 Diagrama de Secuencia (Protocolo UART y Control de Flujo)

Describe el ciclo de vida completo de la comunicación entre la aplicación en la PC y el microcontrolador: handshake, guardado con confirmación por bloques (*stop-and-wait ACK*), reproducción continua por hardware y detención segura.

```mermaid
sequenceDiagram
  autonumber
  actor User as Usuario Biomédico
  participant UI as Interfaz Gráfica (PyQt6)
  participant Worker as QThread Worker (Background)
  participant Driver as CayetinoSerial (Driver PC)
  participant SerialPort as Puerto Serial COM (USB UART)
  participant ESP32 as Firmware ESP32 (Parser)
  participant LittleFS as Memoria Flash (LittleFS)
  participant Timer as esp_timer (Hardware Timer)
  participant DAC as DAC 8-bit (GPIO 25/26)
  participant Circuit as Divisor Atenuador (1000:1)

  %% 1. Handshake
  Note over User, ESP32: 1. Establecimiento de Enlace Serial (Handshake)
  User->>UI: Clic en "Conectar" (COM7, 115200 bps)
  UI->>Worker: Iniciar ConnectWorker(port, 115200)
  Worker->>Driver: connect(port, baudrate)
  Driver->>SerialPort: Abrir conexión COM y limpiar buffers
  Driver->>SerialPort: Enviar "PING\n"
  SerialPort->>ESP32: Recibe "PING"
  ESP32-->>SerialPort: Responde "PONG:CAYETINO_ESP32_OK\n"
  SerialPort-->>Driver: Lectura de respuesta PONG
  Driver-->>Worker: Conexión verificada exitosa (True)
  Worker-->>UI: Emite finished(True)
  UI-->>User: Actualiza estado a "🟢 Conectado"

  %% 2. Guardado con control de flujo
  Note over User, LittleFS: 2. Transmisión y Grabación de Señal en Flash con Flow-Control
  User->>UI: Diseña EKG y pulsa "🚀 Enviar y Guardar"
  UI->>Worker: Iniciar SaveSignalWorker("ekg_5s.csv", 250 Hz, 1250 muestras)
  Worker->>Driver: save_file(filename, fs, dac_values, chunk_size=64)
  Driver->>SerialPort: Enviar "SAVE_START:ekg_5s.csv:250:1250\n"
  SerialPort->>ESP32: Recibe SAVE_START
  ESP32->>LittleFS: LittleFS.open("ekg_5s.csv", "w")
  ESP32-->>SerialPort: Responde "READY_CHUNKS\n"
  SerialPort-->>Driver: Confirma preparación del microcontrolador

  loop Transmisión por bloques de 64 muestras con verificación ACK
    Driver->>SerialPort: Enviar "CHUNK:128,135,142,...\n"
    SerialPort->>ESP32: Escribe bloque en archivo de Flash
    ESP32-->>SerialPort: Responde "ACK_CHUNK\n"
    SerialPort-->>Driver: ACK_CHUNK recibido
    Driver-->>Worker: Notifica avance de progreso (p %)
    Worker-->>UI: Actualiza QProgressBar en tiempo real
  end

  Driver->>SerialPort: Enviar "SAVE_END\n"
  ESP32->>LittleFS: file.close() (Consolida archivo)
  ESP32-->>SerialPort: Responde "OK_SAVE:ekg_5s.csv:1250\n"
  Driver-->>Worker: Guardado finalizado con éxito
  Worker-->>UI: Despliega notificación toast "✅ Archivo grabado"
  UI->>Worker: Iniciar ListFilesWorker() para refrescar tabla

  %% 3. Reproducción continua por DAC
  Note over User, Circuit: 3. Carga en RAM y Reproducción Analógica Continua
  User->>UI: Selecciona "ekg_5s.csv" y pulsa "▶️ REPRODUCIR (PLAY)"
  UI->>Worker: Iniciar PlayFileWorker("ekg_5s.csv")
  Worker->>Driver: play_file("ekg_5s.csv")
  Driver->>SerialPort: Enviar "PLAY:ekg_5s.csv\n"
  SerialPort->>ESP32: Recibe comando PLAY
  ESP32->>LittleFS: Lee archivo y extrae 1250 muestras
  ESP32->>ESP32: Almacena muestras en buffer dinámico de RAM
  ESP32->>Timer: esp_timer_create() y esp_timer_start_periodic(4000 µs)
  ESP32-->>SerialPort: Responde "OK_PLAY:ekg_5s.csv:250:1250\n"
  Driver-->>UI: Actualiza banner a "▶️ REPRODUCIENDO EN VIVO"

  loop Bucle de Emisión Analógica por Interrupción Hardware (ESP32)
    Timer->>DAC: Interrupción periódica: dacWrite(GPIO_25, buffer[i++])
    DAC->>Circuit: Salida analógica directa (0.0 V - 3.3 V)
    Circuit-->>User: Salida atenuada pasiva (0.1 mV - 3.3 mV) a electrodos
  end

  %% 4. Detención segura
  Note over User, DAC: 4. Detención Segura y Nivel de Reposo
  User->>UI: Pulsa "⏹️ DETENER (STOP)"
  UI->>Worker: Iniciar StopWorker()
  Worker->>Driver: stop_playback()
  Driver->>SerialPort: Enviar "STOP\n"
  ESP32->>Timer: esp_timer_stop() (Detiene temporizador)
  ESP32->>DAC: dacWrite(pin, 128) (Coloca DAC en nivel neutro ~1.65 V)
  ESP32-->>SerialPort: Responde "OK_STOP\n"
  UI-->>User: Banner cambia a "⏹️ ESP32 EN ESPERA"
```

---

### 3. 🧠 Diagrama Lógico y Flujo de Procesamiento Numérico

Ilustra la tubería de transformación de datos (*pipeline*), desde la especificación paramétrica matemática hasta la generación física de potenciales eléctricos:

```mermaid
flowchart TD
  subgraph Stage1 ["1. Parámetros de Entrada (Frontend)"]
    P_Type["<b>Selección de Señal:</b><br>• Básicas (Seno, Cuadrada, etc.)<br>• Biomédicas (EKG, EMG, EEG, RSP, PPG)"]
    P_Timing["<b>Parámetros Temporales:</b><br>• Frecuencia Fs (50 a 20000 Hz)<br>• Duración T (0.1 a 15.0 s)<br>• N = round(Fs * T)"]
    P_Noise["<b>Inyección de Ruido Clínico:</b><br>• Red Eléctrica (60 Hz / 50 Hz)<br>• Ruido Blanco Gaussiano (σ)<br>• Spikes impulsionales de movimiento"]
  end

  subgraph Stage2 ["2. Motor de Síntesis Matemática y Fisiológica"]
    Branch_Basic["<b>Síntesis Básica (scipy.signal / numpy):</b><br>t = linspace(0, T, N)<br>y = Amplitud * Onda(2πft, duty) + Offset"]
    Branch_Bio["<b>Síntesis Biomédica (NeuroKit2):</b><br>• ECG: Modelo diferencial McSharry (ecgsyn)<br>• EMG: Ráfagas de activación y contracción<br>• EEG: Superposición bandas α, β, θ + ruido 1/f<br>• RSP / PPG: Modelos de pulso y respiración"]
    P_Type --> Branch_Basic
    P_Type --> Branch_Bio
    P_Timing --> Branch_Basic
    P_Timing --> Branch_Bio
  end

  subgraph Stage3 ["3. Módulo de Contaminación de Señal"]
    CleanSignal["Señal Limpia Sintética: y_limpia(t)"]
    Branch_Basic --> CleanSignal
    Branch_Bio --> CleanSignal

    SineNoise["+ Armónico de Red: A_red * sin(2π * f_red * t)"]
    WhiteNoise["+ Ruido Blanco: normal(0, σ, N)"]
    ImpulseNoise["+ Spikes: Máscara Bernoulli * Amplitud bipolar"]

    CleanSignal --> SineNoise
    SineNoise --> WhiteNoise
    WhiteNoise --> ImpulseNoise
    NoisySignal["Señal Contaminada Final: y_contaminada(t)"]
    ImpulseNoise --> NoisySignal
  end

  subgraph Stage4 ["4. Análisis y Previsualización Gráfica"]
    FFT_Block["<b>Análisis Espectral FFT:</b><br>Y(f) = |rfft(y)| / N<br>Espectro de densidad de 0 a 120 Hz"]
    Plot_Time["<b>Gráficas Temporales Duales:</b><br>pyqtgraph / Plotly<br>Limpia vs. Contaminada vs. Salida DAC"]
    NoisySignal --> FFT_Block
    NoisySignal --> Plot_Time
  end

  subgraph Stage5 ["5. Mapeo y Cuantización a DAC de 8 Bits"]
    Norm["<b>Normalización con Margen Anti-Clipping:</b><br>norm = (y - min_margen) / (max_margen - min_margen)"]
    Quantize["<b>Cuantización Entera Discreta (0 - 255):</b><br>dac_8bit = clip(round(norm * 255), 0, 255)"]
    VoltCalc["<b>Tensión Analógica Estimada:</b><br>V_dac = dac_8bit * (3.3 V / 255.0)"]

    NoisySignal --> Norm
    Norm --> Quantize
    Quantize --> VoltCalc
    VoltCalc --> Plot_Time
  end

  subgraph Stage6 ["6. Serialización y Transmisión por Bloques"]
    FormatFile["<b>Formateo de Archivo:</b><br>#FS, #COUNT, #FORMAT + Filas CSV o datos TXT"]
    Chunking["<b>División en Bloques:</b><br>Paquetes CHUNK de 64 muestras"]
    FlowControl["<b>Transmisión con Handshake UART:</b><br>SAVE_START -> CHUNK + ACK -> SAVE_END"]

    Quantize --> FormatFile
    FormatFile --> Chunking
    Chunking --> FlowControl
  end

  subgraph Stage7 ["7. Recepción y Generación Embebida (ESP32)"]
    FlashSave["<b>Almacenamiento No Volátil:</b><br>Archivo grabado en LittleFS SPI Flash"]
    RAMBuffer["<b>Buffer de Reproducción:</b><br>uint8_t* dacBuffer asignado en memoria RAM"]
    TimerISR["<b>Interrupción Periódica de Alta Resolución:</b><br>esp_timer dispara alarma cada Ts = 1/Fs microsegundos"]
    DACWrite["<b>Registro DAC Hardware:</b><br>dacWrite(GPIO_25, dacBuffer[idx++]) (0.0 V - 3.3 V)"]

    FlowControl -->|"Cable USB UART"| FlashSave
    FlashSave -->|"Comando PLAY"| RAMBuffer
    RAMBuffer --> TimerISR
    TimerISR --> DACWrite
  end

  subgraph Stage8 ["8. Acondicionamiento Analógico Biomédico"]
    PassiveDivider["<b>Divisor Pasivo 1000:1 (Hardware KiCad):</b><br>R1 = 10 kΩ, R2 = 10 Ω"]
    BiomedicalSignal["<b>Biopotencial Seguro Calibrado:</b><br>0.1 mV a 3.3 mV (Nivel Fisiológico)"]
    MedicalDevice["<b>Dispositivo Receptor:</b><br>Amplificador AD620 / INA128 / Electrocardiógrafo Clínico"]

    DACWrite -->|"0.0 V - 3.3 V"| PassiveDivider
    PassiveDivider -->|"0.1 mV - 3.3 mV"| BiomedicalSignal
    BiomedicalSignal --> MedicalDevice
  end
```

---

### 4. 🧩 Diagrama UML de Clases y Estructura de Código

Representa la estructura orientada a objetos de la aplicación PyQt6, los trabajadores en segundo plano (`QThread`), el driver serial y la arquitectura del firmware embebido:

```mermaid
classDiagram
  direction TB

  class MainWindow {
    -serial_client: CayetinoSerial
    -sidebar: SidebarWidget
    -tabs: QTabWidget
    -tab_basic: TabBasicWave
    -tab_adv: TabAdvancedBio
    -tab_manager: TabManager
    -tab_guide: TabGuide
    -toast_frame: QFrame
    -lbl_toast: QLabel
    +__init__()
    -_setup_ui() void
    -_connect_signals() void
    -_on_file_saved(msg: str) void
    -_on_connection_changed(connected: bool) void
    -_on_dac_pin_changed(pin: int) void
    -_on_fs_formatted() void
  }

  class SidebarWidget {
    -client: CayetinoSerial
    -connect_worker: ConnectWorker
    -format_worker: FormatFSWorker
    -chk_simulation: QCheckBox
    -cmb_ports: QComboBox
    -cmb_baud: QComboBox
    -btn_connect: QPushButton
    -btn_group_dac: QButtonGroup
    +connection_changed: pyqtSignal
    +dac_pin_changed: pyqtSignal
    +fs_formatted: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_connect_signals() void
    +refresh_ports() void
    +get_active_dac_pin() int
    -_on_sim_toggled(checked: bool) void
    -_on_connect_toggle() void
    -_on_connect_finished(success: bool, msg: str) void
    -_set_connected_state(connected: bool) void
    -_on_apply_dac() void
    -_on_format_clicked() void
    -_on_format_finished(success: bool, msg: str) void
  }

  class TabBasicWave {
    -client: CayetinoSerial
    -save_worker: SaveSignalWorker
    -current_t: ndarray
    -current_y: ndarray
    -current_dac: ndarray
    -current_volt: ndarray
    -cmb_wave: QComboBox
    -spn_freq: QDoubleSpinBox
    -sld_amp: QSlider
    -sld_offset: QSlider
    -sld_duty: QSlider
    -spn_fs: QSpinBox
    -spn_dur: QDoubleSpinBox
    -win: GraphicsLayoutWidget
    -curve_volt: PlotDataItem
    -curve_dac: PlotDataItem
    +file_saved: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_setup_plots() void
    -_connect_signals() void
    +update_signal() void
    -_on_wave_changed() void
    -_update_default_filename() void
    -_on_send_clicked() void
    -_on_save_progress(percent: int, msg: str) void
    -_on_save_finished(success: bool, msg: str) void
  }

  class TabAdvancedBio {
    -client: CayetinoSerial
    -save_worker: SaveSignalWorker
    -calc_timer: QTimer
    -current_t: ndarray
    -current_clean: ndarray
    -current_noisy: ndarray
    -current_dac: ndarray
    -current_volt: ndarray
    -cmb_bio_type: QComboBox
    -sld_hr: QSlider
    -cmb_method: QComboBox
    -spn_bursts: QSpinBox
    -spn_burst_dur: QDoubleSpinBox
    -chk_sine_noise: QCheckBox
    -chk_white_noise: QCheckBox
    -chk_impulse_noise: QCheckBox
    -win_time: GraphicsLayoutWidget
    -win_fft: GraphicsLayoutWidget
    +file_saved: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_setup_plots() void
    -_connect_signals() void
    +schedule_update() void
    -_compute_and_render() void
    -_update_contextual_controls() void
    -_update_default_filename() void
    -_on_send_clicked() void
  }

  class TabManager {
    -client: CayetinoSerial
    -get_dac_pin: callable
    -poll_timer: QTimer
    -files_cache: list
    -current_status: dict
    -table: QTableWidget
    -cmb_files: QComboBox
    -btn_play: QPushButton
    -btn_stop: QPushButton
    -btn_del: QPushButton
    -btn_test_sine: QPushButton
    -status_banner: QFrame
    +status_updated: pyqtSignal
    +__init__(serial_client, get_dac_pin_func, parent)
    -_setup_ui() void
    -_connect_signals() void
    +refresh_file_list() void
    -_on_files_listed(success: bool, files: list, msg: str) void
    -_render_table(files: list) void
    -_on_play_clicked() void
    -_on_stop_clicked() void
    -_on_delete_clicked() void
    -_on_test_sine_clicked() void
    -_poll_status() void
    -_update_banner(stat: dict) void
  }

  class TabGuide {
    -browser: QTextBrowser
    +__init__(parent)
    -_setup_ui() void
  }

  class CayetinoSerial {
    +simulation_mode: bool
    +ser: Serial
    +port: str
    +baudrate: int
    +sim_files: dict
    +sim_status: dict
    +__init__(simulation_mode: bool)
    +connect(port: str, baudrate: int, timeout: float) bool
    +disconnect() void
    +is_connected() bool
    +ping() bool
    +list_files() list
    +save_file(filename: str, fs: int, dac_values: ndarray, chunk_size: int, progress_callback: callable) bool
    +play_file(filename: str) dict
    +stop_playback() bool
    +delete_file(filename: str) bool
    +format_fs() bool
    +get_status() dict
    +set_dac_pin(pin: int) bool
    +play_test_sine() dict
  }

  class SignalGeneratorModule {
    <<módulo>>
    +generate_basic_signal(signal_type, freq, fs, duration, amplitude, offset, duty_cycle) tuple
    +generate_biomedical_signal(bio_type, fs, duration, heart_rate, burst_number, burst_duration, method) tuple
    +contaminate_signal(signal, fs, white_noise_amp, sine_noise_amp, sine_noise_freq, impulse_noise_prob, impulse_noise_amp) ndarray
    +map_to_dac_8bit(signal, auto_scale, target_min_val, target_max_val, margin_percent) tuple
    +format_file_content(dac_values, fs, ext) str
  }

  class ConnectWorker {
    -client: CayetinoSerial
    -port: str
    -baudrate: int
    +finished: pyqtSignal
    +run() void
  }

  class SaveSignalWorker {
    -client: CayetinoSerial
    -filename: str
    -fs: int
    -dac_values: ndarray
    +progress: pyqtSignal
    +finished: pyqtSignal
    +run() void
  }

  class ListFilesWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class PlayFileWorker {
    -client: CayetinoSerial
    -filename: str
    +finished: pyqtSignal
    +run() void
  }

  class StopWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class DeleteFileWorker {
    -client: CayetinoSerial
    -filename: str
    +finished: pyqtSignal
    +run() void
  }

  class FormatFSWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class TestSineWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class CayetinoFirmwareESP32 {
    <<firmware C++>>
    -currentDacPin: int = 25
    -isPlaying: bool = false
    -dacBuffer: uint8_t*
    -dacBufferLen: int
    -dacBufferIndex: int
    -espTimerHandle: esp_timer_handle_t
    +setup() void
    +loop() void
    +handleCommand(cmd: String) void
    +cmdList() void
    +cmdSaveStart(filename, fs, samples) void
    +cmdChunk(csvLine) void
    +cmdSaveEnd() void
    +cmdPlay(filename) void
    +cmdStop() void
    +cmdStatus() void
    +cmdDelete(filename) void
    +cmdFormat() void
    +cmdTestSine() void
    +dacTimerCallback(arg: void*) void
  }

  %% Relaciones de Composición y Agregación
  MainWindow *-- SidebarWidget
  MainWindow *-- TabBasicWave
  MainWindow *-- TabAdvancedBio
  MainWindow *-- TabManager
  MainWindow *-- TabGuide
  MainWindow o-- CayetinoSerial

  SidebarWidget ..> ConnectWorker : crea
  SidebarWidget ..> FormatFSWorker : crea
  SidebarWidget o-- CayetinoSerial

  TabBasicWave ..> SaveSignalWorker : crea
  TabBasicWave ..> SignalGeneratorModule : usa
  TabBasicWave o-- CayetinoSerial

  TabAdvancedBio ..> SaveSignalWorker : crea
  TabAdvancedBio ..> SignalGeneratorModule : usa
  TabAdvancedBio o-- CayetinoSerial

  TabManager ..> ListFilesWorker : crea
  TabManager ..> PlayFileWorker : crea
  TabManager ..> StopWorker : crea
  TabManager ..> DeleteFileWorker : crea
  TabManager ..> TestSineWorker : crea
  TabManager o-- CayetinoSerial

  %% Relaciones de llamada de Workers a Driver
  ConnectWorker --> CayetinoSerial : invoca
  SaveSignalWorker --> CayetinoSerial : invoca
  ListFilesWorker --> CayetinoSerial : invoca
  PlayFileWorker --> CayetinoSerial : invoca
  StopWorker --> CayetinoSerial : invoca
  DeleteFileWorker --> CayetinoSerial : invoca
  FormatFSWorker --> CayetinoSerial : invoca
  TestSineWorker --> CayetinoSerial : invoca

  %% Interacción física Driver con Firmware
  CayetinoSerial ..> CayetinoFirmwareESP32 : "Protocolo UART bidireccional (115200 bps)"
```

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



---

## 🏛️ Arquitectura del Sistema y Diagramas Técnicos (Mermaid)

Para comprender en profundidad el funcionamiento integral de la plataforma Cayetino (desde el diseño en el frontend de escritorio hasta la síntesis en tiempo real por interrupción en el microcontrolador), se detallan a continuación los diagramas arquitectónicos del proyecto:

---

### 1. 📐 Modelo C4 de Arquitectura

El modelo C4 permite descomponer la arquitectura en diferentes niveles de abstracción jerárquica:

#### Nivel 1: Diagrama de Contexto del Sistema (System Context)
Muestra cómo interactúa el usuario (estudiante o investigador biomédico) con la plataforma Cayetino y los equipos de instrumentación clínica externos.

```mermaid
flowchart TB
  subgraph Contexto ["C4 - Nivel 1: Contexto del Sistema CAYETINO"]
    User["👨‍🔬 Usuario Biomédico<br>[Estudiante / Investigador / Docente]<br>Diseña ondas, inyecta ruido clínico y controla reproducción"]
    
    CayetinoSystem["⚡ <b>Sistema CAYETINO</b><br>[Generador de Biopotenciales y Ondas Sintéticas]<br>Plataforma de software y hardware embebido basada en ESP32"]
    
    BioAmp["🩺 Amplificador de Biopotenciales<br>[AD620 / INA128 / ADS1299]<br>Captación de señales en rango de microvoltios/milivoltios"]
    
    Oscilloscope["📈 Instrumental de Diagnóstico<br>[Osciloscopio / DAQ / Raspberry Pi Pico ADC]<br>Medición y análisis directo en dominio temporal y espectral"]
    
    PC_Host["💻 Computadora Personal Windows<br>[Host PC]<br>Alimentación USB y canal UART bidireccional (115200 bps)"]

    User -->|"Configura parámetros y gestiona memoria Flash"| CayetinoSystem
    CayetinoSystem -->|"Emite señal atenuada segura (0.1 a 3.3 mV)"| BioAmp
    CayetinoSystem -->|"Emite señal DAC pura (0.0 a 3.3 V)"| Oscilloscope
    PC_Host <-->|"Enlace USB-UART Serial (CP210x)"| CayetinoSystem
  end
```

#### Nivel 2: Diagrama de Contenedores (Containers)
Describe las aplicaciones ejecutables, el firmware embebido en el ESP32, el almacenamiento Flash y el circuito atenuador pasivo.

```mermaid
flowchart TB
  subgraph Containers ["C4 - Nivel 2: Diagrama de Contenedores"]
    User["👨‍🔬 Usuario Biomédico"]

    subgraph HostPC ["Computadora Personal (Entorno Windows)"]
      PyQtApp["🖥️ <b>Aplicación de Escritorio PyQt6</b><br>[Python 3.12 / PyQt6 / PyInstaller .EXE]<br>Interfaz gráfica nativa de alto rendimiento con pyqtgraph y workers QThread"]
      StreamlitApp["🌐 <b>Aplicación Web Streamlit</b><br>[Python / Streamlit / Plotly]<br>Panel web interactivo accesible vía navegador local"]
    end

    subgraph EmbeddedESP32 ["Módulo Embebido ESP32 (Hardware Microcontrolador)"]
      FirmwareCore["⚙️ <b>Firmware C++ Cayetino</b><br>[Arduino Core / FreeRTOS / UART Driver]<br>Intérprete de comandos seriales, parser de chunks y despachador"]
      TimerEngine["⏱️ <b>Temporizador de Hardware</b><br>[esp_timer 64-bit]<br>Genera interrupciones periódicas a frecuencia exacta Fs"]
      FlashStorage[("💾 <b>Sistema de Archivos Flash</b><br>[LittleFS non-volatile]<br>Almacena archivos .csv, .txt y .dat de señales")]
      DACModule["⚡ <b>Convertidor DAC 8-bit</b><br>[Hardware DAC interno ESP32]<br>Emisión analógica por GPIO 25 o GPIO 26"]
    end

    subgraph CircuitPCB ["Placa de Acondicionamiento (Circuito KiCad)"]
      Attenuator["🎛️ <b>Divisor Atenuador Pasivo 1000:1</b><br>[R1 = 10 kΩ, R2 = 10 Ω]<br>Reduce la tensión de 3.3 V a niveles fisiológicos seguros"]
    end

    BioAmpExternal["🩺 Amplificador / Electrocardiógrafo Externo"]

    User -->|"Control interactivo nativo"| PyQtApp
    User -->|"Control web"| StreamlitApp
    PyQtApp <-->|"Comandos de texto y datos UART (115200 bps)"| FirmwareCore
    StreamlitApp <-->|"Comandos de texto y datos UART (115200 bps)"| FirmwareCore

    FirmwareCore <-->|"Lectura y escritura por bloques"| FlashStorage
    FirmwareCore -->|"Carga buffer a RAM y configura periodo"| TimerEngine
    TimerEngine -->|"Interrupción periódica dacWrite()"| DACModule
    DACModule -->|"Tensión analógica (0.0 V - 3.3 V)"| Attenuator
    Attenuator -->|"Tensión biomédica (0.1 mV - 3.3 mV)"| BioAmpExternal
  end
```

#### Nivel 3: Diagrama de Componentes (Components)
Detalla los módulos internos del frontend PyQt6 y las rutinas del firmware Arduino/C++.

```mermaid
flowchart TB
  subgraph ComponentsDiagram ["C4 - Nivel 3: Componentes de Software y Firmware"]
    subgraph FrontendPyQt6 ["Contenedor: Aplicación de Escritorio (app_pyqt6)"]
      MainWindow["<b>MainWindow</b><br>Ventana principal, control de pestañas y notificaciones flotantes"]
      Sidebar["<b>SidebarWidget</b><br>Gestión de puertos COM, modo simulación, selección DAC y formateo"]
      TabBasic["<b>TabBasicWave</b><br>Generador de ondas sintéticas, previsualización dual y guardado"]
      TabAdv["<b>TabAdvancedBio</b><br>Modelado NeuroKit2, inyector de 3 ruidos clínicos y FFT"]
      TabMgr["<b>TabManager</b><br>Tabla LittleFS, reproductor PLAY/STOP y prueba senoidal 5Hz"]
      TabGde["<b>TabGuide</b><br>Documentación interactiva y tabla del protocolo serial"]
      SignalGen["<b>signal_generator.py</b><br>Motor numérico: scipy.signal, neurokit2 y cuantización 8-bit"]
      Workers["<b>workers.py (QThreads)</b><br>ConnectWorker, SaveSignalWorker, PlayWorker, ListWorker, etc."]
      SerialDriver["<b>serial_comm.py (CayetinoSerial)</b><br>Controlador de comunicación física pyserial y virtual"]
    end

    subgraph FirmwareESP32 ["Contenedor: Firmware ESP32 (cayetino_esp32.ino)"]
      CmdParser["<b>Command Parser</b><br>Lectura de líneas UART, extracción de comandos y argumentos"]
      FsManager["<b>LittleFS File Manager</b><br>Lectura de encabezados, escritura incremental y borrado"]
      DacController["<b>Playback Controller</b><br>Carga de muestras a RAM estática y gestión de estados"]
      TimerService["<b>esp_timer Service</b><br>Configuración de alarma de microsegundos"]
      DacOutput["<b>DAC Hardware Output</b><br>Escritura analógica directa en registro DAC"]
    end

    MainWindow --> Sidebar
    MainWindow --> TabBasic
    MainWindow --> TabAdv
    MainWindow --> TabMgr
    MainWindow --> TabGde

    TabBasic --> SignalGen
    TabAdv --> SignalGen

    Sidebar --> Workers
    TabBasic --> Workers
    TabAdv --> Workers
    TabMgr --> Workers

    Workers --> SerialDriver
    SerialDriver <-->|"Línea Serial UART (TX/RX)"| CmdParser

    CmdParser --> FsManager
    CmdParser --> DacController
    DacController --> FsManager
    DacController --> TimerService
    TimerService --> DacOutput
  end
```

---

### 2. 🔄 Diagrama de Secuencia (Protocolo UART y Control de Flujo)

Describe el ciclo de vida completo de la comunicación entre la aplicación en la PC y el microcontrolador: handshake, guardado con confirmación por bloques (*stop-and-wait ACK*), reproducción continua por hardware y detención segura.

```mermaid
sequenceDiagram
  autonumber
  actor User as Usuario Biomédico
  participant UI as Interfaz Gráfica (PyQt6)
  participant Worker as QThread Worker (Background)
  participant Driver as CayetinoSerial (Driver PC)
  participant SerialPort as Puerto Serial COM (USB UART)
  participant ESP32 as Firmware ESP32 (Parser)
  participant LittleFS as Memoria Flash (LittleFS)
  participant Timer as esp_timer (Hardware Timer)
  participant DAC as DAC 8-bit (GPIO 25/26)
  participant Circuit as Divisor Atenuador (1000:1)

  %% 1. Handshake
  Note over User, ESP32: 1. Establecimiento de Enlace Serial (Handshake)
  User->>UI: Clic en "Conectar" (COM7, 115200 bps)
  UI->>Worker: Iniciar ConnectWorker(port, 115200)
  Worker->>Driver: connect(port, baudrate)
  Driver->>SerialPort: Abrir conexión COM y limpiar buffers
  Driver->>SerialPort: Enviar "PING\n"
  SerialPort->>ESP32: Recibe "PING"
  ESP32-->>SerialPort: Responde "PONG:CAYETINO_ESP32_OK\n"
  SerialPort-->>Driver: Lectura de respuesta PONG
  Driver-->>Worker: Conexión verificada exitosa (True)
  Worker-->>UI: Emite finished(True)
  UI-->>User: Actualiza estado a "🟢 Conectado"

  %% 2. Guardado con control de flujo
  Note over User, LittleFS: 2. Transmisión y Grabación de Señal en Flash con Flow-Control
  User->>UI: Diseña EKG y pulsa "🚀 Enviar y Guardar"
  UI->>Worker: Iniciar SaveSignalWorker("ekg_5s.csv", 250 Hz, 1250 muestras)
  Worker->>Driver: save_file(filename, fs, dac_values, chunk_size=64)
  Driver->>SerialPort: Enviar "SAVE_START:ekg_5s.csv:250:1250\n"
  SerialPort->>ESP32: Recibe SAVE_START
  ESP32->>LittleFS: LittleFS.open("ekg_5s.csv", "w")
  ESP32-->>SerialPort: Responde "READY_CHUNKS\n"
  SerialPort-->>Driver: Confirma preparación del microcontrolador

  loop Transmisión por bloques de 64 muestras con verificación ACK
    Driver->>SerialPort: Enviar "CHUNK:128,135,142,...\n"
    SerialPort->>ESP32: Escribe bloque en archivo de Flash
    ESP32-->>SerialPort: Responde "ACK_CHUNK\n"
    SerialPort-->>Driver: ACK_CHUNK recibido
    Driver-->>Worker: Notifica avance de progreso (p %)
    Worker-->>UI: Actualiza QProgressBar en tiempo real
  end

  Driver->>SerialPort: Enviar "SAVE_END\n"
  ESP32->>LittleFS: file.close() (Consolida archivo)
  ESP32-->>SerialPort: Responde "OK_SAVE:ekg_5s.csv:1250\n"
  Driver-->>Worker: Guardado finalizado con éxito
  Worker-->>UI: Despliega notificación toast "✅ Archivo grabado"
  UI->>Worker: Iniciar ListFilesWorker() para refrescar tabla

  %% 3. Reproducción continua por DAC
  Note over User, Circuit: 3. Carga en RAM y Reproducción Analógica Continua
  User->>UI: Selecciona "ekg_5s.csv" y pulsa "▶️ REPRODUCIR (PLAY)"
  UI->>Worker: Iniciar PlayFileWorker("ekg_5s.csv")
  Worker->>Driver: play_file("ekg_5s.csv")
  Driver->>SerialPort: Enviar "PLAY:ekg_5s.csv\n"
  SerialPort->>ESP32: Recibe comando PLAY
  ESP32->>LittleFS: Lee archivo y extrae 1250 muestras
  ESP32->>ESP32: Almacena muestras en buffer dinámico de RAM
  ESP32->>Timer: esp_timer_create() y esp_timer_start_periodic(4000 µs)
  ESP32-->>SerialPort: Responde "OK_PLAY:ekg_5s.csv:250:1250\n"
  Driver-->>UI: Actualiza banner a "▶️ REPRODUCIENDO EN VIVO"

  loop Bucle de Emisión Analógica por Interrupción Hardware (ESP32)
    Timer->>DAC: Interrupción periódica: dacWrite(GPIO_25, buffer[i++])
    DAC->>Circuit: Salida analógica directa (0.0 V - 3.3 V)
    Circuit-->>User: Salida atenuada pasiva (0.1 mV - 3.3 mV) a electrodos
  end

  %% 4. Detención segura
  Note over User, DAC: 4. Detención Segura y Nivel de Reposo
  User->>UI: Pulsa "⏹️ DETENER (STOP)"
  UI->>Worker: Iniciar StopWorker()
  Worker->>Driver: stop_playback()
  Driver->>SerialPort: Enviar "STOP\n"
  ESP32->>Timer: esp_timer_stop() (Detiene temporizador)
  ESP32->>DAC: dacWrite(pin, 128) (Coloca DAC en nivel neutro ~1.65 V)
  ESP32-->>SerialPort: Responde "OK_STOP\n"
  UI-->>User: Banner cambia a "⏹️ ESP32 EN ESPERA"
```

---

### 3. 🧠 Diagrama Lógico y Flujo de Procesamiento Numérico

Ilustra la tubería de transformación de datos (*pipeline*), desde la especificación paramétrica matemática hasta la generación física de potenciales eléctricos:

```mermaid
flowchart TD
  subgraph Stage1 ["1. Parámetros de Entrada (Frontend)"]
    P_Type["<b>Selección de Señal:</b><br>• Básicas (Seno, Cuadrada, etc.)<br>• Biomédicas (EKG, EMG, EEG, RSP, PPG)"]
    P_Timing["<b>Parámetros Temporales:</b><br>• Frecuencia Fs (50 a 20000 Hz)<br>• Duración T (0.1 a 15.0 s)<br>• N = round(Fs * T)"]
    P_Noise["<b>Inyección de Ruido Clínico:</b><br>• Red Eléctrica (60 Hz / 50 Hz)<br>• Ruido Blanco Gaussiano (σ)<br>• Spikes impulsionales de movimiento"]
  end

  subgraph Stage2 ["2. Motor de Síntesis Matemática y Fisiológica"]
    Branch_Basic["<b>Síntesis Básica (scipy.signal / numpy):</b><br>t = linspace(0, T, N)<br>y = Amplitud * Onda(2πft, duty) + Offset"]
    Branch_Bio["<b>Síntesis Biomédica (NeuroKit2):</b><br>• ECG: Modelo diferencial McSharry (ecgsyn)<br>• EMG: Ráfagas de activación y contracción<br>• EEG: Superposición bandas α, β, θ + ruido 1/f<br>• RSP / PPG: Modelos de pulso y respiración"]
    P_Type --> Branch_Basic
    P_Type --> Branch_Bio
    P_Timing --> Branch_Basic
    P_Timing --> Branch_Bio
  end

  subgraph Stage3 ["3. Módulo de Contaminación de Señal"]
    CleanSignal["Señal Limpia Sintética: y_limpia(t)"]
    Branch_Basic --> CleanSignal
    Branch_Bio --> CleanSignal

    SineNoise["+ Armónico de Red: A_red * sin(2π * f_red * t)"]
    WhiteNoise["+ Ruido Blanco: normal(0, σ, N)"]
    ImpulseNoise["+ Spikes: Máscara Bernoulli * Amplitud bipolar"]

    CleanSignal --> SineNoise
    SineNoise --> WhiteNoise
    WhiteNoise --> ImpulseNoise
    NoisySignal["Señal Contaminada Final: y_contaminada(t)"]
    ImpulseNoise --> NoisySignal
  end

  subgraph Stage4 ["4. Análisis y Previsualización Gráfica"]
    FFT_Block["<b>Análisis Espectral FFT:</b><br>Y(f) = |rfft(y)| / N<br>Espectro de densidad de 0 a 120 Hz"]
    Plot_Time["<b>Gráficas Temporales Duales:</b><br>pyqtgraph / Plotly<br>Limpia vs. Contaminada vs. Salida DAC"]
    NoisySignal --> FFT_Block
    NoisySignal --> Plot_Time
  end

  subgraph Stage5 ["5. Mapeo y Cuantización a DAC de 8 Bits"]
    Norm["<b>Normalización con Margen Anti-Clipping:</b><br>norm = (y - min_margen) / (max_margen - min_margen)"]
    Quantize["<b>Cuantización Entera Discreta (0 - 255):</b><br>dac_8bit = clip(round(norm * 255), 0, 255)"]
    VoltCalc["<b>Tensión Analógica Estimada:</b><br>V_dac = dac_8bit * (3.3 V / 255.0)"]

    NoisySignal --> Norm
    Norm --> Quantize
    Quantize --> VoltCalc
    VoltCalc --> Plot_Time
  end

  subgraph Stage6 ["6. Serialización y Transmisión por Bloques"]
    FormatFile["<b>Formateo de Archivo:</b><br>#FS, #COUNT, #FORMAT + Filas CSV o datos TXT"]
    Chunking["<b>División en Bloques:</b><br>Paquetes CHUNK de 64 muestras"]
    FlowControl["<b>Transmisión con Handshake UART:</b><br>SAVE_START -> CHUNK + ACK -> SAVE_END"]

    Quantize --> FormatFile
    FormatFile --> Chunking
    Chunking --> FlowControl
  end

  subgraph Stage7 ["7. Recepción y Generación Embebida (ESP32)"]
    FlashSave["<b>Almacenamiento No Volátil:</b><br>Archivo grabado en LittleFS SPI Flash"]
    RAMBuffer["<b>Buffer de Reproducción:</b><br>uint8_t* dacBuffer asignado en memoria RAM"]
    TimerISR["<b>Interrupción Periódica de Alta Resolución:</b><br>esp_timer dispara alarma cada Ts = 1/Fs microsegundos"]
    DACWrite["<b>Registro DAC Hardware:</b><br>dacWrite(GPIO_25, dacBuffer[idx++]) (0.0 V - 3.3 V)"]

    FlowControl -->|"Cable USB UART"| FlashSave
    FlashSave -->|"Comando PLAY"| RAMBuffer
    RAMBuffer --> TimerISR
    TimerISR --> DACWrite
  end

  subgraph Stage8 ["8. Acondicionamiento Analógico Biomédico"]
    PassiveDivider["<b>Divisor Pasivo 1000:1 (Hardware KiCad):</b><br>R1 = 10 kΩ, R2 = 10 Ω"]
    BiomedicalSignal["<b>Biopotencial Seguro Calibrado:</b><br>0.1 mV a 3.3 mV (Nivel Fisiológico)"]
    MedicalDevice["<b>Dispositivo Receptor:</b><br>Amplificador AD620 / INA128 / Electrocardiógrafo Clínico"]

    DACWrite -->|"0.0 V - 3.3 V"| PassiveDivider
    PassiveDivider -->|"0.1 mV - 3.3 mV"| BiomedicalSignal
    BiomedicalSignal --> MedicalDevice
  end
```

---

### 4. 🧩 Diagrama UML de Clases y Estructura de Código

Representa la estructura orientada a objetos de la aplicación PyQt6, los trabajadores en segundo plano (`QThread`), el driver serial y la arquitectura del firmware embebido:

```mermaid
classDiagram
  direction TB

  class MainWindow {
    -serial_client: CayetinoSerial
    -sidebar: SidebarWidget
    -tabs: QTabWidget
    -tab_basic: TabBasicWave
    -tab_adv: TabAdvancedBio
    -tab_manager: TabManager
    -tab_guide: TabGuide
    -toast_frame: QFrame
    -lbl_toast: QLabel
    +__init__()
    -_setup_ui() void
    -_connect_signals() void
    -_on_file_saved(msg: str) void
    -_on_connection_changed(connected: bool) void
    -_on_dac_pin_changed(pin: int) void
    -_on_fs_formatted() void
  }

  class SidebarWidget {
    -client: CayetinoSerial
    -connect_worker: ConnectWorker
    -format_worker: FormatFSWorker
    -chk_simulation: QCheckBox
    -cmb_ports: QComboBox
    -cmb_baud: QComboBox
    -btn_connect: QPushButton
    -btn_group_dac: QButtonGroup
    +connection_changed: pyqtSignal
    +dac_pin_changed: pyqtSignal
    +fs_formatted: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_connect_signals() void
    +refresh_ports() void
    +get_active_dac_pin() int
    -_on_sim_toggled(checked: bool) void
    -_on_connect_toggle() void
    -_on_connect_finished(success: bool, msg: str) void
    -_set_connected_state(connected: bool) void
    -_on_apply_dac() void
    -_on_format_clicked() void
    -_on_format_finished(success: bool, msg: str) void
  }

  class TabBasicWave {
    -client: CayetinoSerial
    -save_worker: SaveSignalWorker
    -current_t: ndarray
    -current_y: ndarray
    -current_dac: ndarray
    -current_volt: ndarray
    -cmb_wave: QComboBox
    -spn_freq: QDoubleSpinBox
    -sld_amp: QSlider
    -sld_offset: QSlider
    -sld_duty: QSlider
    -spn_fs: QSpinBox
    -spn_dur: QDoubleSpinBox
    -win: GraphicsLayoutWidget
    -curve_volt: PlotDataItem
    -curve_dac: PlotDataItem
    +file_saved: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_setup_plots() void
    -_connect_signals() void
    +update_signal() void
    -_on_wave_changed() void
    -_update_default_filename() void
    -_on_send_clicked() void
    -_on_save_progress(percent: int, msg: str) void
    -_on_save_finished(success: bool, msg: str) void
  }

  class TabAdvancedBio {
    -client: CayetinoSerial
    -save_worker: SaveSignalWorker
    -calc_timer: QTimer
    -current_t: ndarray
    -current_clean: ndarray
    -current_noisy: ndarray
    -current_dac: ndarray
    -current_volt: ndarray
    -cmb_bio_type: QComboBox
    -sld_hr: QSlider
    -cmb_method: QComboBox
    -spn_bursts: QSpinBox
    -spn_burst_dur: QDoubleSpinBox
    -chk_sine_noise: QCheckBox
    -chk_white_noise: QCheckBox
    -chk_impulse_noise: QCheckBox
    -win_time: GraphicsLayoutWidget
    -win_fft: GraphicsLayoutWidget
    +file_saved: pyqtSignal
    +__init__(serial_client, parent)
    -_setup_ui() void
    -_setup_plots() void
    -_connect_signals() void
    +schedule_update() void
    -_compute_and_render() void
    -_update_contextual_controls() void
    -_update_default_filename() void
    -_on_send_clicked() void
  }

  class TabManager {
    -client: CayetinoSerial
    -get_dac_pin: callable
    -poll_timer: QTimer
    -files_cache: list
    -current_status: dict
    -table: QTableWidget
    -cmb_files: QComboBox
    -btn_play: QPushButton
    -btn_stop: QPushButton
    -btn_del: QPushButton
    -btn_test_sine: QPushButton
    -status_banner: QFrame
    +status_updated: pyqtSignal
    +__init__(serial_client, get_dac_pin_func, parent)
    -_setup_ui() void
    -_connect_signals() void
    +refresh_file_list() void
    -_on_files_listed(success: bool, files: list, msg: str) void
    -_render_table(files: list) void
    -_on_play_clicked() void
    -_on_stop_clicked() void
    -_on_delete_clicked() void
    -_on_test_sine_clicked() void
    -_poll_status() void
    -_update_banner(stat: dict) void
  }

  class TabGuide {
    -browser: QTextBrowser
    +__init__(parent)
    -_setup_ui() void
  }

  class CayetinoSerial {
    +simulation_mode: bool
    +ser: Serial
    +port: str
    +baudrate: int
    +sim_files: dict
    +sim_status: dict
    +__init__(simulation_mode: bool)
    +connect(port: str, baudrate: int, timeout: float) bool
    +disconnect() void
    +is_connected() bool
    +ping() bool
    +list_files() list
    +save_file(filename: str, fs: int, dac_values: ndarray, chunk_size: int, progress_callback: callable) bool
    +play_file(filename: str) dict
    +stop_playback() bool
    +delete_file(filename: str) bool
    +format_fs() bool
    +get_status() dict
    +set_dac_pin(pin: int) bool
    +play_test_sine() dict
  }

  class SignalGeneratorModule {
    <<módulo>>
    +generate_basic_signal(signal_type, freq, fs, duration, amplitude, offset, duty_cycle) tuple
    +generate_biomedical_signal(bio_type, fs, duration, heart_rate, burst_number, burst_duration, method) tuple
    +contaminate_signal(signal, fs, white_noise_amp, sine_noise_amp, sine_noise_freq, impulse_noise_prob, impulse_noise_amp) ndarray
    +map_to_dac_8bit(signal, auto_scale, target_min_val, target_max_val, margin_percent) tuple
    +format_file_content(dac_values, fs, ext) str
  }

  class ConnectWorker {
    -client: CayetinoSerial
    -port: str
    -baudrate: int
    +finished: pyqtSignal
    +run() void
  }

  class SaveSignalWorker {
    -client: CayetinoSerial
    -filename: str
    -fs: int
    -dac_values: ndarray
    +progress: pyqtSignal
    +finished: pyqtSignal
    +run() void
  }

  class ListFilesWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class PlayFileWorker {
    -client: CayetinoSerial
    -filename: str
    +finished: pyqtSignal
    +run() void
  }

  class StopWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class DeleteFileWorker {
    -client: CayetinoSerial
    -filename: str
    +finished: pyqtSignal
    +run() void
  }

  class FormatFSWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class TestSineWorker {
    -client: CayetinoSerial
    +finished: pyqtSignal
    +run() void
  }

  class CayetinoFirmwareESP32 {
    <<firmware C++>>
    -currentDacPin: int = 25
    -isPlaying: bool = false
    -dacBuffer: uint8_t*
    -dacBufferLen: int
    -dacBufferIndex: int
    -espTimerHandle: esp_timer_handle_t
    +setup() void
    +loop() void
    +handleCommand(cmd: String) void
    +cmdList() void
    +cmdSaveStart(filename, fs, samples) void
    +cmdChunk(csvLine) void
    +cmdSaveEnd() void
    +cmdPlay(filename) void
    +cmdStop() void
    +cmdStatus() void
    +cmdDelete(filename) void
    +cmdFormat() void
    +cmdTestSine() void
    +dacTimerCallback(arg: void*) void
  }

  %% Relaciones de Composición y Agregación
  MainWindow *-- SidebarWidget
  MainWindow *-- TabBasicWave
  MainWindow *-- TabAdvancedBio
  MainWindow *-- TabManager
  MainWindow *-- TabGuide
  MainWindow o-- CayetinoSerial

  SidebarWidget ..> ConnectWorker : crea
  SidebarWidget ..> FormatFSWorker : crea
  SidebarWidget o-- CayetinoSerial

  TabBasicWave ..> SaveSignalWorker : crea
  TabBasicWave ..> SignalGeneratorModule : usa
  TabBasicWave o-- CayetinoSerial

  TabAdvancedBio ..> SaveSignalWorker : crea
  TabAdvancedBio ..> SignalGeneratorModule : usa
  TabAdvancedBio o-- CayetinoSerial

  TabManager ..> ListFilesWorker : crea
  TabManager ..> PlayFileWorker : crea
  TabManager ..> StopWorker : crea
  TabManager ..> DeleteFileWorker : crea
  TabManager ..> TestSineWorker : crea
  TabManager o-- CayetinoSerial

  %% Relaciones de llamada de Workers a Driver
  ConnectWorker --> CayetinoSerial : invoca
  SaveSignalWorker --> CayetinoSerial : invoca
  ListFilesWorker --> CayetinoSerial : invoca
  PlayFileWorker --> CayetinoSerial : invoca
  StopWorker --> CayetinoSerial : invoca
  DeleteFileWorker --> CayetinoSerial : invoca
  FormatFSWorker --> CayetinoSerial : invoca
  TestSineWorker --> CayetinoSerial : invoca

  %% Interacción física Driver con Firmware
  CayetinoSerial ..> CayetinoFirmwareESP32 : "Protocolo UART bidireccional (115200 bps)"
```
