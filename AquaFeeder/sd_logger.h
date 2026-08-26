#pragma once
#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include "config.h"

class SDLogger {
public:
    bool begin();
    bool isOK();
    
    // Legacy CSV logging (for human reading)
    bool logTelemetry(const TelemetryEvent& event);
    bool logEvent(const char* msg);
    
    // Binary Store & Forward Queue
    bool queueTelemetry(const TelemetryEvent& event);
    bool hasQueuedTelemetry();
    int readQueuedTelemetry(TelemetryEvent* buf, int maxCount);
    void markSent(int count);
    
    uint32_t getUsedKB();
    void rotateIfNeeded();

private:
    bool statusOK;
    uint32_t readIndex;
    uint32_t writeIndex;
    
    void ensureDir(const char* dir);
    void prepareSPI();
    void loadIndices();
    void saveIndices();
};
