#define AnalogLDR A0
#define PIN_LED   9

const float V_MIN = 0.30;  
const float V_MAX = 1.20;  

void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  int raw = analogRead(AnalogLDR);
  float v = raw * (5.0 / 1023.0);
  float norm = (v - V_MIN) / (V_MAX - V_MIN);
  if (norm < 0) norm = 0;
  if (norm > 1) norm = 1;

  float inv = 1.0 - norm;                 
  int pwm = (int)(inv * 255.0 + 0.5);
  static float avg = 0;
  avg = 0.9*avg + 0.1*pwm;    
  analogWrite(PIN_LED, (int)(avg+0.5));

  Serial.print("V="); Serial.print(v, 2);
  Serial.print("  inv="); Serial.print(inv, 2);
  Serial.print("  pwm="); Serial.println(pwm);
  delay(50);
}
