#include "src/FreeRTOS/Arduino_FreeRTOS.h"

// Commands
/*
  string -> "ABC"
  A: D -> digital
     A -> analógico
     T -> período de refrescado (delay loop)
          A     D     T
  B: A -> A0    D0    10ms
     B -> A1    D1    50ms
     C -> A2    D2    100ms
     D -> A3    D3    200ms
     E -> A4    D4    300ms
     F -> A5    D5    400ms
     G -> A6    D6    500ms
     H -> A7    D7    600ms
     I -> ---   D8    700ms
     J -> ---   D9    800ms
     K -> ---   D10   900ms
     L -> ---   D11   1000ms
     M -> ---   D12   1200ms
     N -> ---   D13   1500ms
     O -> ---   ---   1700ms
     P -> ---   ---   2000ms
     Q -> ---   ---   3000ms
     R -> ---   ---   4000ms
     S -> ---   ---   5000ms
     T -> ---   ---   7000ms
     U -> ---   ---   10000ms
     V -> ---   ---   15000ms
     W -> ---   ---   20000ms
     X -> ---   ---   30000ms
     Y -> ---   ---   60000ms
     Z -> ---   ---   120000ms

     Digital:
  C: 0 -> poner en bajo
     1 -> poner en alto
     3 -> configurar como entrada
     4 -> configurar como salida
     5 -> poner en estado bajo con confirmación
     6 -> poner en estado alto con confirmación
     Analógico:
     0 -> desactivar lectura del analógico
     1 -> activar lectura del analógico
*/
// JSON
int const SIZE_STROUT = 200;


char strout[] = "{\"A0\":%d,\
\"A1\":%d,\
\"A2\":%d,\
\"A3\":%d,\
\"A4\":%d,\
\"A5\":%d,\
\"A6\":%d,\
\"A7\":%d,\
\"D2\":%d,\
\"D3\":%d,\
\"D4\":%d,\
\"D5\":%d,\
\"D6\":%d,\
\"D7\":%d,\
\"D8\":%d,\
\"D9\":%d,\
\"D10\":%d,\
\"D11\":%d,\
\"D12\":%d,\
\"D13\":%d}";
char strout_s[SIZE_STROUT] = "";

/*  ARDUINO STATUS  */
uint8_t vD[14] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};   // valor del pin digital
int vA[8] = {0, 0, 0, 0, 0, 0, 0, 0};  // valor del conversor analógico
uint8_t vA_active[8] = {0, 0, 0, 0, 0, 0, 0, 0};  // ADC activos
uint8_t const N_vA_POINT = 10;  // número de mediciones de los conversores a promediar
int vA_point[8][N_vA_POINT];  // mediciones de los conversores

bool status_changed = false;  // True si ha cambiado el valor del estado del arduino
bool status_force_send = false;  // Forzar enviar el estado del Arduino por puerto serie

uint8_t confirm_cycles[14] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};  // ciclos restantes de confirmación por pin digital
uint8_t confirm_cycles_max = 15;  // Máximo número de ciclos de confirmación
int pin;
unsigned long delay_loop = 1000;  // Tiempo de retardo del loopRefresh.

/*TASK MEMORY CONFIGURATION*/
#define STACK_SIZE_SEND_STATUS 100
StaticTask_t xTaskBufferSendStatus;
StackType_t xStackSendStatus[ STACK_SIZE_SEND_STATUS ];

#define STACK_SIZE_LOOP_REFRESH 40
StaticTask_t xTaskBufferLoopRefresh;
StackType_t xStackLoopRefresh[ STACK_SIZE_LOOP_REFRESH ];

#define STACK_SIZE_UPDATE_DIGITAL 40
StaticTask_t xTaskBufferUpdateDigital;
StackType_t xStackUpdateDigital[ STACK_SIZE_UPDATE_DIGITAL ];

#define STACK_SIZE_UPDATE_ANALOGIC 56
StaticTask_t xTaskBufferUpdateAnalogic;
StackType_t xStackUpdateAnalogic[ STACK_SIZE_UPDATE_ANALOGIC ];

#define STACK_SIZE_CHECK_SERIAL 56
StaticTask_t xTaskBufferCheckSerial;
StackType_t xStackCheckSerial[ STACK_SIZE_CHECK_SERIAL ];


