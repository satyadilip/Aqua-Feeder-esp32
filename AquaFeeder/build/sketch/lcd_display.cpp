#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\lcd_display.cpp"
#include "lcd_display.h"
#include <Wire.h>

LCDDisplay::LCDDisplay() 
    : lcd(nullptr), lcdOK(false), prevMenuState((MenuState)255), 
      lastUpdateMs(0), msgClearMs(0), showingMsg(false) {}

bool LCDDisplay::begin() {
    Wire.begin();
    
    // Check primary address
    Wire.beginTransmission(I2C_ADDR_LCD_PRIMARY);
    if (Wire.endTransmission() == 0) {
        lcd = new LiquidCrystal_I2C(I2C_ADDR_LCD_PRIMARY, LCD_COLS, LCD_ROWS);
    } else {
        // Check alternate address
        Wire.beginTransmission(I2C_ADDR_LCD_ALT);
        if (Wire.endTransmission() == 0) {
            lcd = new LiquidCrystal_I2C(I2C_ADDR_LCD_ALT, LCD_COLS, LCD_ROWS);
        }
    }
    
    if (lcd == nullptr) {
        Serial.println("[LCD] Error: Display not found on I2C bus");
        return false;
    }
    
    lcd->init();
    lcd->backlight();
    lcdOK = true;
    
    // Create custom smooth progress bar characters (5 sub-pixel fill levels)
    uint8_t barChar[5][8] = {
        { 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10 }, // 1/5 fill
        { 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18 }, // 2/5 fill
        { 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C }, // 3/5 fill
        { 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E }, // 4/5 fill
        { 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F }  // 5/5 solid block
    };
    for (int i = 0; i < 5; i++) {
        lcd->createChar(i, barChar[i]);
    }
    
    Serial.println("[LCD] Display initialized successfully");
    showSplash();
    
    return true;
}

bool LCDDisplay::isOK() {
    return lcdOK;
}

void LCDDisplay::showSplash() {
    if (!lcdOK) return;
    lcd->clear();
    lcd->setCursor(0, 0);
    lcd->print("====================");
    lcd->setCursor(0, 1);
    lcd->print("  Aqua Feeder v4.0  ");
    lcd->setCursor(0, 2);
    lcd->print(" Athena Engineering ");
    lcd->setCursor(0, 3);
    lcd->print("====================");
    delay(2000);
    lcd->clear();
}

void LCDDisplay::showError(const char* line1, const char* line2) {
    if (!lcdOK) return;
    lcd->clear();
    lcd->setCursor(0, 0);
    lcd->print("=== SYSTEM ALARM ===");
    lcd->setCursor(0, 1);
    lcd->print(line1);
    lcd->setCursor(0, 2);
    lcd->print(line2);
    lcd->setCursor(0, 3);
    lcd->print("Press [SEL] to Reset");
}

void LCDDisplay::showMessage(const char* line1, const char* line2, int durationMs) {
    if (!lcdOK) return;
    lcd->clear();
    lcd->setCursor(0, 1);
    lcd->print(line1);
    lcd->setCursor(0, 2);
    lcd->print(line2);
    
    showingMsg = true;
    msgClearMs = millis() + durationMs;
}

void LCDDisplay::setBacklight(bool on) {
    if (!lcdOK) return;
    if (on) lcd->backlight();
    else lcd->noBacklight();
}

const char* LCDDisplay::getConnStatusStr(ConnStatus s) {
    switch(s) {
        case ConnStatus::CONNECTED: return "OK";
        case ConnStatus::CONNECTING: return "CN";
        case ConnStatus::ERROR: return "ER";
        case ConnStatus::DISCONNECTED: return "DC";
        default: return "--";
    }
}

void LCDDisplay::drawProgressBar(int row, float percent) {
    if (percent < 0.0f) percent = 0.0f;
    if (percent > 100.0f) percent = 100.0f;
    
    lcd->setCursor(0, row);
    lcd->print("[");
    
    // 18 chars total -> 16 bar slots inside brackets
    int totalSubPixels = round((percent / 100.0f) * 80.0f); // 16 * 5 = 80 sub-pixels
    int fullChars = totalSubPixels / 5;
    int remainder = totalSubPixels % 5;
    
    for (int i = 0; i < 16; i++) {
        if (i < fullChars) {
            lcd->write((uint8_t)4); // Solid block
        } else if (i == fullChars && remainder > 0) {
            lcd->write((uint8_t)(remainder - 1)); // Partial sub-pixel block
        } else {
            lcd->print(" ");
        }
    }
    lcd->print("]");
}

