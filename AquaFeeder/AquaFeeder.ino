// ============================================================================
// AQUA FEEDER AG_V1 — Main Firmware Sketch
// ============================================================================
// Platform:  YD-ESP32-S3 N16R8 (16MB Flash, 8MB PSRAM)
// Board:     AG_V1 (Athena Engineering Corp)
// Version:   4.0.0
//
// HARDWARE:
//   LCD:       JHD629-204A 20x4 I2C (SDA=8, SCL=9)
//   RTC:       DS3231 I2C (0x68)
//   Power:     INA219 I2C (0x40)
//   LoRa:      E22-900M22S SX1262 SPI (IN865)
//   GSM:       SIM800L UART1 (TX=18, RX=17)
//   WiFi:      ESP32-S3 SoftAP + STA
//   SD Card:   MicroSD SPI (CS=15)
//   Relays:    RL1=Loader (GPIO41), RL2=Dispenser (GPIO39)
//   Hooter:    GPIO38, LEDs: Red=GPIO40, Green=GPIO42
//   Buttons:   SW1=UP(4), SW2=DN(5), SW3=SEL(6), SW4=CFG(7)
//   Proximity: PROX-SW (GPIO16, Active LOW)
// ============================================================================

#include <Wire.h>
#include <SPI.h>
#include <WiFi.h>
#include <WebServer.h>

#include "config.h"
#include "af_hal.h"
#include "config_manager.h"
#include "rtc_manager.h"
#include "power_monitor.h"
#include "lcd_display.h"
#include "sd_logger.h"
#include "lora_manager.h"
#include "gsm_manager.h"
#include "wifi_manager.h"
#include "feed_engine.h"
#include "telemetry.h"
#include "cloud_manager.h"
#include "web_dashboard.h"

// ═══════════════════════════════════════════════════════════════════════════
// GLOBAL OBJECTS
// ═══════════════════════════════════════════════════════════════════════════

HardwareLayer  hal;
ConfigManager  cfgMgr;
RTCManager     rtcMgr;
PowerMonitor   pwrMon;
LCDDisplay     lcd;
SDLogger       sdLog;
LoRaManager    loraMgr;
GSMManager     gsmMgr;
WiFiManager_AF wifiMgr;
WebServer      webServer(WIFI_WEB_PORT);
FeedEngine     feedEng;
TelemetryManager telMgr;
CloudManager   cloudMgr;

// ── Shared State ──
DeviceConfig   config;
SystemStatus   sysStatus;
MenuState      currentMenu = MenuState::MAIN_STATUS;
MenuState      previousMenu = MenuState::MAIN_STATUS;

// ── Menu/Edit State (local, passed to LCD) ──
int            menuCursorIdx = 0;
int            editVal       = 0;
int            editFld       = 0;

// ── Timing ──
unsigned long  lastPowerReadMs  = 0;
unsigned long  lastSerialDbgMs  = 0;
const unsigned long POWER_READ_INTERVAL_MS = 500;
const unsigned long SERIAL_DBG_INTERVAL_MS = 10000;

// ═══════════════════════════════════════════════════════════════════════════
// CALLBACK FUNCTIONS (Bridge between modules)
// ═══════════════════════════════════════════════════════════════════════════

void cbSetRelay(int relay, bool on) {
    hal.setRelay(relay, on);
}

void cbMotorsOff() {
    hal.motorsOff();
}

void cbTelemetryEvent(TelemetryMsgType type) {
    telMgr.queueEvent(type);
}

float cbReadCurrent() {
    pwrMon.update();
    sysStatus.currentMA = pwrMon.getCurrent();
    return sysStatus.currentMA;
}

void cbOnFeedStart() {
    feedEng.calcSchedule();
    if (sysStatus.scheduleValid) {
        feedEng.startFeed();
        currentMenu = MenuState::RUNNING;
        Serial.println("[MAIN] Feed started via web/button!");
    }
}

void cbOnFeedStop() {
    feedEng.stopFeed();
    currentMenu = MenuState::MAIN_STATUS;
    Serial.println("[MAIN] Feed stopped!");
}

void cbOnSaveConfig(const DeviceConfig& newCfg) {
    config = newCfg;
    cfgMgr.saveFeedParams(config);
    feedEng.calcSchedule();
    Serial.println("[MAIN] Config saved via web.");
    telMgr.queueEvent(TelemetryMsgType::SETTINGS_REPORT);
}

void cbOnSaveNetwork(const DeviceConfig& newCfg) {
    config = newCfg;
    cfgMgr.saveNetworkConfig(config);
    Serial.println("[MAIN] Network config saved via web.");
}

