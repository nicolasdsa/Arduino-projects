# Arduino / ESP32 Projects

A collection of small, documented hardware projects. Each project lives in its own folder with a self-contained sketch and media.

## Projects

| Project | Description | Demo | Folder |
|--------|-------------|------|--------|
| HC-SR04 Distance LED | Turns an LED on when distance < **10 cm** (with hysteresis to 12 cm). Averaged readings + timeout for stability. | ![](hc-sr04-distance-led/media/demo.gif) | [/hc-sr04-distance-led](hc-sr04-distance-led) |
| LDR Auto-Dimming LED | LED brightness adjusts **inversely** to ambient light using an LDR + PWM. Includes calibration (`V_MIN`/`V_MAX`) and EMA smoothing to reduce flicker. | ![](ldr-auto-dimming-led/media/demo.gif) | [/ldr-auto-dimming-led](ldr-auto-dimming-led) |
| HC-08 BLE Servo Remote | Control a servo via **BLE UART** (HC-08). Send absolute angles (`0..180`) or relative moves (`+N`/`-N`); smooth tweening with step/delay and dual logging (USB & BLE). | ![](hc08-ble-servo-remote/media/demo.gif) | [/hc08-ble-servo-remote](hc08-ble-servo-remote) |
