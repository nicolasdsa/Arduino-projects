# HC-08 BLE Servo Remote (UART)

Control a servo **wirelessly over BLE (UART)** using an HC-08 module.  
Send **absolute angles** (`0..180`) or **relative moves** (`+N` / `-N`) from your phone/PC and the servo moves **smoothly** to the target (tweening with step + delay).

---

## Bill of Materials

- 1× Arduino Uno (or compatible)
- 1× HC-08 BLE (UART) module
- 1× Servo (e.g., SG90 / MG90S)
- Breadboard + jumper wires

> **Power note:** Many HC-08 breakout boards accept **5 V on VCC** (onboard regulator) but their **UART pins are 3.3 V**. Always check your specific board. If unsure, use 3.3 V for VCC and shift Arduino TX down to 3.3 V.

---

## How It Works (Protocol)

- Open a BLE UART terminal/app and connect to the HC-08 (default baud **9600**).
- Send **one command per line** (ends with `\n`):
  - Absolute position: `0`..`180`
  - Relative move: `+N` or `-N` (e.g., `+10`, `-20`)
- The servo moves smoothly from the current position to the target using:
  - step size (default **2°** per step)
  - delay per step (default **10 ms**)
- The device echoes status on both **USB Serial (115200)** and **BLE (9600)**:

---

## Code Highlights

- **Smooth tweening**: `moveServoSmooth(target, step=2, delayMs=10)` – adjustable feel.
- **Clamping**: angle constrained to **0..180**.
- **Dual input**: reads commands from **BLE** and **USB Serial**.
- **Robust line parsing** with small buffers and newline delimiting.

---

## How to Run

1. Open `hc08-ble-servo-remote.ino` in Arduino IDE.
2. Select board/port and upload.
3. Open **Serial Monitor** at **115200** (optional logging).
4. Pair your phone/PC with the **HC-08**, connect via a **BLE UART app** (9600 baud setting for the module’s UART side).
5. Send commands: `0..180`, `+N`, `-N`.

---

## Diagram
- PNG: ![`media/sketch.png`](media/sketch.png)