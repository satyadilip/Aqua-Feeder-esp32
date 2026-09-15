#include "telemetry.h"

void TelemetryManager::begin(SystemStatus* status, DeviceConfig* cfg) {
    _status = status;
    _cfg = cfg;
    _head = 0;
    _tail = 0;
    _count = 0;
    _lastPeriodicMs = 0;
    _mutex = xSemaphoreCreateMutex();
}

void TelemetryManager::queueEvent(TelemetryMsgType type) {
    if (!_status) return;
    
    TelemetryEvent event;
    event.type = type;
    event.timestamp = _status->currentEpoch;
    event.voltage_mV = (uint16_t)(_status->voltageV * 1000.0f);
    event.current_mA = (uint16_t)_status->currentMA;
    event.feedDispensed_g = _status->currentEvent * (_cfg ? _cfg->feedPerEvent : 0);
    event.currentEvent = _status->currentEvent;
    event.totalEvents = _status->totalEvents;
    
    uint8_t flags = 0;
    if (_status->proximityTriggered) flags |= (1 << 0);
    if (_status->state == SystemState::ERROR_FATAL) flags |= (1 << 1); // Simple mapping
    if (!_status->rtcOK) flags |= (1 << 2);
    if (!_status->sdCardOK) flags |= (1 << 3);
    if (_status->loraStatus == ConnStatus::CONNECTED) flags |= (1 << 4);
    if (_status->wifiStatus == ConnStatus::CONNECTED) flags |= (1 << 5);
    if (_status->gsmStatus == ConnStatus::CONNECTED) flags |= (1 << 6);
    
    event.statusFlags = flags;
    event.sent = false;
    event.retries = 0;
    
    queueEvent(event);
}

void TelemetryManager::queueEvent(const TelemetryEvent& event) {
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        if (_count >= TELEMETRY_QUEUE_SIZE) {
            // Drop oldest event
            _tail = (_tail + 1) % TELEMETRY_QUEUE_SIZE;
            _count--;
        }
        _queue[_head] = event;
        _head = (_head + 1) % TELEMETRY_QUEUE_SIZE;
        _count++;
        xSemaphoreGive(_mutex);
    }
}

bool TelemetryManager::hasEvents() const {
    bool has = false;
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        has = _count > 0;
        xSemaphoreGive(_mutex);
    }
    return has;
}

TelemetryEvent* TelemetryManager::peekNext() {
    TelemetryEvent* ptr = nullptr;
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        if (_count > 0) ptr = &_queue[_tail];
        xSemaphoreGive(_mutex);
    }
    return ptr;
}

void TelemetryManager::markSent() {
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        if (_count > 0) {
            _tail = (_tail + 1) % TELEMETRY_QUEUE_SIZE;
            _count--;
        }
        xSemaphoreGive(_mutex);
    }
}

void TelemetryManager::markFailed() {
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        if (_count > 0) {
            _queue[_tail].retries++;
        }
        xSemaphoreGive(_mutex);
    }
}

int TelemetryManager::pendingCount() const {
    int c = 0;
    if (_mutex && xSemaphoreTake(_mutex, portMAX_DELAY)) {
        c = _count;
        xSemaphoreGive(_mutex);
    }
    return c;
}

void TelemetryManager::update(unsigned long nowMs) {
    if (!_cfg) return;
    
    unsigned long intervalMs = _cfg->telemetryIntervalS * 1000UL;
    
    // Ignore old 5s default from NVS and treat anything under 60s as "disabled"
    if (intervalMs > 0 && intervalMs < 60000) {
        intervalMs = 0; 
    }
    
    // If 0, periodic heartbeat is completely disabled (purely event-driven)
    if (intervalMs == 0) return;
    
    if (nowMs - _lastPeriodicMs >= intervalMs) {
        _lastPeriodicMs = nowMs;
        queueEvent(TelemetryMsgType::PERIODIC_HEARTBEAT);
    }
}