void setup() {

  Serial.begin(9600);  // Configuración del puerto serie
  analogReference(INTERNAL);  // 1.1 volt

  // Create task that publish data in the queue if it was created.
  xTaskCreateStatic(updateDigitalPort, // Task function
              "UpdateDigital", // Task name
              STACK_SIZE_UPDATE_DIGITAL,  // Stack size
              NULL, 
              1, // Priority
              xStackUpdateDigital,
              &xTaskBufferUpdateDigital);
  xTaskCreateStatic(updateAnalogicPort, // Task function
              "UpdateAnalogic", // Task name
              STACK_SIZE_UPDATE_ANALOGIC,  // Stack size
              NULL, 
              1, // Priority
              xStackUpdateAnalogic,
              &xTaskBufferUpdateAnalogic);
  xTaskCreateStatic(loopRefresh, // Task function
              "LoopRefresh", // Task name
              STACK_SIZE_LOOP_REFRESH,  // Stack size
              NULL, 
              1, // Priority
              xStackLoopRefresh,
              &xTaskBufferLoopRefresh);
  xTaskCreateStatic(sendStatus, // Task function
              "SendStatus", // Task name
              STACK_SIZE_SEND_STATUS,  // Stack size
              NULL, 
              1, // Priority
              xStackSendStatus,
              &xTaskBufferSendStatus);
  xTaskCreateStatic(checkSerial, // Task function
              "CheckSerial", // Task name
              STACK_SIZE_CHECK_SERIAL,  // Stack size
              NULL, 
              1, // Priority
              xStackCheckSerial,
              &xTaskBufferCheckSerial);
}

void loop() {}

void updateDigitalPort(void *pvParameters) {
  /*
  * Leer todos los puertos digitales y si se han modificados notificar
  * para que sean enviado por puerto serie.
  */
  int pin;
  for (;;) {
    for (uint8_t i = 2; i < 14; i++){
      pin = digitalRead(i);
      if (vD[i] != pin){
        vD[i] = pin;
        status_changed = true;
      }
    }
    vTaskDelay(1);
  }
}

void updateAnalogicPort(void *pvParameters) {
  /*
  * Leer constantemente los puertos analógicos marcados como activos.
  */
  for (uint8_t i_port = 0; i_port < 8; i_port++){
    for (uint8_t i_point = 0; i_point < N_vA_POINT; i_point++){
      vA_point[i_port][i_point] = analogRead(A0 + i_port);
    }
  }
  uint8_t i_buff = 0;
  int sum = 0;
  for (;;) {
    i_buff ++;
    if (i_buff == N_vA_POINT)
      i_buff = 0;
    int sum = 0;
    int average;
    for (uint8_t i = 0; i < 8; i++){
      if (!vA_active[i]){
        vA[i] = -1;
        continue;
      }
      vA_point[i][i_buff] = analogRead(A0 + i);
      // average of analogic port i
      for (uint8_t i_ave = 0; i_ave < N_vA_POINT; i_ave ++)
        sum += vA_point[i][i_ave];
      vA[i] = sum / N_vA_POINT;
    }
    vTaskDelay(10);
  }
}

void loopRefresh(void *pvParameters) {
  /*
  * Ejecutar algunos procedimientos periódicamente:
  * - Forzar el envío del estado de los puertos del Arduino
  * - Refrescar la rutina de verificación de los pines digitales
  *   que necesitan confirmación para mantener su estado.
  *
  * NOTA: El período que se ejecuta el refrescado es configurable
  * a por comandos por puerto serie.
  */
  for (;;) {
    // Forzar el envío del estado del Arduino.
    if (!status_force_send){
      status_force_send = true;
    }
    // Verificar los pines con confirmación
    for (int i = 2; i < 14; i++){
      if (confirm_cycles[i]){
        confirm_cycles[i]--;
        if (confirm_cycles[i])
          continue;
        // Invertir estado del pin
        if (digitalRead(i))
          digitalWrite(i, LOW);
        else
          digitalWrite(i, HIGH);
      }
    }
    vTaskDelay( delay_loop / portTICK_PERIOD_MS );
  }
}

void sendStatus(void *pvParameters) {
  /*
  * Enviar por puerto serie el estado de los puertos del Arduino
  * Se envía periódicamente marcado por la función loopRefresh o cuando un puerto digital cambia su estado.
  */
  for (;;)
  {
    while (!status_changed && !status_force_send) {
      vTaskDelay(3);
    }
    sprintf(strout_s, strout, vA[0], vA[1], vA[2], vA[3], vA[4], vA[5], vA[6], vA[7], vD[2], vD[3], vD[4], vD[5], vD[6], vD[7], vD[8], vD[9], vD[10], vD[11], vD[12], vD[13]);
    Serial.println(strout_s);
    status_changed = false;
    status_force_send = false;
  }
}