void cbOnDownlink(const LoRaDownlinkPayload& dl) {
    if (dl.msgType == (uint8_t)CommandMsgType::CMD_SET_SETTINGS) {
        Serial.println("[MAIN] Received SET_SETTINGS Downlink!");
        
        config.feedQuantity = dl.feedQuantity / 10.0f;
        config.feedPerEvent = dl.feedPerEvent;
        config.startHour = dl.startHour;
        config.startMinute = dl.startMinute;
        config.endHour = dl.endHour;
        config.endMinute = dl.endMinute;
        config.dischargeRate = dl.dischargeRate;
        
        cfgMgr.saveFeedParams(config);
        feedEng.calcSchedule();
        Serial.println("[MAIN] Settings applied from Downlink!");
        
        // Transmit confirmation report
        telMgr.queueEvent(TelemetryMsgType::SETTINGS_REPORT);
    } 
    else if (dl.msgType == (uint8_t)CommandMsgType::CMD_POLL_DATA) {
        Serial.println("[MAIN] Received POLL_DATA Downlink!");
        telMgr.queueEvent(TelemetryMsgType::PERIODIC_HEARTBEAT);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SERIAL CLI
// ═══════════════════════════════════════════════════════════════════════════

void handleSerialCommand(String cmd) {
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "S" || cmd == "STATUS") {
        Serial.println("\n╔═══════════════════════════════════════╗");
        Serial.println("║       AQUA FEEDER STATUS              ║");
        Serial.println("╚═══════════════════════════════════════╝");
        if (sysStatus.rtcOK) {
            Serial.print("[TIME]  "); Serial.println(rtcMgr.getDateTimeStr());
        }
        Serial.print("[STATE] "); Serial.println((uint8_t)sysStatus.state);
        Serial.print("[FEED]  Active="); Serial.print(sysStatus.feedActive);
        Serial.print(" Event="); Serial.print(sysStatus.currentEvent);
        Serial.print("/"); Serial.println(sysStatus.totalEvents);
        Serial.print("[QTY]   "); Serial.print(config.feedQuantity, 1); Serial.println(" kg");
        Serial.print("[FPE]   "); Serial.print(config.feedPerEvent); Serial.println(" g");
        Serial.print("[RATE]  "); Serial.print(config.dischargeRate); Serial.println(" g/s");
        Serial.print("[TIME]  "); Serial.print(config.startHour); Serial.print(":"); Serial.print(config.startMinute);
        Serial.print(" to "); Serial.print(config.endHour); Serial.print(":"); Serial.println(config.endMinute);
        Serial.print("[POWER] "); Serial.print(sysStatus.voltageV, 2); Serial.print("V ");
        Serial.print(sysStatus.currentMA, 0); Serial.print("mA ");
        Serial.print(sysStatus.powerMW, 0); Serial.println("mW");
        Serial.print("[NET]   LoRa="); Serial.print((uint8_t)sysStatus.loraStatus);
        Serial.print(" WiFi="); Serial.print((uint8_t)sysStatus.wifiStatus);
        Serial.print(" GSM="); Serial.print((uint8_t)sysStatus.gsmStatus);
        Serial.print(" SD="); Serial.println(sysStatus.sdCardOK ? "OK" : "FAIL");
        Serial.print("[PROX]  "); Serial.println(sysStatus.proximityTriggered ? "TRIGGERED" : "Clear");
        Serial.print("[SCHED] "); Serial.println(sysStatus.scheduleValid ? "Valid" : sysStatus.schedError);
    }
    else if (cmd == "EUI") {
        Serial.println("\n╔═══════════════════════════════════════╗");
        Serial.println("║         LoRaWAN CREDENTIALS           ║");
        Serial.println("╚═══════════════════════════════════════╝");
        Serial.print("DevEUI: ");
        for (int i=0; i<8; i++) { Serial.printf("%02X", config.loraDevEUI[i]); }
        Serial.println();
        Serial.print("AppEUI: ");
        for (int i=0; i<8; i++) { Serial.printf("%02X", config.loraAppEUI[i]); }
        Serial.println();
        Serial.print("AppKey: ");
        for (int i=0; i<16; i++) { Serial.printf("%02X", config.loraAppKey[i]); }
        Serial.println();
    }
    else if (cmd == "RUN") {
        cbOnFeedStart();
    }
    else if (cmd == "STOP" || cmd == "0") {
        cbOnFeedStop();
    }
    else if (cmd == "R1") {
        Serial.println("[TEST] Relay 1 (Loader) 2s...");
        hal.setRelay(1, true); delay(2000); hal.setRelay(1, false);
    }
    else if (cmd == "R2") {
        Serial.println("[TEST] Relay 2 (Dispenser) 2s...");
        hal.setRelay(2, true); delay(2000); hal.setRelay(2, false);
    }
    else if (cmd == "HORN" || cmd == "HOOTER") {
        Serial.println("[TEST] Hooter 1s...");
        hal.setHooter(true); delay(1000); hal.setHooter(false);
    }
    else if (cmd == "SCAN") {
        Serial.println("[I2C] Scanning...");
        for (uint8_t addr = 1; addr < 127; addr++) {
            Wire.beginTransmission(addr);
            if (Wire.endTransmission() == 0) {
                Serial.print("  Found: 0x"); Serial.println(addr, HEX);
            }
        }
        Serial.println("[I2C] Scan complete.");
    }
    else if (cmd == "RESET") {
        Serial.println("[!] Factory reset...");
        cfgMgr.resetToDefaults(config);
        delay(500);
        ESP.restart();
    }
    else if (cmd == "REBOOT") {
        Serial.println("[!] Rebooting...");
        delay(500);
        ESP.restart();
    }
    else if (cmd == "H" || cmd == "HELP") {
        Serial.println("  S/STATUS — Full status");
        Serial.println("  EUI      — View LoRaWAN DevEUI/AppKey");
        Serial.println("  RUN      — Start feed cycle");
        Serial.println("  STOP/0   — Emergency stop");
        Serial.println("  R1       — Test Loader relay 2s");
        Serial.println("  R2       — Test Dispenser relay 2s");
        Serial.println("  HORN     — Test Hooter 1s");
        Serial.println("  SCAN     — I2C bus scan");
        Serial.println("  RESET    — Factory reset");
        Serial.println("  REBOOT   — Restart ESP32");
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// BUTTON & MENU HANDLER
// ═══════════════════════════════════════════════════════════════════════════

// Menu items for the list view
const char* menuLabels[] = {
    "Feed Quantity", "Feed Per Event", "Start Time",
    "End Time", "Discharge Rate", "Set Clock",
    "Run Feed", "Network Info", "Power Info"
};
const int MENU_ITEM_COUNT = 9;

void handleButtonNavigation() {
    ButtonState& up   = hal.btnUp();
    ButtonState& dn   = hal.btnDown();
    ButtonState& sel  = hal.btnSelect();
    ButtonState& cfg  = hal.btnConfig();

    if (!up.risingEdge && !dn.risingEdge && !sel.risingEdge && !cfg.risingEdge) return;

    // SW4 (Config) — toggle AP config / return to main / enter menu from running
    if (cfg.risingEdge) {
        if (currentMenu == MenuState::MENU_LIST || currentMenu == MenuState::MAIN_STATUS) {
            currentMenu = (currentMenu == MenuState::MAIN_STATUS) ?
                          MenuState::MENU_LIST : MenuState::MAIN_STATUS;
        } else if (currentMenu == MenuState::RUNNING) {
            currentMenu = MenuState::MENU_LIST; // Allow entering menu while running
        } else {
            // Return to appropriate state
            if (feedEng.isActive()) {
                currentMenu = MenuState::RUNNING;
            } else {
                currentMenu = MenuState::MENU_LIST;
            }
        }
        return;
    }

    switch (currentMenu) {
        case MenuState::MAIN_STATUS:
            if (sel.risingEdge) currentMenu = MenuState::MENU_LIST;
            break;

        case MenuState::MENU_LIST:
            if (up.risingEdge) {
                menuCursorIdx--;
                if (menuCursorIdx < 0) menuCursorIdx = MENU_ITEM_COUNT - 1;
            }
            if (dn.risingEdge) {
                menuCursorIdx++;
                if (menuCursorIdx >= MENU_ITEM_COUNT) menuCursorIdx = 0;
            }
            if (sel.risingEdge) {
                switch (menuCursorIdx) {
                    case 0: editVal = (int)(config.feedQuantity * 10);
                            currentMenu = MenuState::EDIT_QTY; break;
                    case 1: editVal = config.feedPerEvent;
                            currentMenu = MenuState::EDIT_FPE; break;
                    case 2: editVal = config.startHour;
                            editFld = 0;
                            currentMenu = MenuState::EDIT_START_TIME; break;
                    case 3: editVal = config.endHour;
                            editFld = 0;
                            currentMenu = MenuState::EDIT_END_TIME; break;
                    case 4: editVal = config.dischargeRate;
                            currentMenu = MenuState::EDIT_RATE; break;
                    case 5: if (sysStatus.rtcOK) {
                                int h, m, s;
                                rtcMgr.getTime(h, m, s);
                                editVal = h;
                                editFld = 0;
                            }
                            currentMenu = MenuState::EDIT_CLOCK; break;
                    case 6: // Run Feed
                            feedEng.calcSchedule();
                            if (sysStatus.scheduleValid) {
                                feedEng.startFeed();
                                currentMenu = MenuState::RUNNING;
                                telMgr.queueEvent(TelemetryMsgType::FEED_STARTED);
                            }
                            break;
                    case 7: currentMenu = MenuState::INFO_NETWORK; break;
                    case 8: currentMenu = MenuState::INFO_POWER; break;
                }
            }
            break;

        case MenuState::EDIT_QTY:
            if (up.risingEdge)   editVal = constrain(editVal + 5, 5, 1200);  // x10
            if (dn.risingEdge)   editVal = constrain(editVal - 5, 5, 1200);
            if (sel.risingEdge) {
                config.feedQuantity = editVal / 10.0f;
                cfgMgr.saveFeedParams(config);
                if (feedEng.isActive()) feedEng.recalcDynamic(rtcMgr.getEpoch());
                else feedEng.calcSchedule();
                currentMenu = feedEng.isActive() ? MenuState::RUNNING : MenuState::MENU_LIST;
            }
            break;

        case MenuState::EDIT_FPE:
            if (up.risingEdge)   editVal = constrain(editVal + FEED_FPE_STEP, FEED_FPE_MIN, FEED_FPE_MAX);
            if (dn.risingEdge)   editVal = constrain(editVal - FEED_FPE_STEP, FEED_FPE_MIN, FEED_FPE_MAX);
            if (sel.risingEdge) {
                config.feedPerEvent = editVal;
                cfgMgr.saveFeedParams(config);
                if (feedEng.isActive()) feedEng.recalcDynamic(rtcMgr.getEpoch());
                else feedEng.calcSchedule();
                currentMenu = feedEng.isActive() ? MenuState::RUNNING : MenuState::MENU_LIST;
            }
            break;

        case MenuState::EDIT_END_TIME:
            if (editFld == 0) {  // Editing hour
                if (up.risingEdge)   editVal = (editVal + 1) % 24;
                if (dn.risingEdge)   editVal = (editVal + 23) % 24;
                if (sel.risingEdge) {
                    config.endHour = editVal;
                    editVal = config.endMinute;
                    editFld = 1;  // Switch to minute
                }
            } else {  // Editing minute
                if (up.risingEdge)   editVal = (editVal + 1) % 60;
                if (dn.risingEdge)   editVal = (editVal + 59) % 60;
                if (sel.risingEdge) {
                    config.endMinute = editVal;
                    cfgMgr.saveFeedParams(config);
                    if (feedEng.isActive()) feedEng.recalcDynamic(rtcMgr.getEpoch());
                    else feedEng.calcSchedule();
                    currentMenu = feedEng.isActive() ? MenuState::RUNNING : MenuState::MENU_LIST;
                    editFld = 0;
                }
            }
            break;

        case MenuState::EDIT_START_TIME:
            if (editFld == 0) {  // Editing hour
                if (up.risingEdge)   editVal = (editVal + 1) % 24;
                if (dn.risingEdge)   editVal = (editVal + 23) % 24;
                if (sel.risingEdge) {
                    config.startHour = editVal;
                    editVal = config.startMinute;
                    editFld = 1;  // Switch to minute
                }
            } else {  // Editing minute
                if (up.risingEdge)   editVal = (editVal + 1) % 60;
                if (dn.risingEdge)   editVal = (editVal + 59) % 60;
                if (sel.risingEdge) {
                    config.startMinute = editVal;
                    cfgMgr.saveFeedParams(config);
                    if (feedEng.isActive()) feedEng.recalcDynamic(rtcMgr.getEpoch());
                    else feedEng.calcSchedule();
                    currentMenu = feedEng.isActive() ? MenuState::RUNNING : MenuState::MENU_LIST;
                    editFld = 0;
                }
            }
            break;

        case MenuState::EDIT_RATE:
            if (up.risingEdge)   editVal = constrain(editVal + 1, FEED_RATE_MIN, FEED_RATE_MAX);
            if (dn.risingEdge)   editVal = constrain(editVal - 1, FEED_RATE_MIN, FEED_RATE_MAX);
            if (sel.risingEdge) {
                config.dischargeRate = editVal;
                cfgMgr.saveFeedParams(config);
                if (feedEng.isActive()) feedEng.recalcDynamic(rtcMgr.getEpoch());
                else feedEng.calcSchedule();
                currentMenu = feedEng.isActive() ? MenuState::RUNNING : MenuState::MENU_LIST;
            }
            break;

        case MenuState::EDIT_CLOCK:
            if (editFld == 0) {  // Hour
                if (up.risingEdge)   editVal = (editVal + 1) % 24;
                if (dn.risingEdge)   editVal = (editVal + 23) % 24;
                if (sel.risingEdge) {
                    int savedHour = editVal;
                    int h, m, s;
                    rtcMgr.getTime(h, m, s);
                    editVal = m;
                    editFld = 1;
                    // Temporarily store hour
                    config.startHour = savedHour;  // Reuse temporarily
                }
            } else {  // Minute
                if (up.risingEdge)   editVal = (editVal + 1) % 60;
                if (dn.risingEdge)   editVal = (editVal + 59) % 60;
                if (sel.risingEdge) {
                    int setHour = config.startHour;  // Retrieve temp
                    int setMin = editVal;
                    // Restore startHour from config
                    cfgMgr.loadConfig(config);
                    rtcMgr.setTime(setHour, setMin, 0);
                    feedEng.calcSchedule();
                    currentMenu = MenuState::MENU_LIST;
                    editFld = 0;
                    Serial.println("[RTC] Clock set!");
                }
            }
            break;

        case MenuState::RUNNING:
            if (sel.risingEdge) {
                feedEng.stopFeed();
                currentMenu = MenuState::MAIN_STATUS;
                telMgr.queueEvent(TelemetryMsgType::FEED_STARTED);  // Log stop event
                Serial.println("[!] EMERGENCY STOP via button!");
            }
            break;

        case MenuState::PAUSED:
            if (sel.risingEdge) {
                // Check if proximity is clear before resuming
                if (!hal.isProximityTriggered()) {
                    hal.setHooter(false); // Stop hooter when resumed
                    feedEng.resumeFeed();
                    currentMenu = MenuState::RUNNING;
                    telMgr.queueEvent(TelemetryMsgType::FEED_RESUMED);
                } else {
                    // Flash red LED to indicate still blocked
                    hal.setLedRed(true);
                    delay(200);
                    hal.setLedRed(false);
                }
            }
            break;

        case MenuState::FINISHED:
            if (sel.risingEdge) {
                feedEng.calcSchedule();
                currentMenu = MenuState::MAIN_STATUS;
            }
            break;

        case MenuState::INFO_NETWORK:
        case MenuState::INFO_POWER:
            if (sel.risingEdge || cfg.risingEdge) {
                currentMenu = MenuState::MENU_LIST;
            }
            break;

        default:
            break;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// UPDATE SYSTEM STATUS STRUCT (for LCD & Web API)
// ═══════════════════════════════════════════════════════════════════════════

void updateSystemStatus() {
    sysStatus.proximityTriggered = hal.isProximityTriggered();
    // Map menu state to system state
    switch (currentMenu) {
        case MenuState::MAIN_STATUS:
        case MenuState::MENU_LIST:
            sysStatus.state = sysStatus.feedActive ? SystemState::IDLE : SystemState::IDLE;
            break;
        case MenuState::RUNNING:
            switch (sysStatus.feedState) {
                case FeedCycleState::FC_PRE:  sysStatus.state = SystemState::FEED_PRE_WARMUP; break;
                case FeedCycleState::FC_DISP: sysStatus.state = SystemState::FEED_DISPENSING; break;
                case FeedCycleState::FC_POST: sysStatus.state = SystemState::FEED_POST_CLEAR; break;
                case FeedCycleState::FC_WAIT: sysStatus.state = SystemState::FEED_WAIT_NEXT; break;
                default: sysStatus.state = SystemState::IDLE; break;
            }
            break;
        case MenuState::PAUSED:    sysStatus.state = SystemState::FEED_PAUSED; break;
        case MenuState::FINISHED:  sysStatus.state = SystemState::FEED_FINISHED; break;
        default:                   sysStatus.state = SystemState::IDLE; break;
    }

    // Proximity
    sysStatus.proximityTriggered = hal.isProximityTriggered();

    // RTC
    if (sysStatus.rtcOK) {
        sysStatus.currentEpoch = rtcMgr.getEpoch();
    }

    // Network status
    sysStatus.wifiStatus = wifiMgr.getStatus();
    sysStatus.loraStatus = loraMgr.getStatus();
    sysStatus.gsmStatus  = gsmMgr.getStatus();
    sysStatus.sdCardOK   = sdLog.isOK();

    // Boot time
    sysStatus.bootTimeMs = millis();
}

void runHardwareDiagnostics() {
    Serial.println("\n╔═══════════════════════════════════════════════════════════╗");
    Serial.println("║         AG_V1 HARDWARE DIAGNOSTIC RESULTS                 ║");
    Serial.println("╠═══════════════════════════════════════════════════════════╣");

    memset(&sysStatus.diag, 0, sizeof(sysStatus.diag));

    // 1. I2C Bus Scan
    uint8_t count = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            if (count < 16) sysStatus.diag.i2c_addrs[count] = addr;
            count++;
        }
    }
    sysStatus.diag.i2c_count = count;

    // 2. RTC DS3231 Check
    bool rtcFound = rtcMgr.isOK();
    for (uint8_t i = 0; i < count; i++) {
        if (sysStatus.diag.i2c_addrs[i] == I2C_ADDR_RTC) rtcFound = true;
    }
    sysStatus.diag.ds3231_rtc = rtcFound;
    Serial.printf("║ DS3231 RTC            : [ %s ] (I2C 0x68)\n", sysStatus.diag.ds3231_rtc ? "PASS" : "FAIL");

    // 3. INA219 Power Monitor Check
    bool pwrFound = pwrMon.isOK();
    for (uint8_t i = 0; i < count; i++) {
        if (sysStatus.diag.i2c_addrs[i] == I2C_ADDR_INA219) pwrFound = true;
    }
    sysStatus.diag.ina219_power = pwrFound;
    Serial.printf("║ INA219 Power Monitor  : [ %s ] (I2C 0x40)\n", sysStatus.diag.ina219_power ? "PASS" : "FAIL");

    // 4. JHD629 20x4 LCD Check
    sysStatus.diag.lcd_display = lcd.isOK();
    Serial.printf("║ JHD629 20x4 LCD       : [ %s ] (I2C 0x27/0x3F)\n", sysStatus.diag.lcd_display ? "PASS" : "FAIL");

    // 5. SX1262 LoRa Check
    sysStatus.diag.lora_sx1262 = loraMgr.isAvailable();
    Serial.printf("║ SX1262 LoRa Module    : [ %s ] (SPI CS=13, IN865)\n", sysStatus.diag.lora_sx1262 ? "PASS" : "FAIL (Check SPI wiring)");

    // 6. MicroSD Card Check
    sysStatus.diag.sd_card = sdLog.isOK();
    Serial.printf("║ MicroSD Card Reader   : [ %s ] (SPI CS=15, %s)\n", 
                  sysStatus.diag.sd_card ? "PASS" : "READY",
                  sysStatus.diag.sd_card ? "Card Mounted" : "No Card Inserted");

    // 7. SIM800L GSM Check
    sysStatus.diag.gsm_sim800l = gsmMgr.isAvailable();
    sysStatus.diag.gsm_csq = gsmMgr.getSignalQuality();
    Serial.printf("║ SIM800L GSM Modem     : [ %s ] (UART1 9600/115200)\n", 
                  sysStatus.diag.gsm_sim800l ? "PASS" : "FAIL (Check 4V power & TX/RX)");

    // 8. Push Buttons Check
    sysStatus.diag.sw1_ok = (digitalRead(PIN_BTN_UP) == HIGH);
    sysStatus.diag.sw2_ok = (digitalRead(PIN_BTN_DOWN) == HIGH);
    sysStatus.diag.sw3_ok = (digitalRead(PIN_BTN_SELECT) == HIGH);
    sysStatus.diag.sw4_ok = (digitalRead(PIN_BTN_CONFIG) == HIGH);
    Serial.printf("║ Push Buttons SW1-SW4  : [ %s ]\n", 
                  (sysStatus.diag.sw1_ok && sysStatus.diag.sw2_ok && sysStatus.diag.sw3_ok && sysStatus.diag.sw4_ok) ? "PASS" : "WARN");

    // 9. Proximity Sensor Check
    sysStatus.diag.prox_sensor_clear = !hal.isProximityTriggered();
    Serial.printf("║ Proximity Optocoupler : [ %s ] (Chute Clear)\n", sysStatus.diag.prox_sensor_clear ? "PASS" : "BLOCKED");

    Serial.printf("║ I2C Bus Active Devices: %d found (", count);
    for (int i = 0; i < count && i < 16; i++) {
        Serial.printf("0x%02X ", sysStatus.diag.i2c_addrs[i]);
    }
    Serial.println(")");
    Serial.println("╚═══════════════════════════════════════════════════════════╝\n");
}

// ═══════════════════════════════════════════════════════════════════════════
// CLOUD FREERTOS TASK (Runs on Core 0)
// ═══════════════════════════════════════════════════════════════════════════
void cloudTask(void* pvParameters) {
    while (true) {
        cloudMgr.loop();
        if (loraMgr.isAvailable()) {
            loraMgr.loop();
        }
        vTaskDelay(pdMS_TO_TICKS(10)); // Yield to IDLE task
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════════════════════

void setup() {
    // ── Serial Console ──
    delay(300);
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    while (!Serial && millis() < 5000);
    delay(500);

    Serial.println("\n╔═══════════════════════════════════════════╗");
    Serial.println("║   Aqua Feeder AG_V1 v4.0.0               ║");
    Serial.println("║   LoRa + WiFi + GSM + LCD                ║");
    Serial.println("║   Athena Engineering Corp                 ║");
    Serial.println("╚═══════════════════════════════════════════╝\n");

    // ── HAL Init (GPIOs) ──
    Serial.println("[INIT] HAL...");
    hal.begin();
    hal.setRgbLed(64, 64, 64);  // Glows WHITE on bootup
    hal.setLedRed(true);         // Red on during init
    hal.setLedGreen(false);

    // ── I2C Bus ──
    Serial.println("[INIT] I2C Bus...");
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setTimeOut(50);
    delay(200);

    // ── SPI Bus ──
    Serial.println("[INIT] SPI Bus...");
    SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);
    // Ensure all CS lines are HIGH (deselected)
    pinMode(PIN_SD_CS, OUTPUT);
    digitalWrite(PIN_SD_CS, HIGH);
    pinMode(PIN_LORA_NSS, OUTPUT);
    digitalWrite(PIN_LORA_NSS, HIGH);

    // ── RTC ──
    Serial.println("[INIT] RTC DS3231...");
    sysStatus.rtcOK = rtcMgr.begin();
    if (sysStatus.rtcOK) {
        Serial.print("[RTC]  "); Serial.println(rtcMgr.getDateTimeStr());
        Serial.print("[RTC]  Temp: "); Serial.print(rtcMgr.getTemperature()); Serial.println(" C");
    } else {
        Serial.println("[RTC]  *** FAILED — Check I2C wiring (SDA=8, SCL=9) ***");
    }

    // ── INA219 Power Monitor ──
    Serial.println("[INIT] INA219 Power Monitor...");
    if (pwrMon.begin()) {
        pwrMon.update();
        Serial.print("[PWR]  "); Serial.print(pwrMon.getVoltage(), 2);
        Serial.print("V  "); Serial.print(pwrMon.getCurrent(), 0);
        Serial.println("mA");
    } else {
        Serial.println("[PWR]  INA219 not found (non-critical).");
    }

    // ── LCD Display ──
    Serial.println("[INIT] LCD Display...");
    if (lcd.begin()) {
        Serial.println("[LCD]  20x4 LCD OK!");
    } else {
        Serial.println("[LCD]  LCD not found — using Serial + Web only.");
    }

    // ── NVS Config ──
    Serial.println("[INIT] Config Manager...");
    cfgMgr.begin();
    bool firstBoot = cfgMgr.isFirstBoot();
    cfgMgr.loadConfig(config);
    if (firstBoot) {
        Serial.println("[CFG]  First boot — defaults loaded.");
        // Generate a random device ID
        snprintf(config.deviceId, sizeof(config.deviceId),
                 "AF_%04X%04X", (uint16_t)(ESP.getEfuseMac() >> 32),
                 (uint16_t)(ESP.getEfuseMac() & 0xFFFF));
        cfgMgr.saveConfig(config);
        cfgMgr.markInitialized();
    }
    Serial.print("[CFG]  Device ID: "); Serial.println(config.deviceId);
    Serial.print("[CFG]  Qty="); Serial.print(config.feedQuantity, 1);
    Serial.print("kg FPE="); Serial.print(config.feedPerEvent);
    Serial.print("g End="); Serial.print(config.endHour);
    Serial.print(":"); Serial.print(config.endMinute);
    Serial.print(" Rate="); Serial.print(config.dischargeRate);
    Serial.print("g/s Start="); Serial.print(config.startHour);
    Serial.print(":"); Serial.println(config.startMinute);

    // ── MicroSD Card ──
    Serial.println("[INIT] MicroSD Card...");
    if (sdLog.begin()) {
        sysStatus.sdCardOK = true;
        Serial.println("[SD]   Card OK!");
        sdLog.logEvent("System boot — AquaFeeder AG_V1 v4.0.0");
    } else {
        sysStatus.sdCardOK = false;
        Serial.println("[SD]   Card not found (non-critical).");
    }

    // ── LoRa SX1262 ──
    Serial.println("[INIT] LoRa E22-900M22S (SX1262)...");
    if (loraMgr.begin()) {
        sysStatus.loraStatus = ConnStatus::DISCONNECTED;
        Serial.println("[LORA] SX1262 detected! Setting keys...");
        bool allZero = true;
        for (int i=0; i<8; i++) {
            if (config.loraDevEUI[i] != 0) { allZero = false; break; }
        }
        if (allZero) {
            const uint8_t defaultDevEUI[8] = { 0xE0, 0x72, 0xA1, 0xF6, 0x24, 0x9C, 0x00, 0x05 };
            const uint8_t defaultAppEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
            const uint8_t defaultAppKey[16] = { 
                0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6, 
                0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C 
            };
            memcpy(config.loraDevEUI, defaultDevEUI, 8);
            memcpy(config.loraAppEUI, defaultAppEUI, 8);
            memcpy(config.loraAppKey, defaultAppKey, 16);
            cfgMgr.saveConfig(config);
        }
        
        config.loraOTAA = false;
        if (loraMgr.join(config.loraDevEUI, config.loraAppEUI, config.loraAppKey)) {
            sysStatus.loraStatus = ConnStatus::CONNECTED;
            Serial.println("[LORA] LoRaWAN Session Join SUCCESS!");
        } else {
            sysStatus.loraStatus = ConnStatus::ERROR;
            Serial.println("[LORA] LoRaWAN Join failed — will retry later.");
        }
        
        loraMgr.setDownlinkCallback(cbOnDownlink);
    } else {
        sysStatus.loraStatus = ConnStatus::NOT_AVAILABLE;
        Serial.println("[LORA] SX1262 not detected (check SPI wiring).");
    }

    // ── SIM800L GSM ──
    Serial.println("[INIT] SIM800L GSM...");
    if (gsmMgr.begin()) {
        sysStatus.gsmStatus = ConnStatus::DISCONNECTED;
        int sig = gsmMgr.getSignalQuality();
        Serial.print("[GSM]  Modem OK! Signal: "); Serial.println(sig);
    } else {
        sysStatus.gsmStatus = ConnStatus::NOT_AVAILABLE;
        Serial.println("[GSM]  SIM800L not detected.");
    }

    // ── WiFi + Web Server ──
    Serial.println("[INIT] WiFi Manager...");
    wifiMgr.begin(config);
    wifiMgr.setStatusRef(&sysStatus);
    wifiMgr.setConfigRef(&config);
    wifiMgr.setCallbacks(cbOnFeedStart, cbOnFeedStop, cbOnSaveConfig, cbOnSaveNetwork);
    wifiMgr.setupWebServer(webServer);
    webServer.begin();
    sysStatus.wifiStatus = ConnStatus::CONNECTED;
    Serial.print("[WIFI] AP: "); Serial.print(config.apSSID);
    Serial.print(" IP: "); Serial.println(WiFi.softAPIP());

    // ── Feed Engine ──
    Serial.println("[INIT] Feed Engine...");
    feedEng.begin(&sysStatus, &config);
    feedEng.setRelayCallback(cbSetRelay);
    feedEng.setMotorsOffCallback(cbMotorsOff);
    feedEng.setTelemetryCallback(cbTelemetryEvent);
    feedEng.setCurrentReadCallback(cbReadCurrent);
    feedEng.calcSchedule();

    // ── Telemetry Manager ──
    Serial.println("[INIT] Telemetry Manager...");
    telMgr.begin(&sysStatus, &config);

    // ── Cloud Manager ──
    Serial.println("[INIT] Cloud Manager...");
    cloudMgr.begin(&sysStatus, &config);
    cloudMgr.setLoRa(&loraMgr);
    cloudMgr.setWiFi(&wifiMgr);
    cloudMgr.setGSM(gsmMgr.isAvailable() ? &gsmMgr : nullptr);
    cloudMgr.setSDLogger(sdLog.isOK() ? &sdLog : nullptr);
    cloudMgr.setTelemetry(&telMgr);

    // ── Motors OFF (safety) ──
    hal.motorsOff();

    // ── Run Hardware Diagnostics ──
    runHardwareDiagnostics();

    // ── Boot telemetry ──
    telMgr.queueEvent(TelemetryMsgType::DEVICE_BOOT);
    telMgr.queueEvent(TelemetryMsgType::SETTINGS_REPORT);

    // ── Init complete ──
    hal.setLedRed(false);
    
    bool hasCriticalError = !sysStatus.rtcOK;
    if (!hasCriticalError) {
        hal.setRgbLed(0, 128, 0); // Glows GREEN once booted up and everything is fine
        delay(2000);              // Glows for 2 seconds
        hal.setRgbLed(0, 0, 0);   // Turns OFF
    } else {
        hal.setRgbLed(128, 0, 0); // Glows RED if any error
    }
    hal.blinkGreen(3, 200);  // 3 blinks = boot OK
    Serial.println("\n[OK] Initialization complete! Type H for help.\n");

    // ── Create FreeRTOS Task for Cloud / LoRa ──
    xTaskCreatePinnedToCore(
        cloudTask,       // Task function
        "CloudTask",     // Name
        8192,            // Stack size (bytes)
        NULL,            // Parameters
        1,               // Priority
        NULL,            // Task handle
        0                // Core 0 (Main loop runs on Core 1)
    );

    // Start on status screen or AP config if first boot
    currentMenu = firstBoot ? MenuState::MAIN_STATUS : MenuState::MAIN_STATUS;
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════════════════════

void loop() {
    unsigned long nowMs = millis();

    // ── 1. Password-Protected Technician Serial CLI ──
    static bool techAuthenticated = false;
    static unsigned long authExpiryMs = 0;
    
    if (techAuthenticated && nowMs > authExpiryMs) {
        techAuthenticated = false;
        Serial.println("\n[SEC] Technician session expired. Enter 'AUTH <PIN>' to unlock.");
    }
    
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        if (input.length() > 0) {
            String upper = input;
            upper.toUpperCase();
            
            if (upper.startsWith("AUTH ")) {
                String pin = input.substring(5);
                pin.trim();
                if (pin == "8888" || pin == "athena2026") {
                    techAuthenticated = true;
                    authExpiryMs = nowMs + (15 * 60 * 1000UL); // 15 min session
                    Serial.println("\n[SUCCESS] Technician authenticated! Session active for 15 mins.");
                    Serial.println("Commands unlocked: DIAG, TEST MOTOR 1|2, TEST LORA, TEST GSM, SET ID <serial>");
                } else {
                    Serial.println("\n[REJECTED] Invalid Technician PIN.");
                }
            } else if (upper == "DIAG" || upper == "D") {
                runHardwareDiagnostics();
            } else if (upper == "REBOOT" || upper == "R") {
                Serial.println("[SYS] Rebooting controller...");
                delay(200);
                ESP.restart();
            } else if (upper.startsWith("TEST MOTOR ")) {
                if (!techAuthenticated) {
                    Serial.println("[REJECTED] Locked! Enter 'AUTH <PIN>' first.");
                } else {
                    int motorNum = upper.substring(11).toInt();
                    if (motorNum == 1) {
                        Serial.println("[TEST] Running Loader Motor (Relay 1) for 2s...");
                        hal.setRelay(1, true);
                        delay(2000);
                        hal.setRelay(1, false);
                        Serial.println("[TEST] Motor 1 Test COMPLETE.");
                    } else if (motorNum == 2) {
                        Serial.println("[TEST] Running Dispenser Motor (Relay 2) for 2s...");
                        hal.setRelay(2, true);
                        delay(2000);
                        hal.setRelay(2, false);
                        Serial.println("[TEST] Motor 2 Test COMPLETE.");
                    } else {
                        Serial.println("[ERROR] Usage: TEST MOTOR 1  or  TEST MOTOR 2");
                    }
                }
            } else if (upper.startsWith("SET ID ")) {
                if (!techAuthenticated) {
                    Serial.println("[REJECTED] Locked! Enter 'AUTH <PIN>' first.");
                } else {
                    String newId = input.substring(7);
                    newId.trim();
                    if (newId.length() >= 3 && newId.length() < 32) {
                        newId.toCharArray(config.deviceId, sizeof(config.deviceId));
                        cfgMgr.saveConfig(config);
                        Serial.printf("[SUCCESS] Serial Device ID set to: '%s'\n", config.deviceId);
                    } else {
                        Serial.println("[ERROR] Invalid Serial ID. Must be 3-30 chars.");
                    }
                }
            } else if (upper == "GET LORA" || upper == "EUI") {
                if (!techAuthenticated) {
                    Serial.println("[REJECTED] Locked! Enter 'AUTH <PIN>' first.");
                } else {
                    Serial.println("\n[LORA CREDENTIALS (OTAA)]");
                    Serial.print("  DevEUI  : "); 
                    for(int i=0; i<8; i++) Serial.printf("%02X", config.loraDevEUI[i]);
                    Serial.println();
                    
                    Serial.print("  AppEUI  : "); 
                    for(int i=0; i<8; i++) Serial.printf("%02X", config.loraAppEUI[i]);
                    Serial.println();
                    
                    Serial.print("  AppKey  : "); 
                    for(int i=0; i<16; i++) Serial.printf("%02X", config.loraAppKey[i]);
                    Serial.println("\n");
                }
            } else if (upper == "HELP" || upper == "H" || upper == "?") {
                Serial.println("\n══════════ AG_V1 TECHNICIAN SERIAL CLI ══════════");
                Serial.printf("  Device Serial ID : %s\n", config.deviceId);
                Serial.printf("  Auth Status      : %s\n", techAuthenticated ? "UNLOCKED" : "LOCKED");
                Serial.println("  --------------------------------------------------");
                Serial.println("  AUTH <PIN>         : Unlock Technician CLI (PIN: 8888)");
                Serial.println("  DIAG               : Run 9-Point Hardware Diagnostic Scan");
                Serial.println("  TEST MOTOR 1|2     : Pulse Motor 1 or 2 for 2 Seconds");
                Serial.println("  SET ID <SERIAL_ID> : Set Permanent Enclosure Serial ID");
                Serial.println("  GET LORA           : Print LoRaWAN ABP Credentials for AWS");
                Serial.println("  REBOOT             : Soft Reset ESP32 Controller");
                Serial.println("  HELP               : Print CLI Command Menu");
                Serial.println("═══════════════════════════════════════════════════\n");
            }
        }
    }

    // ── 2. Web Server ──
    webServer.handleClient();

    // ── 3. Button Scanning ──
    hal.updateButtons();

    // ── 4. Button Navigation ──
    handleButtonNavigation();

    // ── 5. Proximity Check ──
    if (sysStatus.feedActive && currentMenu == MenuState::RUNNING) {
        if (hal.isProximityTriggered()) {
            feedEng.pauseFeed();
            currentMenu = MenuState::PAUSED;
            hal.setHooter(true);
            telMgr.queueEvent(TelemetryMsgType::ALARM_PROXIMITY);
            Serial.println("[!] PROXIMITY PAUSE!");
        }
    }

    // ── 6. Feed Engine State Machine ──
    uint32_t epoch = sysStatus.rtcOK ? rtcMgr.getEpoch() : 0;
    feedEng.update(nowMs, epoch);

    // Check if feed engine transitioned to finished
    if (!sysStatus.feedActive && currentMenu == MenuState::RUNNING) {
        currentMenu = MenuState::FINISHED;
    }

    // ── 7. Auto-Start Scheduled Feed ──
    if (sysStatus.rtcOK && !sysStatus.feedActive && currentMenu != MenuState::PAUSED) {
        if (feedEng.shouldAutoStart(epoch)) {
            feedEng.startFeed();
            currentMenu = MenuState::RUNNING;
            telMgr.queueEvent(TelemetryMsgType::FEED_STARTED);
            Serial.println("[SCHED] Auto-start triggered!");
        }
    }

    // ── 8. INA219 Overcurrent Check ──
    if (sysStatus.feedActive && sysStatus.feedState == FeedCycleState::FC_DISP) {
        if (nowMs - lastPowerReadMs >= INA219_SAMPLE_MS) {
            lastPowerReadMs = nowMs;
            pwrMon.update();
            sysStatus.currentMA = pwrMon.getCurrent();
            sysStatus.voltageV  = pwrMon.getVoltage();
            sysStatus.powerMW   = pwrMon.getPower();

            if (pwrMon.isOvercurrent(config.overcurrentLimit)) {
                feedEng.pauseFeed();
                currentMenu = MenuState::PAUSED;
                hal.setLedRed(true);
                hal.setHooter(true);
                delay(1000);
                hal.setHooter(false);
                telMgr.queueEvent(TelemetryMsgType::ALARM_OVERCURRENT);
                Serial.println("[!!] OVERCURRENT DETECTED! Motors stopped.");
            }
        }
    }

    // ── 9. Periodic Power Reading (when not dispensing) ──
    if (nowMs - lastPowerReadMs >= POWER_READ_INTERVAL_MS) {
        lastPowerReadMs = nowMs;
        if (pwrMon.isOK()) {
            pwrMon.update();
            sysStatus.voltageV  = pwrMon.getVoltage();
            sysStatus.currentMA = pwrMon.getCurrent();
            sysStatus.powerMW   = pwrMon.getPower();
        }
    }

    // ── 10. Telemetry Periodic Check ──
    telMgr.update(nowMs);

    // ── 11. Cloud and LoRa processing moved to FreeRTOS CloudTask on Core 0 ──
    
    // ── 13. GSM Processing ──
    if (gsmMgr.isAvailable()) {
        gsmMgr.loop();
    }

    // ── 14. Update System Status ──
    updateSystemStatus();

    // ── 15. LCD Render ──
    lcd.update(sysStatus, config, currentMenu, menuCursorIdx, editVal, editFld);

    // ── 16. Heartbeat LED ──
    hal.heartbeatTick();

    // ── 18. Status LED Indicators ──
    // Red LED: ON if any error condition
    if (!sysStatus.feedActive) {
        bool hasError = !sysStatus.rtcOK || !sysStatus.scheduleValid;
        hal.setLedRed(hasError);
    }
}
