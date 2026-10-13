/*
 ============================================================================
  PROYECTO CAYETINO - FIRMWARE ESP32
  Generador de Señales Analógicas Biomédicas y Sintéticas vía DAC y LittleFS
 ============================================================================
  
  Dispositivo para generar señales biomédicas (EKG, EMG, EEG, etc.) y ondas
  básicas (seno, triangular, cuadrada, rampa) para el entrenamiento de 
  estudiantes de Ingeniería Biomédica.
  
  Características:
   - Almacenamiento no volátil en memoria Flash usando LittleFS.
   - Generación continua analógica mediante DAC interno de 8 bits (GPIO 25 / GPIO 26).
   - Temporizador de ultra alta precisión por hardware (esp_timer, 64-bit microsegundos).
   - Protocolo Serial robusto con control de flujo por bloques (ACK) y gestión de archivos.
   - Parser universal tolerante a fallos para lectura completa de muestras.
   - Modo de autodiagnóstico de hardware integrado (TEST_SINE).
 ============================================================================
*/

#include <Arduino.h>
#include <FS.h>
#include <LittleFS.h>
#include <esp_timer.h>

// Definición de pines DAC del ESP32
#define DEFAULT_DAC_PIN 25  // DAC1 = GPIO 25 (opcional DAC2 = GPIO 26)
#define STATUS_LED_PIN   2  // LED indicador integrado (GPIO 2 en DevKit)

// Variables globales de reproducción
static int currentDacPin = DEFAULT_DAC_PIN;
static uint8_t* dacBuffer = nullptr;
static size_t dacBufferSize = 0;
static volatile size_t dacPlaybackIndex = 0;
static volatile bool isPlaying = false;
static esp_timer_handle_t dacTimerHandle = NULL;

static uint32_t currentSampleRate = 250;
static String currentFileName = "";

// Variables para recepción de archivos
static File saveFile;
static bool isSaving = false;
static String savingFileName = "";
static uint32_t savingFs = 250;
static size_t savingTotalSamples = 0;
static size_t savingReceivedSamples = 0;

// ============================================================================
// RUTINA DE INTERRUPCIÓN DEL TEMPORIZADOR DAC (IRAM)
// ============================================================================
void IRAM_ATTR onDacTimerCallback(void* arg) {
    if (isPlaying && dacBuffer != nullptr && dacBufferSize > 0) {
        dacWrite(currentDacPin, dacBuffer[dacPlaybackIndex]);
        dacPlaybackIndex++;
        if (dacPlaybackIndex >= dacBufferSize) {
            dacPlaybackIndex = 0; // Bucle continuo ininterrumpido
        }
    }
}

// ============================================================================
// FUNCIONES DE CONTROL DE REPRODUCCIÓN DAC
// ============================================================================
void stopPlayback() {
    isPlaying = false;
    if (dacTimerHandle != NULL) {
        esp_timer_stop(dacTimerHandle);
        esp_timer_delete(dacTimerHandle);
        dacTimerHandle = NULL;
    }
    // Nivel neutro de reposo (~1.65V)
    dacWrite(currentDacPin, 128);
    digitalWrite(STATUS_LED_PIN, LOW);
}

bool startPlayback(uint32_t fsHz) {
    stopPlayback();
    
    if (dacBuffer == nullptr || dacBufferSize == 0) {
        return false;
    }
    
    currentSampleRate = fsHz;
    dacPlaybackIndex = 0;
    
    esp_timer_create_args_t timerArgs = {
        .callback = &onDacTimerCallback,
        .arg = NULL,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "cayetino_dac_timer"
    };
    
    esp_err_t err = esp_timer_create(&timerArgs, &dacTimerHandle);
    if (err != ESP_OK) {
        return false;
    }
    
    // Período de muestreo en microsegundos = 1,000,000 / Fs
    uint64_t periodUs = 1000000ULL / currentSampleRate;
    if (periodUs < 10) periodUs = 10; // Máximo ~100 kHz
    
    err = esp_timer_start_periodic(dacTimerHandle, periodUs);
    if (err != ESP_OK) {
        esp_timer_delete(dacTimerHandle);
        dacTimerHandle = NULL;
        return false;
    }
    
    isPlaying = true;
    digitalWrite(STATUS_LED_PIN, HIGH);
    return true;
}

