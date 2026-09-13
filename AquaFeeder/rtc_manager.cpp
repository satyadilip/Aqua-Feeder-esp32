#include "rtc_manager.h"

bool RTCManager::begin() {
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
        return false;
    }
    
    if (rtc.lostPower()) {
        Serial.println("[RTC] RTC lost power, syncing with build time...");
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    } else {
        Serial.println("[RTC] RTC retains time, skipping sync.");
    }
    
    Serial.println("[RTC] Initialized successfully");
    return true;
}

bool RTCManager::isOK() {
    return statusOK;
}

DateTime RTCManager::getNow() {
    if (!statusOK) return DateTime(2026, 8, 23, 0, 0, 0);
    return rtc.now();
}

uint32_t RTCManager::getEpoch() {
    if (!statusOK) return 0;
    return rtc.now().unixtime();
}

void RTCManager::getTime(int& h, int& m, int& s) {
    if (!statusOK) { h=0; m=0; s=0; return; }
    DateTime now = rtc.now();
    h = now.hour();
    m = now.minute();
    s = now.second();
}

void RTCManager::getDate(int& y, int& mo, int& d) {
    if (!statusOK) { y=0; mo=0; d=0; return; }
    DateTime now = rtc.now();
    y = now.year();
    mo = now.month();
    d = now.day();
}

String RTCManager::getTimeStr() {
    if (!statusOK) return "00:00:00";
    DateTime now = rtc.now();
    char buf[9];
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d", now.hour(), now.minute(), now.second());
    return String(buf);
}

String RTCManager::getDateTimeStr() {
    if (!statusOK) return "2026-08-23 00:00:00";
    DateTime now = rtc.now();
    char buf[20];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d", 
             now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second());
    return String(buf);
}

void RTCManager::setTime(int h, int m, int s) {
    if (!statusOK) return;
    DateTime now = rtc.now();
    rtc.adjust(DateTime(now.year(), now.month(), now.day(), h, m, s));
    Serial.println("[RTC] Time updated");
}

void RTCManager::setDateTime(int y, int mo, int d, int h, int m, int s) {
    if (!statusOK) return;
    rtc.adjust(DateTime(y, mo, d, h, m, s));
    Serial.println("[RTC] Date & Time updated");
}

float RTCManager::getTemperature() {
    if (!statusOK) return 0.0f;
    return rtc.getTemperature();
}