void LCDDisplay::update(const SystemStatus& status, const DeviceConfig& cfg, MenuState menuState, int menuCursor, int editValue, int editField) {
    if (!lcdOK) return;
    
    unsigned long now = millis();
    
    if (showingMsg) {
        if (now < msgClearMs) return; // Keep showing message
        showingMsg = false;
        prevMenuState = (MenuState)255; // Force full redraw
    }
    
    // Limit update rate to 4Hz (250ms) to prevent flicker
    if (now - lastUpdateMs < 250) return;
    lastUpdateMs = now;
    
    if (menuState != prevMenuState) {
        lcd->clear();
        prevMenuState = menuState;
    }
    
    switch (menuState) {
        case MenuState::MAIN_STATUS: drawMainStatus(status); break;
        case MenuState::MENU_LIST: drawMenuList(menuCursor); break;
        case MenuState::EDIT_QTY: drawEditQty(editValue); break;
        case MenuState::EDIT_FPE: drawEditFPE(editValue); break;
        case MenuState::EDIT_TIME: drawEditTime(editValue); break;
        case MenuState::EDIT_START_TIME: drawEditStartTime(editValue, editField); break;
        case MenuState::EDIT_RATE: drawEditRate(editValue); break;
        case MenuState::EDIT_CLOCK: drawEditClock(status, editValue, editField); break;
        case MenuState::RUNNING: drawRunning(status); break;
        case MenuState::PAUSED: drawPaused(status); break;
        case MenuState::FINISHED: drawFinished(status); break;
        case MenuState::INFO_NETWORK: drawNetworkInfo(status); break;
        case MenuState::INFO_POWER: drawPowerInfo(status); break;
    }
}

void LCDDisplay::drawMainStatus(const SystemStatus& status) {
    char buf[21];
    
    // Line 1: AquaFeeder + Live Formatted RTC Date & Time
    lcd->setCursor(0, 0);
    if (status.rtcOK && status.currentEpoch > 100000) {
        uint32_t secs = status.currentEpoch % 86400;
        int hh = secs / 3600;
        int mm = (secs % 3600) / 60;
        int ss = secs % 60;
        snprintf(buf, sizeof(buf), "AquaFeeder  %02d:%02d:%02d", hh, mm, ss);
    } else {
        snprintf(buf, sizeof(buf), "AquaFeeder  NO-CLOCK");
    }
    lcd->print(buf);
    
    // Line 2: Machine State
    lcd->setCursor(0, 1);
    const char* stStr = "SYSTEM READY ";
    if (status.feedActive) {
        if (status.feedState == FeedCycleState::FC_DISP) stStr = "DISPENSING   ";
        else if (status.feedState == FeedCycleState::FC_PRE) stStr = "WARM-UP      ";
        else if (status.feedState == FeedCycleState::FC_POST) stStr = "POST-CLEAR   ";
        else if (status.feedState == FeedCycleState::FC_WAIT) stStr = "GAP DELAY    ";
    } else if (status.state == SystemState::FEED_PAUSED) {
        stStr = "FEED PAUSED  ";
    }
    snprintf(buf, sizeof(buf), "State: %-13s", stStr);
    lcd->print(buf);
    
    // Line 3: Event / Gap details
    lcd->setCursor(0, 2);
    if (status.feedActive) {
        if (status.feedState == FeedCycleState::FC_WAIT) {
            long remSec = status.nextFeedEpoch > status.currentEpoch ? (status.nextFeedEpoch - status.currentEpoch) : 0;
            snprintf(buf, sizeof(buf), "Evt:%d/%-3ld NEXT:%lds  ", status.currentEvent, status.totalEvents, remSec);
        } else {
            snprintf(buf, sizeof(buf), "Evt:%d/%-3ld FEEDING   ", status.currentEvent, status.totalEvents);
        }
    } else {
        snprintf(buf, sizeof(buf), "Press [SEL] for Menu");
    }
    lcd->print(buf);
    
    // Line 4: Clean Network Connectivity Indicators
    lcd->setCursor(0, 3);
    snprintf(buf, sizeof(buf), "LoRa:%-2s WiFi:%-2s GSM:%-2s", 
        getConnStatusStr(status.loraStatus), 
        getConnStatusStr(status.wifiStatus), 
        getConnStatusStr(status.gsmStatus));
    lcd->print(buf);
}