void generateTestSine() {
    stopPlayback();
    dacBufferSize = 100;
    uint8_t* newBuf = (uint8_t*)realloc(dacBuffer, 100);
    if (newBuf != nullptr) {
        dacBuffer = newBuf;
        for (int i = 0; i < 100; i++) {
            float rad = (2.0f * PI * (float)i) / 100.0f;
            float val = 127.5f + 127.5f * sin(rad);
            dacBuffer[i] = (uint8_t)constrain((int)round(val), 0, 255);
        }
        currentFileName = "TEST_SENO_5HZ";
        startPlayback(500); // 100 muestras @ 500 Hz = 5 Hz señal continua
        Serial.printf("OK_TEST_SINE:%u:%u\n", 500, dacBufferSize);
    } else {
        Serial.println("ERR_TEST:NO_MEM");
    }
}

// ============================================================================
// GESTIÓN DE LITTLEFS (LISTAR, CARGAR, GUARDAR)
// ============================================================================
String normalizePath(const String& name) {
    String p = name;
    p.trim();
    if (!p.startsWith("/")) {
        p = "/" + p;
    }
    return p;
}

void listFiles() {
    Serial.println("FILES_START");
    File root = LittleFS.open("/");
    if (root && root.isDirectory()) {
        File file = root.openNextFile();
        while (file) {
            if (!file.isDirectory()) {
                String fname = file.name();
                size_t fsize = file.size();
                
                // Inspeccionar metadatos en cabecera
                uint32_t fFs = 250;
                uint32_t fCount = 0;
                
                int linesRead = 0;
                while (file.available() && linesRead < 6) {
                    String line = file.readStringUntil('\n');
                    line.trim();
                    if (line.startsWith("# FS:") || line.startsWith("#FS:")) {
                        int idx = line.indexOf(':');
                        if (idx != -1) fFs = line.substring(idx + 1).toInt();
                    } else if (line.startsWith("# COUNT:") || line.startsWith("#COUNT:")) {
                        int idx = line.indexOf(':');
                        if (idx != -1) fCount = line.substring(idx + 1).toInt();
                    } else if (line.startsWith("index,dac_val") || line.startsWith("# DATA")) {
                        break;
                    }
                    linesRead++;
                }
                
                if (fCount == 0 && fsize > 0) {
                    fCount = fsize / 4;
                }
                
                Serial.printf("FILE:%s:%u:%u:%u\n", fname.c_str(), fFs, fCount, fsize);
            }
            file = root.openNextFile();
        }
    }
    Serial.println("FILES_END");
}

