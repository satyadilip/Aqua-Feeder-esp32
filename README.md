# 🐟 Aqua Feeder AG_V1 — v4.0.0

**Automated Aquaculture Feed Dispensing System**

An ESP32-S3 based automated fish/shrimp feed dispenser with **20x4 LCD display**, **LoRaWAN + WiFi + GSM** multi-channel cloud telemetry, **web configuration dashboard**, precision motor control, and industrial safety features.

---

## 📋 Features

- **Scheduled Feeding** — Configure daily feed cycles with quantity, rate, and timing
- **Dual Motor Control** — Loader + Dispenser motors with pre/post run sequencing
- **20x4 LCD Display** — JHD629-204A real-time status and menu system
- **Multi-Channel Cloud** — LoRaWAN (IN865) primary, WiFi & SIM800L GPRS fallback
- **WiFi Dashboard** — Built-in SoftAP (`AquaFeeder-Config` / `aqua1234`) with responsive web UI
- **AWS IoT Core** — Telemetry to AWS via LoRaWAN gateway or MQTT
- **Proximity Sensor** — Auto-pause when obstruction detected, resume after clearance
- **Overcurrent Protection** — INA219 monitors motor current, auto-stop on jam
- **Power Monitoring** — Real-time voltage, current, power display
- **MicroSD Logging** — Offline telemetry storage with sync-on-reconnect
- **Persistent Settings** — NVS flash storage for all configuration
- **Serial CLI** — Debug and control via USB serial commands
- **Safety First** — Emergency stop, operational hour limits (06:00–18:00), robust relay shutdown

## 🔧 Hardware Platform (AG_V1)

| Component | Specification |
|-----------|--------------|
| **MCU** | YD-ESP32-S3 N16R8 (16MB Flash, 8MB PSRAM) |
| **Display** | JHD629-204A 20x4 I2C LCD (SDA=8, SCL=9) |
| **RTC** | DS3231 I2C (0x68) |
| **Power Monitor** | INA219 I2C (0x40) |
| **LoRa** | E22-900M22S (SX1262) SPI — IN865 Band |
| **GSM** | SIM800L UART1 (TX=18, RX=17) |
| **LoRa Gateway** | Seeed Studio SenseCAP M2 |
| **SD Card** | MicroSD SPI (CS=15) |
| **Relays** | RL1=Loader (GPIO41), RL2=Dispenser (GPIO39) |
| **Alarm** | Hooter (GPIO38) |
| **LEDs** | Red=STAT1(GPIO40), Green=STAT2(GPIO42) |
| **Buttons** | SW1=UP(4), SW2=DN(5), SW3=SEL(6), SW4=CFG(7) |
| **Proximity** | PC817 Optocoupler (GPIO16, Active LOW) |
| **WiFi** | SoftAP: `AquaFeeder-Config` / `aqua1234` |

## 📁 Project Structure

```
Aqua_feeder/
├── AquaFeeder/
│   ├── AquaFeeder.ino          # Main firmware sketch
│   ├── config.h                # Pin definitions, constants, shared types
│   ├── hal.h / hal.cpp         # Hardware Abstraction Layer
│   ├── config_manager.h/.cpp   # NVS Preferences persistence
│   ├── rtc_manager.h/.cpp      # DS3231 RTC wrapper
│   ├── power_monitor.h/.cpp    # INA219 voltage/current monitor
│   ├── lcd_display.h/.cpp      # 20x4 LCD display driver & menus
│   ├── sd_logger.h/.cpp        # MicroSD card logging
│   ├── lora_manager.h/.cpp     # LoRaWAN SX1262 driver (IN865)
│   ├── gsm_manager.h/.cpp      # SIM800L AT command driver
│   ├── wifi_manager.h/.cpp     # WiFi AP/STA + WebServer
│   ├── feed_engine.h/.cpp      # Feed cycle state machine
│   ├── telemetry.h/.cpp        # Telemetry event queue
│   ├── cloud_manager.h/.cpp    # Unified cloud failover manager
│   └── web_dashboard.h         # PROGMEM HTML/CSS/JS dashboard
└── README.md
```

## 🚀 Quick Start

1. **Open** `AquaFeeder/AquaFeeder.ino` in Arduino IDE 2.x
2. **Select Board:** ESP32S3 Dev Module (16MB Flash, 8MB PSRAM)
3. **Install Libraries:**
   - `LiquidCrystal_I2C` (LCD)
   - `RTClib` (DS3231)
   - `Adafruit_INA219` (Power Monitor)
   - `RadioLib` (SX1262 LoRa)
   - `ArduinoJson` (Web API)
   - `WiFi`, `WebServer`, `Preferences`, `SPI`, `Wire`, `SD` (built-in)
4. **Upload** and connect to `AquaFeeder-Config` WiFi
5. **Open** `http://192.168.4.1` for web dashboard

## 📡 Cloud Communication

| Priority | Channel | Protocol | Target |
|----------|---------|----------|--------|
| 1 (Primary) | **LoRaWAN** | IN865 OTAA via SenseCAP M2 | AWS IoT Core for LoRaWAN |
| 2 (Fallback) | **WiFi** | MQTT/TLS | AWS IoT Core |
| 3 (Fallback) | **SIM800L GPRS** | MQTT/TCP | AWS IoT Core |
| 4 (Offline) | **MicroSD** | CSV file | Sync on reconnect |

### Telemetry Schedule
- **Session Reports**: Sent immediately after each feed event completion
- **Periodic Heartbeat**: Every 3 hours (configurable 5min – 24h)

## 📡 Web API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard UI |
| `/api/status` | GET | JSON system status |
| `/api/settings` | POST | Update feed parameters |
| `/api/network` | POST | Update network/cloud config |
| `/api/start` | POST | Start feed cycle |
| `/api/stop` | POST | Emergency stop |
| `/api/test` | POST | Test relay/hooter |
| `/api/reboot` | POST | Reboot device |
| `/api/reset` | POST | Factory reset |

## 🖥️ Serial Commands

| Command | Action |
|---------|--------|
| `S` / `STATUS` | Print full system status |
| `RUN` | Start feed cycle |
| `STOP` / `0` | Emergency stop all motors |
| `R1` | Test loader relay for 2s |
| `R2` | Test dispenser relay for 2s |
| `HORN` | Test hooter for 1s |
| `SCAN` | I2C bus scan |
| `RESET` | Factory reset |
| `REBOOT` | Restart ESP32 |
| `H` / `HELP` | Show command list |

## 📜 License

Proprietary — Athena Engineering Corp. All rights reserved.
