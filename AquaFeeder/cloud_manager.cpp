#include "cloud_manager.h"
#include "telemetry.h"
#include "lora_manager.h"
#include "wifi_manager.h"
// #include "gsm_manager.h"
#include "sd_logger.h"

void CloudManager::begin(SystemStatus* status, DeviceConfig* cfg) {
    _status = status;
    _cfg = cfg;
    _lora = nullptr;
    _wifi = nullptr;
    _gsm = nullptr;
    _sd = nullptr;
    _tm = nullptr;
    _lastSendAttemptMs = 0;
}

void CloudManager::setLoRa(LoRaManager* lora) { _lora = lora; }
void CloudManager::setWiFi(WiFiManager_AF* wifi) { _wifi = wifi; }
void CloudManager::setGSM(GSMManager* gsm) { _gsm = gsm; }
void CloudManager::setSDLogger(SDLogger* sd) { _sd = sd; }
void CloudManager::setTelemetry(TelemetryManager* tm) { _tm = tm; }

void CloudManager::loop() {
    if (!_tm || !_cfg || !_status) return;
    
    unsigned long nowMs = millis();
    // Use 30 seconds interval if we are disconnected/error (Join Retry), otherwise 5 seconds for telemetry check
    unsigned long interval = (_status->loraStatus == ConnStatus::ERROR || _status->loraStatus == ConnStatus::DISCONNECTED) ? 30000 : 5000;
    
    if (nowMs - _lastSendAttemptMs < interval) return;
    
    Serial.println("[CLOUD] Processing telemetry uplink check...");
    
    // Auto-reconnect LoRaWAN if it failed previously
    if (_lora && (_status->loraStatus == ConnStatus::ERROR || _status->loraStatus == ConnStatus::DISCONNECTED)) {
        if (_cfg->uplinkMode == UplinkMode::LORAWAN_ONLY || _cfg->uplinkMode == UplinkMode::AUTO_FAILOVER) {
            Serial.println("[LORA] Retrying LoRaWAN Join (30s cooldown)...");
            if (_lora->join(_cfg->loraDevEUI, _cfg->loraAppEUI, _cfg->loraAppKey)) {
                _status->loraStatus = ConnStatus::CONNECTED;
                Serial.println("[LORA] LoRaWAN Join SUCCESS upon retry!");
            } else {
                _status->loraStatus = ConnStatus::ERROR;
                Serial.println("[LORA] LoRaWAN Join retry FAILED.");
            }
            _lastSendAttemptMs = millis(); // Reset timer AFTER the attempt!
            return; // Give it a break before processing telemetry
        }
    }
    
    _lastSendAttemptMs = millis(); // Reset timer for normal telemetry checks
    
    TelemetryEvent heartBeatEvent;
    TelemetryEvent* event = nullptr;
    
    if (_tm->hasEvents()) {
        event = _tm->peekNext();
    } else if (_sd && _sd->hasQueuedTelemetry()) {
        static TelemetryEvent sdEvent;
        if (_sd->readQueuedTelemetry(&sdEvent, 1) == 1) {
            event = &sdEvent;
            Serial.println("[CLOUD] Processing queued event from SD");
        }
    } else {
        memset(&heartBeatEvent, 0, sizeof(heartBeatEvent));
        heartBeatEvent.type = TelemetryMsgType::PERIODIC_HEARTBEAT;
        heartBeatEvent.timestamp = time(nullptr);
        heartBeatEvent.voltage_mV = (uint16_t)(_status->voltageV * 1000);
        heartBeatEvent.current_mA = (uint16_t)_status->currentMA;
        heartBeatEvent.feedDispensed_g = 100;
        heartBeatEvent.currentEvent = _status->currentEvent;
        heartBeatEvent.totalEvents = _status->totalEvents;
        event = &heartBeatEvent;
    }
    if (!event) return;
    
    bool sent = false;
    
    switch (_cfg->uplinkMode) {
        case UplinkMode::AUTO_FAILOVER:
            sent = trySendLoRa(*event);
            if (!sent && _status->wifiStatus == ConnStatus::CONNECTED) {
                sent = trySendWiFi(*event);
            }
            if (!sent && _status->gsmStatus == ConnStatus::CONNECTED) {
                sent = trySendGSM(*event);
            }
            break;
            
        case UplinkMode::LORAWAN_ONLY:
            sent = trySendLoRa(*event);
            break;
            
        case UplinkMode::WIFI_ONLY:
            if (_status->wifiStatus == ConnStatus::CONNECTED) {
                sent = trySendWiFi(*event);
            }
            break;
            
        case UplinkMode::GSM_ONLY:
            if (_status->gsmStatus == ConnStatus::CONNECTED) {
                sent = trySendGSM(*event);
            }
            break;
    }
    
    if (sent) {
        if (event != &heartBeatEvent) {
            if (_tm->hasEvents() && event == _tm->peekNext()) {
                _tm->markSent();
            } else if (_sd) {
                _sd->markSent(1);
            }
        }
    } else {
        if (event != &heartBeatEvent) {
            if (_tm->hasEvents() && event == _tm->peekNext()) {
                _tm->markFailed();
                if (event->retries >= TELEMETRY_RETRY_COUNT) {
                    logToSD(*event);
                    _tm->markSent(); // Discard from RAM after max retries, but logged to SD
                }
            } else if (_sd) {
                // If it failed from SD, do nothing. It will be retried next time.
            }
        }
    }
}

