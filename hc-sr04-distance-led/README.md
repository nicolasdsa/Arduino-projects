# HC-SR04 Distance LED

Turns the LED (D8) **ON** when measured distance is **below 10 cm**, and **OFF** above 12 cm (hysteresis).  
Includes averaging across multiple readings and a `pulseIn` timeout for robustness.

![Demo](media/demo.gif)

---
## Bill of Materials

- 1× Arduino Uno 
- 1× HC-SR04 ultrasonic sensor
- 1× LED (any color)
- 1× Resistor **220–330 Ω** (LED series)
- Breadboard + jumper wires

---

## How to Run

1. Open `hc-sr04-distance-led.ino` in Arduino IDE.
2. Select the board/port and upload.
3. Open the Serial Monitor at **9600 baud** to see distance logs.

---

## Code Highlights

- 10 µs trigger pulse on TRIG.
- `pulseIn(ECHO, HIGH, 30000)` timeout (~30 ms) to avoid blocking if no echo.
- Convert time to distance:  
  `distance_cm = (echo_us * 0.0343) / 2`
- Average of 5 valid samples + **hysteresis** (ON < 10 cm, OFF > 12 cm) to prevent flicker near the threshold.

---

## Diagram
- PNG: ![`media/sketch.png`](media/sketch.png)
