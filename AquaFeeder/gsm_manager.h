#pragma once

#include <Arduino.h>
#include "config.h"

class GSMManager {
public:
    GSMManager();

    bool begin();
    bool isAvailable();
    ConnStatus getStatus();
    
    bool connectGPRS(const char* apn, const char* user, const char* pass);
    bool isGPRSConnected();
    int getSignalQuality();
    
    bool mqttConnect(const char* server, uint16_t port, const char* clientId);
    bool mqttPublish(const char* topic, const char* payload);
    
    void disconnect();
    void loop();

private:
    String sendAT(const char* cmd, uint32_t timeoutMs, const char* expectedResp);
    
    bool _available;
    ConnStatus _status;
    bool _gprsConnected;
};
