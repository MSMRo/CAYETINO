// Definimos el pin ADC 0 de la Raspberry Pi Pico (GP26)
const int analogInPin = 27; // También puedes usar A0 si tienes el core de Philhower instalado

void setup() {
  // Iniciamos la comunicación serial para el Serial Plotter
  Serial.begin(115200);
  
  // (Opcional) Configuramos la resolución del ADC a 12 bits (0 a 4095)
  // que es la capacidad nativa del hardware de la Raspberry Pi Pico
  analogReadResolution(12); 
}

void loop() {
  // Leemos el valor que llega desde el DAC del ESP32
  int sensorValue = analogRead(analogInPin);
  
  // Enviamos el dato al Serial Plotter
  Serial.print("4095,");
  Serial.print(sensorValue);
  Serial.println(",0");
  
  // Retardo de 10ms para estabilizar la gráfica
  delay(20);
}