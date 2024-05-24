
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
     I -> A8    D8    700ms
     J -> A9    D9    800ms
     K -> A10   D10   900ms
     L -> A11   D11   1000ms
     M -> A12   D12   1200ms
     N -> A13   D13   1500ms
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
int const SIZE_STROUT = 512;

int adc_a0 = 0;
int adc_a1 = 0;
int adc_a2 = 0;
int adc_a3 = 0;
int adc_a4 = 0;
int adc_a5 = 0;
int adc_a6 = 0;
int adc_a7 = 0;

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
char strout_json[SIZE_STROUT] = "";

int SENSOR_MAX_PIN = 3;
int sensor_max = 0;
uint8_t vD2, vD3, vD4, vD5, vD6, vD7, vD8, vD9, vD10, vD11, vD12, vD13;  // valor del pin digital
int vA0, vA1, vA2, vA3, vA4, vA5, vA6, vA7;  // valor del conversor analógico
uint8_t vA0_active=0, vA1_active=0, vA2_active=0, vA3_active=0, vA4_active=0, vA5_active=0, vA6_active=0, vA7_active=0;
int confirm_cycles[14] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
int confirm_cycles_max = 6;
int pin;
unsigned long delay_loop = 1000;  // Tiempo de retardo del loop.

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(SENSOR_MAX_PIN, INPUT);
  pinMode(13, OUTPUT);
  analogReference(INTERNAL);  // 1.1 volt
}


int read_adc(uint8_t pin){
  uint8_t const N_VALUES = 8;
  int const DISTANCE = 4;
  int values[N_VALUES];
  int sum = 0;
  int average = 0;
  int distance_max = 0;
  int distance = 0;
  do {
    sum = 0;
    distance_max = 0;
    for (uint8_t i = 0; i < N_VALUES; i++) {
      values[i] = analogRead(A0);
      sum += values[i];
      delay(10);
    }
    average = sum / N_VALUES;
    for (uint8_t i = 0; i < N_VALUES; i++) {
      if (average > values[i]){
        distance = average - values[i];
      }else {
        distance = values[i] - average;
      }
      if (distance > distance_max){
        distance_max = distance;
      }
    }
  }while (distance_max > DISTANCE);
  return average;
}



int read_adc_average(uint8_t pin){
  uint8_t const N_VALUES = 100;
  int values[N_VALUES];
  uint32_t sum = 0;
  int average = 0;
  for (uint8_t i = 0; i < N_VALUES; i++) {
    values[i] = analogRead(A0);
    sum += values[i];
    delay(10);
  }
  average = sum / N_VALUES;
  return average;
}

void loop() {
  // put your main code here, to run repeatedly:
  //adc_value = read_adc_average(A0);
  vD2 = digitalRead(2);
  vD3 = digitalRead(3);
  vD4 = digitalRead(4);
  vD5 = digitalRead(5);
  vD6 = digitalRead(6);
  vD7 = digitalRead(7);
  vD8 = digitalRead(8);
  vD9 = digitalRead(9);
  vD10 = digitalRead(10);
  vD11 = digitalRead(11);
  vD12 = digitalRead(12);
  vD13 = digitalRead(13);
  if (vA0_active)
    vA0 = read_adc_average(A0);
  else
   vA0 = -1;
  if (vA1_active)
    vA1 = read_adc_average(A1);
  else
   vA1 = -1;
  if (vA2_active)
    vA2 = read_adc_average(A2);
  else
   vA2 = -1;
  if (vA3_active)
    vA3 = read_adc_average(A3);
  else
   vA3 = -1;
  if (vA4_active)
    vA4 = read_adc_average(A4);
  else
   vA4 = -1;
  if (vA5_active)
    vA5 = read_adc_average(A5);
  else
   vA5 = -1;
  if (vA6_active)
    vA6 = read_adc_average(A6);
  else
   vA6 = -1;
  if (vA7_active)
    vA7 = read_adc_average(A7);
  else
   vA7 = -1;
  sprintf(strout_s, strout, vA0, vA1, vA2, vA3, vA4, vA5, vA6, vA7, vD2, vD3, vD4, vD5, vD6, vD7, vD8, vD9, vD10, vD11, vD12, vD13);
  Serial.println(strout_s);
  while (Serial.available() > 0) {
    // read the incoming string:
    String incomingString = Serial.readStringUntil('\n');
    // Analógico
    if (incomingString[0] == 'A' || incomingString[0] == 'a'){
      if (incomingString[2] == '1')
        active_analogic(incomingString[1], 1);
      if (incomingString[2] == '0')
        active_analogic(incomingString[1], 0);
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
  }
  // Verificar los pines con confirmación
  for (int i = 0; i < 14; i++){
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
  delay(delay_loop);
}

void active_analogic(char an, uint8_t active){
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
      vA0_active = active;
      break;
    case 'B':
      vA1_active = active;
      break;
    case 'C':
      vA2_active = active;
      break;
    case 'D':
      vA3_active = active;
      break;
    case 'E':
      vA4_active = active;
      break;
    case 'F':
      vA5_active = active;
      break;
    case 'G':
      vA6_active = active;
      break;
    case 'H':
      vA7_active = active;
      break;
  }
}

void desactive_analogic(char an){

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




