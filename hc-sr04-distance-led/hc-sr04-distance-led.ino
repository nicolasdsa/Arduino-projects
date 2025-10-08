#include <Arduino.h>

const uint8_t TRIG_PIN = 2;
const uint8_t ECHO_PIN = 3;
const uint8_t LED_PIN  = 8;

const float SOUND_SPEED_CM_PER_US = 0.0343f; 
const uint32_t PULSE_TIMEOUT_US   = 30000;    

const float THRESHOLD_ON_CM  = 10.0f;  
const float THRESHOLD_OFF_CM = 12.0f;  

bool ledOn = false;

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);

  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(9600);
  delay(100);
}

void loop() {
  const uint8_t SAMPLES = 5;
  float sum = 0.0f;
  uint8_t valid = 0;

  for (uint8_t i = 0; i < SAMPLES; i++) {
    float d = readDistanceCm();
    if (d > 0) {      
      sum += d;
      valid++;
    }
    delay(30); 
  }

  float distance = valid ? (sum / valid) : -1.0f;

  if (distance > 0) {
    Serial.print("Distance: ");
    Serial.print(distance, 1);
    Serial.println(" cm");
  } else {
    Serial.println("No echo (out of range / timeout)");
  }

  if (!ledOn && distance > 0 && distance < THRESHOLD_ON_CM) {
    ledOn = true;
    digitalWrite(LED_PIN, HIGH);
  } else if (ledOn && (distance < 0 || distance > THRESHOLD_OFF_CM)) {
    ledOn = false;
    digitalWrite(LED_PIN, LOW);
  }

  delay(80);
}

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long dur = pulseIn(ECHO_PIN, HIGH, PULSE_TIMEOUT_US);
  if (dur == 0) return -1.0f;

  return (dur * SOUND_SPEED_CM_PER_US) / 2.0f;
}
