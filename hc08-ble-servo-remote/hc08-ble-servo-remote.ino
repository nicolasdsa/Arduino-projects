#include <SoftwareSerial.h>
#include <Servo.h>

SoftwareSerial BLE(11, 12);
Servo servo;

const uint8_t SERVO_PIN = 9;
int currentPos = 90;           
const int MIN_ANG = 0;
const int MAX_ANG = 180;

String bufBLE = "";
String bufUSB = "";

void moveServoSmooth(int target, int step = 2, int delayMs = 10) {
  target = constrain(target, MIN_ANG, MAX_ANG);
  if (target == currentPos) return;

  int dir = (target > currentPos) ? 1 : -1;
  while (currentPos != target) {
    currentPos += dir * step;
    if ((dir > 0 && currentPos > target) || (dir < 0 && currentPos < target)) {
      currentPos = target;
    }
    servo.write(currentPos);
    delay(delayMs);
  }
}

void handleLine(const String& line) {
  String s = line;
  s.trim();
  if (s.length() == 0) return;

  long newTarget;
  if (s[0] == '+' || s[0] == '-') {
    long delta = s.toInt();           
    newTarget = currentPos + delta;
  } else {
    newTarget = s.toInt();           
  }

  int clamped = constrain((int)newTarget, MIN_ANG, MAX_ANG);
  moveServoSmooth(clamped);

  String msg = "Servo -> " + String(currentPos) + " deg";
  Serial.println(msg);
  BLE.println(msg);
}

void readStreamToBuffer(Stream& src, String& buffer) {
  while (src.available()) {
    char c = (char)src.read();
    if (c == '\r') continue;
    if (c == '\n') {
      handleLine(buffer);
      buffer = "";
    } else {
      buffer += c;
      if (buffer.length() > 32) buffer = "";
    }
  }
}

void setup() {
  Serial.begin(115200);
  BLE.begin(9600);    
  servo.attach(SERVO_PIN);
  servo.write(currentPos);
  delay(300);

  Serial.println("Ready! Send number: 0-180 (absolute), +N or -N (relative).");
  BLE.println("Ready! Send number: 0-180 (absolute), +N or -N (relative).");
}

void loop() {
  readStreamToBuffer(BLE,   bufBLE);
  readStreamToBuffer(Serial, bufUSB);
}