void checkSerial(void *pvParameters) {
  /*
  * Chequear el puerto serie.
  * Capturar el comando y ejecutar el comando.
  */
  char incomingString[5];
  for (;;) {
    //Capturar los 4 caracteres de comando por el puerto serie
    for ( uint8_t i = 0; i < 4; i++) {
      while (Serial.available() == 0) {
        vTaskDelay(6);
      }
      Serial.readBytes(&incomingString[i], 1);
      if (incomingString[i] == '\n')
        break;
    }
    if (incomingString[3] != '\n')
      continue;
    incomingString[3] = '-';
    // Analógico
    if (incomingString[0] == 'A' || incomingString[0] == 'a'){
      if (incomingString[2] == '1')
        activeAnalogic(incomingString[1], 1);
      if (incomingString[2] == '0')
        activeAnalogic(incomingString[1], 0);
    }
    // Digital
    if (incomingString[0] == 'D' || incomingString[0] == 'd'){
      // Poner en bajo
      if (incomingString[2] == '0'){
        pin = str2pin(incomingString[1]);
        digitalWrite(pin, LOW);
        confirm_cycles[pin] = 0;
      }
      // Poner en alto
      if (incomingString[2] == '1'){
        pin = str2pin(incomingString[1]);
        digitalWrite(pin, HIGH);
        confirm_cycles[pin] = 0;
      }
      // Poner en estado bajo con confirmación
      if (incomingString[2] == '5'){
        pin = str2pin(incomingString[1]);
        digitalWrite(pin, LOW);
        confirm_cycles[pin] = confirm_cycles_max;
      }
      // Poner en estado alto con confirmación
      if (incomingString[2] == '6'){
        pin = str2pin(incomingString[1]);
        digitalWrite(pin, HIGH);
        confirm_cycles[pin] = confirm_cycles_max;
      }
      // Poner como entrada
      if (incomingString[2] == '3')
        pinMode(str2pin(incomingString[1]), INPUT);
      // Poner como salida
      if (incomingString[2] == '4')
        pinMode(str2pin(incomingString[1]), OUTPUT);
    }
    // Período
    if (incomingString[0] == 'T' || incomingString[0] == 't'){
      // Ajustar el período
      delay_loop = str2delay_time(incomingString[1]);
    }
    vTaskDelay(5);
  }
}

void activeAnalogic(char an, uint8_t active){
  /*
  Activa o desactiva la lectura del puento analógico

  Parámetros:
  -----------
    an : char
      Pin analógico a desactivar ('A', 'B', ...)
    active : uint8_t
      Activar o desactivar el puerto. 1: activar, 0: desactivar
  */
  switch (an) {
    case 'A':
      vA_active[0] = active;
      break;
    case 'B':
      vA_active[1] = active;
      break;
    case 'C':
      vA_active[2] = active;
      break;
    case 'D':
      vA_active[3] = active;
      break;
    case 'E':
      vA_active[4] = active;
      break;
    case 'F':
      vA_active[5] = active;
      break;
    case 'G':
      vA_active[6] = active;
      break;
    case 'H':
      vA_active[7] = active;
      break;
  }
}

int str2pin(char c){
  switch (c) {
    case 'A': case 'a':
      return 0;
      break;
    case 'B': case 'b':
      return 1;
      break;
    case 'C': case 'c':
      return 2;
      break;
    case 'D': case 'd':
      return 3;
      break;
    case 'E': case 'e':
      return 4;
      break;
    case 'F': case 'f':
      return 5;
      break;
    case 'G': case 'g':
      return 6;
      break;
    case 'H': case 'h':
      return 7;
      break;
    case 'I': case 'i':
      return 8;
      break;
    case 'J': case 'j':
      return 9;
      break;
    case 'K': case 'k':
      return 10;
      break;
    case 'L': case 'l':
      return 11;
      break;
    case 'M': case 'm':
      return 12;
      break;
    case 'N': case 'n':
      return 13;
      break;
  }
}


int str2delay_time(char c){
  switch (c) {
    case 'A': case 'a':
      return 10;
      break;
    case 'B': case 'b':
      return 50;
      break;
    case 'C': case 'c':
      return 100;
      break;
    case 'D': case 'd':
      return 200;
      break;
    case 'E': case 'e':
      return 300;
      break;
    case 'F': case 'f':
      return 400;
      break;
    case 'G': case 'g':
      return 500;
      break;
    case 'H': case 'h':
      return 600;
      break;
    case 'I': case 'i':
      return 700;
      break;
    case 'J': case 'j':
      return 800;
      break;
    case 'K': case 'k':
      return 900;
      break;
    case 'L': case 'l':
      return 1000;
      break;
    case 'M': case 'm':
      return 1200;
      break;
    case 'N': case 'n':
      return 1500;
      break;
    case 'O': case 'o':
      return 1700;
      break;
    case 'P': case 'p':
      return 2000;
      break;
    case 'Q': case 'q':
      return 3000;
      break;
    case 'R': case 'r':
      return 4000;
      break;
    case 'S': case 's':
      return 5000;
      break;
    case 'T': case 't':
      return 7000;
      break;
    case 'U': case 'u':
      return 10000;
      break;
    case 'V': case 'v':
      return 15000;
      break;
    case 'W': case 'w':
      return 20000;
      break;
    case 'X': case 'x':
      return 30000;
      break;
    case 'Y': case 'y':
      return 60000;
      break;
    case 'Z': case 'z':
      return 120000;
      break;
  }
}


