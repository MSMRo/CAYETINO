"""
=============================================================================
PROYECTO CAYETINO - GUÍA DE HARDWARE Y PROTOCOLO BIOMÉDICO (tab_guide.py)
Documentación de conexión, atenuación pasiva y tabla de comandos seriales
=============================================================================
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser


class TabGuide(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 16px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)

        html_content = """
        <html>
        <head>
        <style>
            body { font-family: 'Segoe UI', sans-serif; color: #1E293B; }
            h2 { color: #1E3A8A; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; }
            h3 { color: #2563EB; margin-top: 18px; margin-bottom: 6px; }
            .info-box {
                background-color: #EFF6FF;
                border-left: 5px solid #3B82F6;
                padding: 12px 16px;
                border-radius: 6px;
                margin: 12px 0;
            }
            .schematic-box {
                background-color: #0F172A;
                color: #38BDF8;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 14px;
                border-radius: 6px;
                font-size: 13px;
                white-space: pre;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 14px 0;
            }
            th {
                background-color: #F8FAFC;
                color: #1E3A8A;
                border: 1px solid #CBD5E1;
                padding: 8px 10px;
                text-align: left;
            }
            td {
                border: 1px solid #E2E8F0;
                padding: 8px 10px;
                font-size: 12.5px;
            }
            tr:nth-child(even) { background-color: #F8FAFC; }
            code {
                background-color: #F1F5F9;
                color: #D946EF;
                padding: 2px 5px;
                border-radius: 4px;
                font-family: Consolas, monospace;
            }
            .formula {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                font-size: 15px;
                color: #1E3A8A;
                margin: 10px 0;
            }
        </style>
        </head>
        <body>
            <h2>🔌 Conexión de Hardware y Circuito Atenuador Biomédico</h2>
            <p>Aprende a conectar el ESP32 a amplificadores de biopotenciales y osciloscopios de forma segura.</p>

            <h3>1. Salida Directa del DAC del ESP32</h3>
            <ul>
                <li><b>Resolución</b>: 8 bits (256 niveles discretos: de 0 a 255).</li>
                <li><b>Tensión de salida analógica</b>: 0.0 V a 3.3 V.</li>
                <li><b>Pines DAC integrados en chip ESP32</b>:
                    <ul>
                        <li><b>DAC 1</b>: <code>GPIO 25</code> (salida predeterminada)</li>
                        <li><b>DAC 2</b>: <code>GPIO 26</code></li>
                        <li><b>Referencia común de masa</b>: <code>GND</code></li>
                    </ul>
                </li>
                <li>Para conectar a un osciloscopio o entrada ADC, se conecta la sonda positiva al pin <code>GPIO 25</code> y la pinza de tierra al pin <code>GND</code>.</li>
            </ul>

            <div class="info-box">
                <b>💡 ¿Por qué atenuar para equipos biomédicos?</b><br>
                Las señales fisiológicas reales captadas sobre la piel humana tienen amplitudes en el orden de los milivoltios o microvoltios:
                <ul>
                    <li><b>EKG / ECG</b>: 1 mV a 3 mV</li>
                    <li><b>EMG</b>: 0.1 mV a 5 mV</li>
                    <li><b>EEG</b>: 10 µV a 100 µV</li>
                </ul>
                Dado que el DAC del ESP32 emite hasta <b>3.3 V</b>, si se conecta directamente a un amplificador de biopotenciales de instrumentación (como un AD620 o INA128 con ganancia G = 1000), la salida se saturaría de inmediato en el riel de alimentación. Se requiere un <b>divisor resistivo pasivo atenuador</b>.
            </div>

            <h3>2. Diagrama Esquemático del Divisor Resistivo Pasivo</h3>
            <div class="schematic-box">
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
ESP32 GND ─────────────────> Salida de Referencia (-) GND</div>

            <h3>3. Relación Matemática de Atenuación</h3>
            <div class="formula">
                V<sub>out</sub> = V<sub>DAC</sub> × [ R<sub>2</sub> / (R<sub>1</sub> + R<sub>2</sub>) ]
            </div>
            <p>Con <b>R<sub>1</sub> = 10 kΩ (10,000 Ω)</b> y <b>R<sub>2</sub> = 10 Ω</b>:</p>
            <div class="formula">
                V<sub>out</sub> ≈ 3.3 V × [ 10 / (10,000 + 10) ] ≈ 3.29 mV ≈ 3.3 mV
            </div>
            <p><i>¡Esto convierte a la placa ESP32 en un simulador de paciente perfecto para calibrar y evaluar filtros analógicos y etapas de ganancia en ingeniería clínica!</i></p>

            <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 20px 0;">

            <h3>📋 Protocolo Serial Cayetino (Firmware ESP32)</h3>
            <p>Especificación de comandos UART (Baudrate predeterminado: 115200 bps):</p>
            <table>
                <tr>
                    <th>Comando Serial</th>
                    <th>Parámetros</th>
                    <th>Respuesta ESP32</th>
                    <th>Descripción</th>
                </tr>
                <tr>
                    <td><code>PING</code></td>
                    <td>Ninguno</td>
                    <td><code>PONG:CAYETINO_ESP32_OK</code></td>
                    <td>Prueba de vida y confirmación de firmware instalado.</td>
                </tr>
                <tr>
                    <td><code>LIST</code></td>
                    <td>Ninguno</td>
                    <td><code>FILES_START ... FILES_END</code></td>
                    <td>Lista todos los archivos grabados con metadatos en LittleFS.</td>
                </tr>
                <tr>
                    <td><code>SAVE_START:&lt;name&gt;:&lt;fs&gt;:&lt;n&gt;</code></td>
                    <td>Nombre, Fs, N° muestras</td>
                    <td><code>READY_CHUNKS</code></td>
                    <td>Prepara el archivo en memoria Flash para escritura.</td>
                </tr>
                <tr>
                    <td><code>CHUNK:&lt;v1,v2,...&gt;</code></td>
                    <td>Muestras 8-bit (CSV)</td>
                    <td><code>ACK_CHUNK</code></td>
                    <td>Escribe bloque con control de flujo por confirmación.</td>
                </tr>
                <tr>
                    <td><code>SAVE_END</code></td>
                    <td>Ninguno</td>
                    <td><code>OK_SAVE:&lt;name&gt;:&lt;n&gt;</code></td>
                    <td>Cierra y consolida el archivo en LittleFS.</td>
                </tr>
                <tr>
                    <td><code>PLAY:&lt;name&gt;</code></td>
                    <td>Nombre de archivo</td>
                    <td><code>OK_PLAY:&lt;name&gt;:&lt;fs&gt;:&lt;n&gt;</code></td>
                    <td>Carga el archivo a RAM e inicia el temporizador DAC.</td>
                </tr>
                <tr>
                    <td><code>STOP</code></td>
                    <td>Ninguno</td>
                    <td><code>OK_STOP</code></td>
                    <td>Detiene la emisión y deja el DAC en nivel neutro.</td>
                </tr>
                <tr>
                    <td><code>STATUS</code></td>
                    <td>Ninguno</td>
                    <td><code>STATUS:PLAYING:...</code> / <code>IDLE</code></td>
                    <td>Consulta si el hardware DAC está emitiendo señal.</td>
                </tr>
                <tr>
                    <td><code>DELETE:&lt;name&gt;</code></td>
                    <td>Nombre de archivo</td>
                    <td><code>OK_DELETE:&lt;name&gt;</code></td>
                    <td>Elimina el archivo especificado de LittleFS.</td>
                </tr>
                <tr>
                    <td><code>FORMAT</code></td>
                    <td>Ninguno</td>
                    <td><code>OK_FORMAT</code></td>
                    <td>Formatea por completo el sistema de archivos Flash.</td>
                </tr>
                <tr>
                    <td><code>SET_DAC_PIN:&lt;pin&gt;</code></td>
                    <td>25 o 26</td>
                    <td>Ninguno</td>
                    <td>Selecciona el canal analógico activo (DAC1 o DAC2).</td>
                </tr>
                <tr>
                    <td><code>TEST_SINE</code></td>
                    <td>Ninguno</td>
                    <td><code>OK_TEST_SINE:500:100</code></td>
                    <td>Emite onda senoidal pura de 5 Hz calculada en RAM.</td>
                </tr>
            </table>
        </body>
        </html>
        """

        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)