bool loadAndPlayFile(const String& filename) {
    String path = normalizePath(filename);
    if (!LittleFS.exists(path)) {
        Serial.printf("ERR_PLAY:FILE_NOT_FOUND:%s\n", path.c_str());
        return false;
    }
    
    File f = LittleFS.open(path, "r");
    if (!f) {
        Serial.printf("ERR_PLAY:OPEN_FAILED:%s\n", path.c_str());
        return false;
    }
    
    stopPlayback();
    
    uint32_t fileFs = 250;
    size_t fileCount = 0;
    bool isCsvFormat = false;
    
    // 1. Leer encabezados
    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.startsWith("# FS:") || line.startsWith("#FS:")) {
            int idx = line.indexOf(':');
            if (idx != -1) fileFs = line.substring(idx + 1).toInt();
        } else if (line.startsWith("# COUNT:") || line.startsWith("#COUNT:")) {
            int idx = line.indexOf(':');
            if (idx != -1) fileCount = line.substring(idx + 1).toInt();
        } else if (line.startsWith("index,dac_val")) {
            isCsvFormat = true;
            break;
        } else if (line.startsWith("# DATA")) {
            break;
        } else if (!line.startsWith("#") && line.length() > 0) {
            // Datos directos sin cabecera # DATA
            f.seek(f.position() - line.length() - 1);
            break;
        }
    }
    
    if (fileCount == 0) {
        fileCount = 2000;
    }
    
    // Reservar buffer en RAM con margen
    uint8_t* newBuf = (uint8_t*)realloc(dacBuffer, fileCount + 500);
    if (newBuf == nullptr) {
        f.close();
        Serial.println("ERR_PLAY:OUT_OF_MEMORY");
        return false;
    }
    dacBuffer = newBuf;
    
    size_t loadedCount = 0;
    
    if (isCsvFormat) {
        // Formato CSV por filas: "index,dac_val,voltage"
        while (f.available() && loadedCount < 50000) {
            String line = f.readStringUntil('\n');
            line.trim();
            if (line.length() == 0 || line.startsWith("#")) continue;
            
            int idx1 = line.indexOf(',');
            if (idx1 != -1) {
                int idx2 = line.indexOf(',', idx1 + 1);
                String valStr = (idx2 != -1) ? line.substring(idx1 + 1, idx2) : line.substring(idx1 + 1);
                valStr.trim();
                int num = valStr.toInt();
                if (num >= 0 && num <= 255) {
                    if (loadedCount >= fileCount) {
                        fileCount += 1000;
                        dacBuffer = (uint8_t*)realloc(dacBuffer, fileCount + 500);
                    }
                    dacBuffer[loadedCount++] = (uint8_t)num;
                }
            }
        }
    } else {
        // Formato universal de muestras separadas por coma, espacios o saltos de línea
        String numStr = "";
        numStr.reserve(8);
        while (f.available() && loadedCount < 50000) {
            char c = (char)f.read();
            if (isDigit(c)) {
                numStr += c;
            } else if (c == ',' || c == '\n' || c == '\r' || c == ' ' || c == '\t') {
                if (numStr.length() > 0) {
                    int val = numStr.toInt();
                    if (val >= 0 && val <= 255) {
                        if (loadedCount >= fileCount) {
                            fileCount += 1000;
                            dacBuffer = (uint8_t*)realloc(dacBuffer, fileCount + 500);
                        }
                        dacBuffer[loadedCount++] = (uint8_t)val;
                    }
                    numStr = "";
                }
            }
        }
        if (numStr.length() > 0 && loadedCount < 50000) {
            int val = numStr.toInt();
            if (val >= 0 && val <= 255) {
                if (loadedCount >= fileCount) {
                    fileCount += 1000;
                    dacBuffer = (uint8_t*)realloc(dacBuffer, fileCount + 500);
                }
                dacBuffer[loadedCount++] = (uint8_t)val;
            }
        }
    }
    
    f.close();
    
    if (loadedCount == 0) {
        Serial.println("ERR_PLAY:NO_SAMPLES_PARSED");
        return false;
    }
    
    dacBufferSize = loadedCount;
    currentFileName = path;
    
    if (startPlayback(fileFs)) {
        Serial.printf("OK_PLAY:%s:%u:%u\n", path.c_str(), currentSampleRate, dacBufferSize);
        return true;
    } else {
        Serial.println("ERR_PLAY:TIMER_FAILED");
        return false;
    }
}

