# Firmware Cayetino ESP32

Este firmware para Arduino permite al ESP32 actuar como un generador de señales analógicas de alta fidelidad para prácticas de Ingeniería Biomédica.

## Características
1. **DAC Interno de 8 bits**:
   - Salida analógica por **GPIO 25** (DAC1) o **GPIO 26** (DAC2).
   - Rango de tensión de salida: `0.0 V` a `3.3 V` (256 niveles de cuantización).
2. **Sistema de Archivos Flash LittleFS**:
   - Almacena señales biomédicas y ondas sintéticas transferidas desde Streamlit.
   - Persistencia de datos al reiniciar la placa.
3. **Temporizador por Hardware `esp_timer` (64 bits)**:
   - Permite frecuencias de muestreo desde 10 Hz hasta 20 kHz con jitter despreciable.
   - Ejecución sin bloqueos del procesador, operando en bucle continuo de la ventana guardada.
4. **Protocolo Serial de Alta Fiabilidad**:
   - Velocidad: `115200 baudios`.
   - Control de flujo por bloques (`CHUNK` + `ACK_CHUNK`) para evitar pérdida de datos o desbordamiento de buffer serial.

## Instrucciones de Compilación y Carga

### Opción 1: Mediante Arduino IDE
1. Abre Arduino IDE y ve a **Archivo -> Abrir...**.
2. Selecciona el archivo `cayetino_esp32.ino`.
3. En **Herramientas -> Placa -> esp32**, selecciona **ESP32 Dev Module** (o la placa ESP32 correspondiente).
4. En **Herramientas -> Puerto**, selecciona el puerto COM de tu ESP32 (por ejemplo, `COM7`).
5. En **Herramientas -> Flash Size**, asegúrate de tener al menos **4MB** y esquema de partición con soporte SPIFFS/LittleFS (por ejemplo, *Default 4MB with spiffs*).
6. Presiona el botón **Subir** (si tu placa no entra en modo bootloader automáticamente, mantén presionado el botón **BOOT** mientras compila hasta que empiece a escribir la memoria flash).

### Opción 2: Mediante arduino-cli
Ejecuta en la consola:
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 ./firmware_esp32/cayetino_esp32
arduino-cli upload -p COM7 --fqbn esp32:esp32:esp32 ./firmware_esp32/cayetino_esp32
```

## Circuito de Conexión Recomendado
- **Osciloscopio / Adquisición Directa**:
  - `GPIO 25` -> Canal 1 (+)
  - `GND` -> Referencia Tierra (-)
- **Amplificador Biomédico (AD620 / INA128)**:
  - Ver diagrama en pestaña *Hardware & Guía Biomédica* de la app Streamlit con divisor resistivo para atenuar a milivoltios ($1 - 3\text{ mV}$).
