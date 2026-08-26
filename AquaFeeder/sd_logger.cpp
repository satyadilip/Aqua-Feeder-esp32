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
    
    readIndex = 0;
    writeIndex = 0;
    loadIndices();
    
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

bool SDLogger::queueTelemetry(const TelemetryEvent& event) {
    if (!statusOK) return false;
    prepareSPI();
    
    File file = SD.open(SD_QUEUE_FILE, FILE_APPEND);
    if (!file) return false;
    
    size_t written = file.write((const uint8_t*)&event, sizeof(TelemetryEvent));
    file.close();
    
    if (written == sizeof(TelemetryEvent)) {
        writeIndex++;
        saveIndices();
        return true;
    }
    return false;
}

bool SDLogger::hasQueuedTelemetry() {
    if (!statusOK) return false;
    return readIndex < writeIndex;
}

int SDLogger::readQueuedTelemetry(TelemetryEvent* buf, int maxCount) {
    if (!statusOK || readIndex >= writeIndex) return 0;
    prepareSPI();
    
    File file = SD.open(SD_QUEUE_FILE, FILE_READ);
    if (!file) return 0;
    
    uint32_t offset = readIndex * sizeof(TelemetryEvent);
    if (!file.seek(offset)) {
        file.close();
        return 0;
    }
    
    int count = 0;
    while (count < maxCount && file.available() >= sizeof(TelemetryEvent) && (readIndex + count) < writeIndex) {
        if (file.read((uint8_t*)&buf[count], sizeof(TelemetryEvent)) == sizeof(TelemetryEvent)) {
            count++;
        } else {
            break;
        }
    }
    file.close();
    return count;
}

void SDLogger::markSent(int count) {
    if (count <= 0 || !statusOK) return;
    readIndex += count;
    if (readIndex > writeIndex) readIndex = writeIndex;
    
    // If we've caught up completely, we can truncate the file to save space
    if (readIndex == writeIndex) {
        prepareSPI();
        SD.remove(SD_QUEUE_FILE);
        readIndex = 0;
        writeIndex = 0;
    }
    saveIndices();
}

void SDLogger::loadIndices() {
    if (!statusOK) return;
    prepareSPI();
    
    File file = SD.open(SD_QUEUE_IDX, FILE_READ);
    if (file && file.size() == 8) {
        file.read((uint8_t*)&readIndex, 4);
        file.read((uint8_t*)&writeIndex, 4);
        file.close();
    } else {
        if (file) file.close();
        // Try to recover writeIndex from file size
        File qFile = SD.open(SD_QUEUE_FILE, FILE_READ);
        if (qFile) {
            writeIndex = qFile.size() / sizeof(TelemetryEvent);
            readIndex = 0;
            qFile.close();
        } else {
            readIndex = 0;
            writeIndex = 0;
        }
    }
}

void SDLogger::saveIndices() {
    if (!statusOK) return;
    prepareSPI();
    
    File file = SD.open(SD_QUEUE_IDX, FILE_WRITE);
    if (file) {
        file.write((const uint8_t*)&readIndex, 4);
        file.write((const uint8_t*)&writeIndex, 4);
        file.close();
    }
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