void LCDDisplay::drawMenuList(int menuCursor) {
    const char* items[] = {
        "Feed Quantity", 
        "Feed Per Event", 
        "Duration Window", 
        "Start Time", 
        "Discharge Rate", 
        "Set Real Clock", 
        "Start Feeding", 
        "Network Info", 
        "Power Monitor"
    };
    int totalItems = 9;
    
    int startIdx = (menuCursor / 4) * 4;
    
    for (int i = 0; i < 4; i++) {
        lcd->setCursor(0, i);
        int itemIdx = startIdx + i;
        if (itemIdx < totalItems) {
            char buf[21];
            if (itemIdx == menuCursor) {
                snprintf(buf, sizeof(buf), "> %-18s", items[itemIdx]);
            } else {
                snprintf(buf, sizeof(buf), "  %-18s", items[itemIdx]);
            }
            lcd->print(buf);
        } else {
            lcd->print("                    ");
        }
    }
}

void LCDDisplay::drawEditQty(int editValue) {
    lcd->setCursor(0, 0);
    lcd->print("=== FEED QUANTITY ==");
    
    char buf[21];
    float val = editValue / 10.0f; // editValue is 10x kg
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), "   Target: %5.1f Kg ", val);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Save");
}

void LCDDisplay::drawEditFPE(int editValue) {
    lcd->setCursor(0, 0);
    lcd->print("== FEED PER EVENT ==");
    
    char buf[21];
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), "   Amount: %4d g   ", editValue);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Save");
}

void LCDDisplay::drawEditTime(int editValue) {
    lcd->setCursor(0, 0);
    lcd->print("== FEED DURATION ===");
    
    char buf[21];
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), "   Window: %2d Hours ", editValue);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Save");
}

void LCDDisplay::drawEditStartTime(int editValue, int editField) {
    lcd->setCursor(0, 0);
    lcd->print("==== START TIME ====");
    
    int hh = editValue / 100;
    int mm = editValue % 100;
    
    char buf[21];
    lcd->setCursor(0, 1);
    if (editField == 0) {
        snprintf(buf, sizeof(buf), "    Time: [%02d]:%02d   ", hh, mm);
    } else {
        snprintf(buf, sizeof(buf), "    Time:  %02d:[%02d]  ", hh, mm);
    }
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Next");
}

void LCDDisplay::drawEditRate(int editValue) {
    lcd->setCursor(0, 0);
    lcd->print("== DISCHARGE RATE ==");
    
    char buf[21];
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), "   Rate: %3d g/sec  ", editValue);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Save");
}

void LCDDisplay::drawEditClock(const SystemStatus& status, int editValue, int editField) {
    lcd->setCursor(0, 0);
    lcd->print("==== SET RTC CLOCK ===");
    
    int hh = editValue / 100;
    int mm = editValue % 100;
    
    char buf[21];
    lcd->setCursor(0, 1);
    if (editField == 0) {
        snprintf(buf, sizeof(buf), "    Clock: [%02d]:%02d  ", hh, mm);
    } else {
        snprintf(buf, sizeof(buf), "    Clock:  %02d:[%02d] ", hh, mm);
    }
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print("                    ");
    
    lcd->setCursor(0, 3);
    lcd->print("\x7E\x7F: Adjust  [SEL]: Next");
}

