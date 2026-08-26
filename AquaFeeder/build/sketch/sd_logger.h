#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\sd_logger.h"
#pragma once
#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include "config.h"

class SDLogger {
public:
    bool begin();
    bool isOK();
    bool logTelemetry(const TelemetryEvent& event);
    bool logEvent(const char* msg);
    bool hasQueuedTelemetry();
    int readQueuedTelemetry(TelemetryEvent* buf, int maxCount);
    void markSent(int count);
    uint32_t getUsedKB();
    void rotateIfNeeded();

private:
    bool statusOK;
    void ensureDir(const char* dir);
    void prepareSPI();
};
