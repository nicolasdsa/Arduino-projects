# LDR Auto-Dimming LED (PWM)

Adjusts LED brightness **inversely** to ambient light using an LDR (photoresistor).  
Darker environment ⇒ LED gets brighter; brighter environment ⇒ LED dims.  
Includes normalization with calibratable min/max voltage and an exponential moving average to smooth flicker.

---

## Bill of Materials

- 1× Arduino Uno (or compatible)
- 1× LDR (photoresistor), ~10 kΩ @ room light (typical)
- 1× Fixed resistor **10 kΩ** (forms a voltage divider with the LDR)
- 1× LED
- 1× Resistor **220–330 Ω** (LED series)
- Breadboard + jumper wires

> The exact fixed-resistor value depends on your LDR. 10 kΩ is a good starting point.

---

## How to Run

1. Open `ldr-auto-dimming-led.ino` in Arduino IDE.
2. Select the board/port and upload.
3. Open the Serial Monitor at **9600 baud** to see distance logs.

---

## Code Highlights

- const float V_MIN = 0.30;   // calibration: voltage seen in (near) dark
- const float V_MAX = 1.20;   // calibration: voltage seen in bright light

---

## Diagram
- PNG: ![`media/sketch.png`](media/sketch.png)