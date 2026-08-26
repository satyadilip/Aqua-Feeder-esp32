#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\sd_logger.cpp"
#include "sd_logger.h"

void SDLogger::prepareSPI() {
    // Ensure LoRa SPI CS is inactive so it doesn't interfere
    digitalWrite(PIN_LORA_NSS, HIGH);
}

bool SDLogger::begin() {
    pinMode(PIN_LORA_NSS, OUTPUT);
    digitalWrite(PIN_LORA_NSS, HIGH);
    
    statusOK = SD.begin(PIN_SD_CS);
    if (!statusOK) {
        Serial.println("[SD] Failed to initialize SD card");
        return false;
    }
    
    ensureDir(SD_LOG_DIR);
    Serial.println("[SD] Initialized successfully");
    return true;
}

bool SDLogger::isOK() {
    return statusOK;
}

void SDLogger::ensureDir(const char* dir) {
    if (!SD.exists(dir)) {
        SD.mkdir(dir);
    }
}

bool SDLogger::logTelemetry(const TelemetryEvent& event) {
    if (!statusOK) return false;
    prepareSPI();
    rotateIfNeeded();
    
    File file = SD.open(SD_TELEMETRY_FILE, FILE_APPEND);
    if (!file) {
        Serial.println("[SD] Failed to open telemetry log");
        return false;
    }
    
    // format: timestamp,msgType,voltage_mV,current_mA,feedDispensed_g,currentEvent,totalEvents,statusFlags,sent
    file.print(event.timestamp); file.print(",");
    file.print((uint8_t)event.type); file.print(",");
    file.print(event.voltage_mV); file.print(",");
    file.print(event.current_mA); file.print(",");
    file.print(event.feedDispensed_g); file.print(",");
    file.print(event.currentEvent); file.print(",");
    file.print(event.totalEvents); file.print(",");
    file.print(event.statusFlags); file.print(",");
    file.println(event.sent ? "1" : "0");
    
    file.close();
    return true;
}

bool SDLogger::logEvent(const char* msg) {
    if (!statusOK) return false;
    prepareSPI();
    
    File file = SD.open(SD_EVENT_FILE, FILE_APPEND);
    if (!file) {
        Serial.println("[SD] Failed to open event log");
        return false;
    }
    
    file.println(msg);
    file.close();
    return true;
}

bool SDLogger::hasQueuedTelemetry() {
    if (!statusOK) return false;
    prepareSPI();
    
    File file = SD.open(SD_TELEMETRY_FILE, FILE_READ);
    if (!file) return false;
    
    bool hasUnsent = false;
    while(file.available()) {
        String line = file.readStringUntil('\n');
        if (line.endsWith(",0\r") || line.endsWith(",0")) {
            hasUnsent = true;
            break;
        }
    }
    file.close();
    return hasUnsent;
}

int SDLogger::readQueuedTelemetry(TelemetryEvent* buf, int maxCount) {
    // Simplified stub
    return 0;
}

void SDLogger::markSent(int count) {
    // Simplified stub
}

uint32_t SDLogger::getUsedKB() {
    if (!statusOK) return 0;
    prepareSPI();
    return (uint32_t)(SD.usedBytes() / 1024);
}

void SDLogger::rotateIfNeeded() {
    if (!statusOK) return;
    prepareSPI();
    
    File file = SD.open(SD_TELEMETRY_FILE, FILE_READ);
    if (file) {
        size_t size = file.size();
        file.close();
        
        if (size > (SD_MAX_FILE_SIZE_KB * 1024)) {
            Serial.println("[SD] Rotating telemetry file");
            SD.remove("/logs/telemetry.bak");
            SD.rename(SD_TELEMETRY_FILE, "/logs/telemetry.bak");
        }
    }
}
