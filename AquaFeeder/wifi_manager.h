#pragma once

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <DNSServer.h>
#include "config.h"

class WiFiManager_AF {
public:
    void begin(const DeviceConfig& cfg);
    void startAP(const char* ssid, const char* pass);
    void startSTA(const char* ssid, const char* pass);
    bool isAPActive();
    bool isSTAConnected();
    ConnStatus getStatus();
    IPAddress getAPIP();
    IPAddress getSTAIP();
    void setupWebServer(WebServer& server);
    void loop();

    void setStatusRef(SystemStatus* status);
    void setConfigRef(DeviceConfig* cfg);
    void setCallbacks(void (*onStart)(), void (*onStop)(), void (*onSaveConfig)(const DeviceConfig&), void (*onSaveNetwork)(const DeviceConfig&));

private:
    SystemStatus* _status = nullptr;
    DeviceConfig* _cfg = nullptr;
    void (*_onStart)() = nullptr;
    void (*_onStop)() = nullptr;
    void (*_onSaveConfig)(const DeviceConfig&) = nullptr;
    void (*_onSaveNetwork)(const DeviceConfig&) = nullptr;

    WebServer* _server = nullptr;
    DNSServer _dnsServer;
    bool _apActive = false;
    bool _mdnsActive = false;
    ConnStatus _staStatus = ConnStatus::DISCONNECTED;

    void handleRoot();
    void handleStatus();
    void handleSettings();
    void handleNetwork();
    void handleStart();
    void handleStop();
    void handleScan();
    void handleReboot();
    bool authenticateAdmin();
};