// ============================================================================
// PROCESADOR DE COMANDOS SERIALES
// ============================================================================
void processCommand(const String& cmdLine) {
    String cmd = cmdLine;
    cmd.trim();
    if (cmd.length() == 0) return;
    
    if (cmd == "PING") {
        Serial.println("PONG:CAYETINO_ESP32_OK");
    }
    else if (cmd == "STATUS") {
        if (isPlaying) {
            Serial.printf("STATUS:PLAYING:%s:%u:%u\n", currentFileName.c_str(), currentSampleRate, dacBufferSize);
        } else {
            Serial.println("STATUS:IDLE");
        }
    }
    else if (cmd == "STOP") {
        stopPlayback();
        Serial.println("OK_STOP");
    }
    else if (cmd == "TEST_SINE") {
        generateTestSine();
    }
    else if (cmd == "LIST") {
        listFiles();
    }
    else if (cmd.startsWith("PLAY:")) {
        String fname = cmd.substring(5);
        loadAndPlayFile(fname);
    }
    else if (cmd.startsWith("SAVE_START:")) {
        // Formato: SAVE_START:<filename>:<fs>:<samples>
        int idx1 = cmd.indexOf(':', 11);
        int idx2 = (idx1 != -1) ? cmd.indexOf(':', idx1 + 1) : -1;
        
        if (idx1 != -1 && idx2 != -1) {
            savingFileName = normalizePath(cmd.substring(11, idx1));
            savingFs = cmd.substring(idx1 + 1, idx2).toInt();
            savingTotalSamples = cmd.substring(idx2 + 1).toInt();
            savingReceivedSamples = 0;
            
            stopPlayback();
            
            saveFile = LittleFS.open(savingFileName, "w");
            if (saveFile) {
                isSaving = true;
                saveFile.printf("# CAYETINO SIGNAL FILE\n");
                saveFile.printf("# FS:%u\n", savingFs);
                saveFile.printf("# COUNT:%u\n", savingTotalSamples);
                saveFile.printf("# DATA\n");
                Serial.println("READY_CHUNKS");
            } else {
                Serial.println("ERR_SAVE:FILE_CREATE_FAILED");
            }
        } else {
            Serial.println("ERR_SAVE:BAD_FORMAT");
        }
    }
    else if (cmd.startsWith("CHUNK:")) {
        if (!isSaving || !saveFile) {
            Serial.println("ERR_CHUNK:NOT_SAVING");
            return;
        }
        String data = cmd.substring(6);
        saveFile.print(data);
        saveFile.print(",");
        
        int cCount = 1;
        for (int i = 0; i < data.length(); i++) {
            if (data.charAt(i) == ',') cCount++;
        }
        savingReceivedSamples += cCount;
        Serial.println("ACK_CHUNK");
    }
    else if (cmd == "SAVE_END") {
        if (isSaving && saveFile) {
            saveFile.println();
            saveFile.flush();
            saveFile.close();
            isSaving = false;
            Serial.printf("OK_SAVE:%s:%u\n", savingFileName.c_str(), savingReceivedSamples);
        } else {
            Serial.println("ERR_SAVE:NOT_ACTIVE");
        }
    }
    else if (cmd.startsWith("DELETE:")) {
        String fname = normalizePath(cmd.substring(7));
        if (isPlaying && currentFileName == fname) {
            stopPlayback();
        }
        if (LittleFS.exists(fname)) {
            LittleFS.remove(fname);
            Serial.printf("OK_DELETE:%s\n", fname.c_str());
        } else {
            Serial.printf("ERR_DELETE:NOT_FOUND:%s\n", fname.c_str());
        }
    }
    else if (cmd == "FORMAT") {
        stopPlayback();
        LittleFS.format();
        Serial.println("OK_FORMAT");
    }
    else if (cmd.startsWith("SET_DAC_PIN:")) {
        int pin = cmd.substring(12).toInt();
        if (pin == 25 || pin == 26) {
            currentDacPin = pin;
            dacWrite(currentDacPin, 128);
            Serial.printf("OK_DAC_PIN:%d\n", pin);
        } else {
            Serial.println("ERR_DAC_PIN:ONLY_25_OR_26");
        }
    }
    else {
        Serial.printf("ERR_UNKNOWN_CMD:%s\n", cmd.c_str());
    }
}

// ============================================================================
// CONFIGURACIÓN INICIAL (SETUP)
// ============================================================================
void setup() {
    Serial.begin(115200);
    delay(500);
    
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);
    
    // Iniciar DAC en reposo (128 = ~1.65V)
    dacWrite(currentDacPin, 128);
    
    // Iniciar LittleFS
    if (!LittleFS.begin(true)) {
        Serial.println("CAYETINO_BOOT:LITTLEFS_ERROR");
    } else {
        Serial.println("CAYETINO_BOOT:OK");
    }
}

// ============================================================================
// BUCLE PRINCIPAL (LOOP)
// ============================================================================
void loop() {
    if (Serial.available()) {
        String cmdLine = Serial.readStringUntil('\n');
        processCommand(cmdLine);
    }
    
    // Parpadeo del LED durante reproducción
    static unsigned long lastBlink = 0;
    if (isPlaying && (millis() - lastBlink > 300)) {
        lastBlink = millis();
        digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    }
}
