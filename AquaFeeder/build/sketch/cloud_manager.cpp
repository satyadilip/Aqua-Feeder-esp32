#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\cloud_manager.cpp"
#include "cloud_manager.h"
#include "telemetry.h"
#include "lora_manager.h"
// #include "wifi_manager.h"
// #include "gsm_manager.h"
// #include "sd_logger.h"

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
    
    if (!_tm->hasEvents()) return;
    
    unsigned long nowMs = millis();
    if (nowMs - _lastSendAttemptMs < 1000) return; // Rate limit 1s for fast testing
    _lastSendAttemptMs = nowMs;
    
    TelemetryEvent* event = _tm->peekNext();
    if (!event) return;
    
    bool sent = false;
    
    switch (_cfg->uplinkMode) {
        case UplinkMode::AUTO_FAILOVER:
            if (_status->loraStatus == ConnStatus::CONNECTED) {
                sent = trySendLoRa(*event);
            }
            if (!sent && _status->wifiStatus == ConnStatus::CONNECTED) {
                sent = trySendWiFi(*event);
            }
            if (!sent && _status->gsmStatus == ConnStatus::CONNECTED) {
                sent = trySendGSM(*event);
            }
            break;
            
        case UplinkMode::LORAWAN_ONLY:
            if (_status->loraStatus == ConnStatus::CONNECTED) {
                sent = trySendLoRa(*event);
            }
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
        _tm->markSent();
    } else {
        _tm->markFailed();
        if (event->retries >= TELEMETRY_RETRY_COUNT) {
            logToSD(*event);
            _tm->markSent(); // Discard after max retries, but logged to SD
        }
    }
}

bool CloudManager::trySendLoRa(const TelemetryEvent& event) {
    if (_lora) return _lora->sendTelemetry(event);
    return false;
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
    // Stub for SD logging
    // if (_sd) _sd->logTelemetry(event);
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