bool CloudManager::trySendLoRa(const TelemetryEvent& event) {
    if (!_lora || _status->loraStatus != ConnStatus::CONNECTED) return false;
    if (event.type == TelemetryMsgType::SETTINGS_REPORT) {
        if (_cfg) return _lora->sendSettings(*_cfg);
        return false;
    }
    return _lora->sendTelemetry(event);
}

bool CloudManager::trySendWiFi(const TelemetryEvent& event) {
    String payload = buildJSON(event);
    // Stub for actual WiFi MQTT send implementation
    // String topic = String("aquafeeder/") + _cfg->deviceId + "/telemetry";
    // if (_wifi && _wifi->mqttPublish(topic.c_str(), payload.c_str())) return true;
    return false; // Not implemented without wifi manager
}

bool CloudManager::trySendGSM(const TelemetryEvent& event) {
    String payload = buildJSON(event);
    // Stub for actual GSM MQTT send implementation
    // String topic = String("aquafeeder/") + _cfg->deviceId + "/telemetry";
    // if (_gsm && _gsm->mqttPublish(topic.c_str(), payload.c_str())) return true;
    return false; // Not implemented without gsm manager
}

void CloudManager::logToSD(const TelemetryEvent& event) {
    if (_sd) {
        _sd->logTelemetry(event); // CSV log
        _sd->queueTelemetry(event); // Binary queue for Store & Forward
        Serial.println("[CLOUD] Event queued to SD Card for Store & Forward");
    }
}

String CloudManager::buildJSON(const TelemetryEvent& event) {
    // Basic JSON builder without ArduinoJson for simplicity and memory savings,
    // although ArduinoJson is available.
    String json = "{";
    json += "\"device_id\":\"" + String(_cfg->deviceId) + "\",";
    
    String msgTypeStr = "UNKNOWN";
    if (event.type == TelemetryMsgType::SESSION_COMPLETE) msgTypeStr = "SESSION_COMPLETE";
    else if (event.type == TelemetryMsgType::PERIODIC_HEARTBEAT) msgTypeStr = "PERIODIC_HEARTBEAT";
    else if (event.type == TelemetryMsgType::FEED_STARTED) msgTypeStr = "FEED_STARTED";
    else if (event.type == TelemetryMsgType::FEED_PAUSED) msgTypeStr = "FEED_PAUSED";
    else if (event.type == TelemetryMsgType::FEED_RESUMED) msgTypeStr = "FEED_RESUMED";
    else if (event.type == TelemetryMsgType::ALARM_OVERCURRENT) msgTypeStr = "ALARM_OVERCURRENT";
    else if (event.type == TelemetryMsgType::SETTINGS_REPORT) msgTypeStr = "SETTINGS_REPORT";
    
    json += "\"msg_type\":\"" + msgTypeStr + "\",";
    json += "\"ts\":" + String(event.timestamp) + ",";
    json += "\"v_mv\":" + String(event.voltage_mV) + ",";
    json += "\"i_ma\":" + String(event.current_mA) + ",";
    json += "\"feed_g\":" + String(event.feedDispensed_g) + ",";
    json += "\"evt\":" + String(event.currentEvent) + ",";
    json += "\"total\":" + String(event.totalEvents) + ",";
    json += "\"flags\":" + String(event.statusFlags);
    json += "}";
    
    return json;
}
