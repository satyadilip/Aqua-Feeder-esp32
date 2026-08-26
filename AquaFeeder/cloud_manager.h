#pragma once

#include "config.h"
#include <Arduino.h>

class LoRaManager;
class WiFiManager_AF;
class GSMManager;
class SDLogger;
class TelemetryManager;

class CloudManager {
public:
    void begin(SystemStatus* status, DeviceConfig* cfg);
    void setLoRa(LoRaManager* lora);
    void setWiFi(WiFiManager_AF* wifi);
    void setGSM(GSMManager* gsm);
    void setSDLogger(SDLogger* sd);
    void setTelemetry(TelemetryManager* tm);
    
    void loop();

private:
    SystemStatus* _status;
    DeviceConfig* _cfg;
    LoRaManager* _lora;
    WiFiManager_AF* _wifi;
    GSMManager* _gsm;
    SDLogger* _sd;
    TelemetryManager* _tm;
    
    unsigned long _lastSendAttemptMs;
    
    bool trySendLoRa(const TelemetryEvent& event);
    bool trySendWiFi(const TelemetryEvent& event);
    bool trySendGSM(const TelemetryEvent& event);
    void logToSD(const TelemetryEvent& event);
    String buildJSON(const TelemetryEvent& event);
};
