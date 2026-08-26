#pragma once

#include "config.h"
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

class TelemetryManager {
public:
    void begin(SystemStatus* status, DeviceConfig* cfg);
    void queueEvent(TelemetryMsgType type);
    void queueEvent(const TelemetryEvent& event);
    bool hasEvents() const;
    TelemetryEvent* peekNext();
    void markSent();
    void markFailed();
    int pendingCount() const;
    void update(unsigned long nowMs);

private:
    SystemStatus* _status;
    DeviceConfig* _cfg;
    TelemetryEvent _queue[TELEMETRY_QUEUE_SIZE];
    int _head;
    int _tail;
    int _count;
    unsigned long _lastPeriodicMs;
    SemaphoreHandle_t _mutex;
};
