# Pulse-Guard: Edge AI Wearable for Geriatric Fall Detection & Vital Signs Monitoring
**Gharbiya STEM High School | Grade 11 | Semester 1 (2026/2027) | Group 19204**

## Overview
Pulse-Guard is an autonomous, low-profile wrist-worn device powered by a **Raspberry Pi Pico 2 W (RP2350)**. It runs a memory-optimized, rule-based Edge AI classifier at 100 Hz to detect geriatric falls and monitor heart rate in real time, featuring a 20-second tactile cancel countdown and automated Telegram emergency alerts.

## Hardware Architecture
* **Microcontroller:** Raspberry Pi Pico 2 W (MicroPython)
* **Inertial Sensor:** MPU-6050 (6-axis Accelerometer & Gyroscope on I2C `GP4`/`GP5`)
* **Vital Signs Sensor:** MAX30102 Optical PPG Heart Rate Sensor (shared I2C bus)
* **Power Management:** TP4056 LiPo Charger + 3.7V 1400mAh LiPo routed to `VSYS` (Pin 39)
* **User Interface:** Tactile Cancel Button (`GP14`) & 12mm Piezo Buzzer (`GP15`)

## Key Results
* **Detection Accuracy:** 96.7% across 60 controlled trials (Sensitivity: 97.2%, Specificity: 95.8%)
* **Alert Latency:** 1.18 seconds over 2.4 GHz Wi-Fi
* **Battery Endurance:** 32.4 hours continuous runtime on a single charge