void LCDDisplay::drawRunning(const SystemStatus& status) {
    char buf[21];
    
    // Line 1: Header + Event Counter
    lcd->setCursor(0, 0);
    snprintf(buf, sizeof(buf), "AquaFeeder  Evt:%d/%ld", status.currentEvent, status.totalEvents);
    lcd->print(buf);
    
    // Line 2: Stage & Gap Timer
    lcd->setCursor(0, 1);
    if (status.feedState == FeedCycleState::FC_PRE) {
        snprintf(buf, sizeof(buf), "Stage: PRE-WARMUP   ");
    } else if (status.feedState == FeedCycleState::FC_DISP) {
        snprintf(buf, sizeof(buf), "Stage: DISPENSING   ");
    } else if (status.feedState == FeedCycleState::FC_POST) {
        snprintf(buf, sizeof(buf), "Stage: POST-CLEAR   ");
    } else if (status.feedState == FeedCycleState::FC_WAIT) {
        long remSec = status.nextFeedEpoch > status.currentEpoch ? (status.nextFeedEpoch - status.currentEpoch) : 0;
        snprintf(buf, sizeof(buf), "Stage: GAP DELAY %lds ", remSec);
    } else {
        snprintf(buf, sizeof(buf), "Stage: IDLE         ");
    }
    lcd->print(buf);
    
    // Line 3: Smooth Progress Bar (Gap countdown fill or Overall Feed Cycle fill)
    float pct = 0.0f;
    if (status.feedState == FeedCycleState::FC_WAIT) {
        // Gap countdown progress bar matching remaining delay
        long totalGapSec = status.intervalMs / 1000;
        if (totalGapSec <= 0) totalGapSec = 1;
        long remSec = status.nextFeedEpoch > status.currentEpoch ? (status.nextFeedEpoch - status.currentEpoch) : 0;
        long elapsedSec = totalGapSec > remSec ? (totalGapSec - remSec) : 0;
        pct = (float(elapsedSec) / float(totalGapSec)) * 100.0f;
    } else {
        // Overall Feed Cycle Progress
        if (status.totalEvents > 0) {
            pct = (float(status.currentEvent) / float(status.totalEvents)) * 100.0f;
        }
    }
    drawProgressBar(2, pct);
    
    // Line 4: Clear Emergency Stop Instruction (fits 20 chars)
    lcd->setCursor(0, 3);
    lcd->print("[SEL]: Press to STOP");
}

void LCDDisplay::drawPaused(const SystemStatus& status) {
    lcd->setCursor(0, 0);
    lcd->print("=== FEED PAUSED ===");
    
    lcd->setCursor(0, 1);
    if (status.proximityTriggered) {
        lcd->print("Reason: CHUTE BLOCKED");
    } else if (status.currentMA > OVERCURRENT_LIMIT_MA) {
        lcd->print("Reason: OVERCURRENT ");
    } else {
        lcd->print("Reason: MANUAL STOP ");
    }
    
    lcd->setCursor(0, 2);
    lcd->print("Press [SEL] to Resume");
    
    lcd->setCursor(0, 3);
    lcd->print("Press [BACK] to Cancel");
}

void LCDDisplay::drawFinished(const SystemStatus& status) {
    lcd->setCursor(0, 0);
    lcd->print("== CYCLE COMPLETE ==");
    
    char buf[21];
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), " Events Done: %-4ld  ", status.totalEvents);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    lcd->print(" All Dispensed OK!  ");
    
    lcd->setCursor(0, 3);
    lcd->print("Press [SEL] for Menu");
}

void LCDDisplay::drawNetworkInfo(const SystemStatus& status) {
    char buf[21];
    
    lcd->setCursor(0, 0);
    lcd->print("=== NETWORK INFO ===");
    
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), "LoRaWAN: %-11s", getConnStatusStr(status.loraStatus));
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    snprintf(buf, sizeof(buf), "WiFi AP: %-11s", getConnStatusStr(status.wifiStatus));
    lcd->print(buf);
    
    lcd->setCursor(0, 3);
    snprintf(buf, sizeof(buf), "GSM Cell:%-11s", getConnStatusStr(status.gsmStatus));
    lcd->print(buf);
}

void LCDDisplay::drawPowerInfo(const SystemStatus& status) {
    char buf[21];
    
    lcd->setCursor(0, 0);
    lcd->print("=== POWER MONITOR ==");
    
    lcd->setCursor(0, 1);
    snprintf(buf, sizeof(buf), " Voltage: %5.2f V    ", status.voltageV);
    lcd->print(buf);
    
    lcd->setCursor(0, 2);
    snprintf(buf, sizeof(buf), " Current: %5.0f mA   ", status.currentMA);
    lcd->print(buf);
    
    lcd->setCursor(0, 3);
    snprintf(buf, sizeof(buf), " Power:   %5.0f mW   ", status.powerMW);
    lcd->print(buf);
}

