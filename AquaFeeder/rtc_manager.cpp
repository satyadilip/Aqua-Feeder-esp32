#include "rtc_manager.h"

bool RTCManager::begin() {
    // Initialize Software RTC fallback from compilation date & time
    DateTime buildDT(F(__DATE__), F(__TIME__));
    softBaseEpoch = buildDT.unixtime();
    softBaseMs = millis();

    statusOK = false;
    for (int i = 0; i < 3; i++) {
        if (rtc.begin()) {
            statusOK = true;
            break;
        }
        delay(100);
    }
    
    if (!statusOK) {
        Serial.println("[RTC] Failed to find DS3231 RTC");
        Serial.printf("[RTC] Software RTC active: %s (epoch: %lu)\n", 
                      getDateTimeStr().c_str(), softBaseEpoch);
        return false;
    }
    
    if (rtc.lostPower()) {
        Serial.println("[RTC] RTC lost power, syncing with build time...");
        rtc.adjust(buildDT);
    } else {
        Serial.println("[RTC] RTC retains time, skipping sync.");
    }
    
    softBaseEpoch = rtc.now().unixtime();
    softBaseMs = millis();

    Serial.println("[RTC] Initialized successfully");
    return true;
}

bool RTCManager::isOK() {
    return statusOK;
}

DateTime RTCManager::getNow() {
    if (statusOK) {
        return rtc.now();
    }
    uint32_t currentSec = softBaseEpoch + ((millis() - softBaseMs) / 1000UL);
    return DateTime(currentSec);
}

uint32_t RTCManager::getEpoch() {
    if (statusOK) {
        return rtc.now().unixtime();
    }
    return softBaseEpoch + ((millis() - softBaseMs) / 1000UL);
}

void RTCManager::getTime(int& h, int& m, int& s) {
    DateTime now = getNow();
    h = now.hour();
    m = now.minute();
    s = now.second();
}

void RTCManager::getDate(int& y, int& mo, int& d) {
    DateTime now = getNow();
    y = now.year();
    mo = now.month();
    d = now.day();
}

String RTCManager::getTimeStr() {
    DateTime now = getNow();
    char buf[9];
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d", now.hour(), now.minute(), now.second());
    return String(buf);
}

String RTCManager::getDateTimeStr() {
    DateTime now = getNow();
    char buf[20];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d", 
             now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second());
    return String(buf);
}

void RTCManager::setTime(int h, int m, int s) {
    DateTime now = getNow();
    DateTime updated(now.year(), now.month(), now.day(), h, m, s);
    if (statusOK) {
        rtc.adjust(updated);
    }
    softBaseEpoch = updated.unixtime();
    softBaseMs = millis();
    Serial.println("[RTC] Time updated");
}

void RTCManager::setDateTime(int y, int mo, int d, int h, int m, int s) {
    DateTime updated(y, mo, d, h, m, s);
    if (statusOK) {
        rtc.adjust(updated);
    }
    softBaseEpoch = updated.unixtime();
    softBaseMs = millis();
    Serial.println("[RTC] Date & Time updated");
}

void RTCManager::setEpoch(uint32_t epoch) {
    if (statusOK) {
        rtc.adjust(DateTime(epoch));
    }
    softBaseEpoch = epoch;
    softBaseMs = millis();
    Serial.println("[RTC] Epoch updated");
}

float RTCManager::getTemperature() {
    if (!statusOK) return 25.0f;
    return rtc.getTemperature();
}
