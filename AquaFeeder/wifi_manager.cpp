#include "wifi_manager.h"
#include "web_dashboard.h"
#include <ArduinoJson.h>
#include <Preferences.h>

const byte DNS_PORT = 53;

void WiFiManager_AF::begin(const DeviceConfig& cfg) {
    if (cfg.wifiSSID[0] != '\0' && strcmp(cfg.wifiSSID, cfg.apSSID) != 0) {
        WiFi.mode(WIFI_AP_STA);
        startSTA(cfg.wifiSSID, cfg.wifiPass);
    } else {
        WiFi.mode(WIFI_AP);
    }
    startAP(cfg.apSSID, cfg.apPass);
    
    // Start mDNS responder so user can type http://aquafeeder.local
    if (MDNS.begin("aquafeeder")) {
        MDNS.addService("http", "tcp", 80);
        _mdnsActive = true;
        Serial.println("[WIFI] mDNS responder started: http://aquafeeder.local");
    }

    // Start Captive Portal DNS server (redirects any domain to SoftAP IP)
    _dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
    Serial.println("[WIFI] Captive Portal DNS server active.");
}

void WiFiManager_AF::startAP(const char* ssid, const char* pass) {
    Serial.printf("[WIFI] Starting AP: %s\n", ssid);
    WiFi.softAP(ssid, pass, WIFI_AP_CHANNEL, 0, WIFI_AP_MAX_CONN);
    _apActive = true;
    Serial.print("[WIFI] AP IP: ");
    Serial.println(WiFi.softAPIP());
}

void WiFiManager_AF::startSTA(const char* ssid, const char* pass) {
    Serial.printf("[WIFI] Connecting to STA: %s\n", ssid);
    WiFi.begin(ssid, pass);
    _staStatus = ConnStatus::CONNECTING;
    
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[WIFI] STA Connected.");
        Serial.print("[WIFI] STA IP: ");
        Serial.println(WiFi.localIP());
        _staStatus = ConnStatus::CONNECTED;
    } else {
        Serial.println("[WIFI] STA Connection failed.");
        _staStatus = ConnStatus::ERROR;
    }
}

bool WiFiManager_AF::isAPActive() { return _apActive; }
bool WiFiManager_AF::isSTAConnected() { return WiFi.status() == WL_CONNECTED; }
ConnStatus WiFiManager_AF::getStatus() { return _staStatus; }
IPAddress WiFiManager_AF::getAPIP() { return WiFi.softAPIP(); }
IPAddress WiFiManager_AF::getSTAIP() { return WiFi.localIP(); }

void WiFiManager_AF::setupWebServer(WebServer& server) {
    _server = &server;
    
    _server->on("/", HTTP_GET, [this]() { handleRoot(); });
    _server->on("/generate_204", HTTP_GET, [this]() { handleRoot(); }); // Captive Portal Android
    _server->on("/fwlink", HTTP_GET, [this]() { handleRoot(); });       // Captive Portal Windows
    _server->on("/api/status", HTTP_GET, [this]() { handleStatus(); });
    _server->on("/api/settings", HTTP_POST, [this]() { handleSettings(); });
    _server->on("/api/network", HTTP_POST, [this]() { handleNetwork(); });
    _server->on("/api/start", HTTP_POST, [this]() { handleStart(); });
    _server->on("/api/stop", HTTP_POST, [this]() { handleStop(); });
    _server->on("/api/test", HTTP_POST, [this]() {
        if (!authenticateAdmin()) return;
        if (_server->hasArg("relay")) {
            int r = _server->arg("relay").toInt();
            if (r == 1 || r == 2) {
                digitalWrite((r == 1) ? PIN_RELAY_LOADER : PIN_RELAY_DISPENSER, LOW);
                delay(2000);
                digitalWrite((r == 1) ? PIN_RELAY_LOADER : PIN_RELAY_DISPENSER, HIGH);
            }
        }
        if (_server->hasArg("hooter")) {
            digitalWrite(PIN_HOOTER, LOW);
            delay(1000);
            digitalWrite(PIN_HOOTER, HIGH);
        }
        _server->send(200, "application/json", "{\"ok\":true}");
    });
    _server->on("/api/network/scan", HTTP_GET, [this]() { handleScan(); });
    _server->on("/api/reboot", HTTP_POST, [this]() { 
        if (!authenticateAdmin()) return;
        handleReboot(); 
    });
    _server->on("/api/reset", HTTP_POST, [this]() {
        if (!authenticateAdmin()) return;
        if (_cfg) {
            Preferences prefs;
            prefs.begin(NVS_NAMESPACE, false);
            prefs.clear();
            prefs.end();
        }
        _server->send(200, "application/json", "{\"ok\":true}");
        delay(1000);
        ESP.restart();
    });

    _server->onNotFound([this]() {
        handleRoot(); // Captive portal wildcard redirect
    });
}

bool WiFiManager_AF::authenticateAdmin() {
    if (!_server) return false;
    const char* apPass = (_cfg && _cfg->apPass[0] != '\0') ? _cfg->apPass : "aquafeeder123";
    if (!_server->authenticate("admin", apPass)) {
        _server->requestAuthentication();
        return false;
    }
    return true;
}

void WiFiManager_AF::loop() {
    _dnsServer.processNextRequest();
    if (_server) _server->handleClient();
}

void WiFiManager_AF::setStatusRef(SystemStatus* status) { _status = status; }
void WiFiManager_AF::setConfigRef(DeviceConfig* cfg) { _cfg = cfg; }
void WiFiManager_AF::setCallbacks(void (*onStart)(), void (*onStop)(), void (*onSaveConfig)(const DeviceConfig&), void (*onSaveNetwork)(const DeviceConfig&)) {
    _onStart = onStart;
    _onStop = onStop;
    _onSaveConfig = onSaveConfig;
    _onSaveNetwork = onSaveNetwork;
}

void WiFiManager_AF::handleRoot() {
    if (_server) _server->send(200, "text/html", WEB_DASHBOARD_HTML);
}

void WiFiManager_AF::handleStatus() {
    if (!_server || !_status) return;
    
    JsonDocument doc;
    doc["state"] = (uint8_t)_status->state;
    doc["feedState"] = (uint8_t)_status->feedState;
    doc["feedActive"] = _status->feedActive;
    doc["currentEvent"] = _status->currentEvent;
    doc["totalEvents"] = _status->totalEvents;
    doc["scheduleValid"] = _status->scheduleValid;
    doc["schedError"] = _status->schedError;
    doc["voltage"] = _status->voltageV;
    doc["current"] = _status->currentMA;
    doc["power"] = _status->powerMW;
    doc["proximity"] = _status->proximityTriggered;
    doc["rtcOK"] = _status->rtcOK;
    doc["loraStatus"] = (uint8_t)_status->loraStatus;
    doc["wifiStatus"] = (uint8_t)_status->wifiStatus;
    doc["gsmStatus"] = (uint8_t)_status->gsmStatus;
    doc["sdOK"] = _status->sdCardOK;
    doc["heap"] = ESP.getFreeHeap();
    doc["uptime"] = millis() - _status->bootTimeMs;

    // Time formatting
    if (_status->rtcOK) {
        char tb[16];
        uint32_t ep = _status->currentEpoch;
        int s = ep % 60; ep /= 60;
        int m = ep % 60; ep /= 60;
        int h = ep % 24;
        snprintf(tb, sizeof(tb), "%02d:%02d:%02d", h, m, s);
        doc["time"] = tb;
    } else {
        doc["time"] = "--:--:--";
    }

    // Config object
    if (_cfg) {
        JsonObject cfgObj = doc["cfg"].to<JsonObject>();
        cfgObj["qty"] = _cfg->feedQuantity;
        cfgObj["fpe"] = _cfg->feedPerEvent;
        cfgObj["ehour"] = _cfg->endHour;
        cfgObj["emin"] = _cfg->endMinute;
        cfgObj["rate"] = _cfg->dischargeRate;
        cfgObj["shour"] = _cfg->startHour;
        cfgObj["smin"] = _cfg->startMinute;
        cfgObj["uplinkMode"] = (uint8_t)_cfg->uplinkMode;
        cfgObj["txInterval"] = _cfg->telemetryIntervalS;
        cfgObj["wssid"] = _cfg->wifiSSID;
        cfgObj["mqsrv"] = _cfg->mqttServer;
        cfgObj["mqport"] = _cfg->mqttPort;
        cfgObj["apn"] = _cfg->gsmAPN;
        cfgObj["devid"] = _cfg->deviceId;
    }

    // Hardware Diagnostics Object
    JsonObject diagObj = doc["diag"].to<JsonObject>();
    diagObj["rtc"] = _status->diag.ds3231_rtc;
    diagObj["power"] = _status->diag.ina219_power;
    diagObj["lcd"] = _status->diag.lcd_display;
    diagObj["lcdAddr"] = _status->diag.lcd_i2c_addr;
    diagObj["sd"] = _status->diag.sd_card;
    diagObj["lora"] = _status->diag.lora_sx1262;
    diagObj["gsm"] = _status->diag.gsm_sim800l;
    diagObj["csq"] = _status->diag.gsm_csq;
    diagObj["sw1"] = _status->diag.sw1_ok;
    diagObj["sw2"] = _status->diag.sw2_ok;
    diagObj["sw3"] = _status->diag.sw3_ok;
    diagObj["sw4"] = _status->diag.sw4_ok;
    diagObj["proxClear"] = _status->diag.prox_sensor_clear;
    diagObj["i2cCount"] = _status->diag.i2c_count;

    JsonArray i2cArr = diagObj["i2cAddrs"].to<JsonArray>();
    for (int i = 0; i < _status->diag.i2c_count && i < 16; i++) {
        i2cArr.add(_status->diag.i2c_addrs[i]);
    }
    
    String out;
    serializeJson(doc, out);
    _server->send(200, "application/json", out);
}

void WiFiManager_AF::handleSettings() {
    if (!_server || !_cfg) return;
    if (!authenticateAdmin()) return;

    if (_server->hasArg("qty"))   _cfg->feedQuantity = _server->arg("qty").toFloat();
    if (_server->hasArg("fpe"))   _cfg->feedPerEvent = _server->arg("fpe").toInt();
    if (_server->hasArg("ehour")) _cfg->endHour = _server->arg("ehour").toInt();
    if (_server->hasArg("emin"))  _cfg->endMinute = _server->arg("emin").toInt();
    if (_server->hasArg("rate"))  _cfg->dischargeRate = _server->arg("rate").toInt();
    if (_server->hasArg("shour")) _cfg->startHour = _server->arg("shour").toInt();
    if (_server->hasArg("smin"))  _cfg->startMinute = _server->arg("smin").toInt();

    if (_onSaveConfig) _onSaveConfig(*_cfg);
    _server->send(200, "application/json", "{\"ok\":true}");
}

void WiFiManager_AF::handleNetwork() {
    if (!_server || !_cfg) return;
    if (!authenticateAdmin()) return;

    if (_server->hasArg("mode"))     _cfg->uplinkMode = (UplinkMode)_server->arg("mode").toInt();
    if (_server->hasArg("interval")) _cfg->telemetryIntervalS = _server->arg("interval").toInt();
    if (_server->hasArg("wssid"))    strncpy(_cfg->wifiSSID, _server->arg("wssid").c_str(), sizeof(_cfg->wifiSSID));
    if (_server->hasArg("wpass") && _server->arg("wpass").length() > 0)
        strncpy(_cfg->wifiPass, _server->arg("wpass").c_str(), sizeof(_cfg->wifiPass));
    if (_server->hasArg("mqsrv"))    strncpy(_cfg->mqttServer, _server->arg("mqsrv").c_str(), sizeof(_cfg->mqttServer));
    if (_server->hasArg("mqport"))   _cfg->mqttPort = _server->arg("mqport").toInt();
    if (_server->hasArg("apn"))      strncpy(_cfg->gsmAPN, _server->arg("apn").c_str(), sizeof(_cfg->gsmAPN));
    if (_server->hasArg("guser"))    strncpy(_cfg->gsmUser, _server->arg("guser").c_str(), sizeof(_cfg->gsmUser));
    if (_server->hasArg("gpass") && _server->arg("gpass").length() > 0)
        strncpy(_cfg->gsmPass, _server->arg("gpass").c_str(), sizeof(_cfg->gsmPass));
    if (_server->hasArg("gmqsrv"))   strncpy(_cfg->gsmMqttServer, _server->arg("gmqsrv").c_str(), sizeof(_cfg->gsmMqttServer));

    if (_onSaveNetwork) _onSaveNetwork(*_cfg);
    _server->send(200, "application/json", "{\"ok\":true}");
}

void WiFiManager_AF::handleStart() {
    if (!authenticateAdmin()) return;
    if (_onStart) _onStart();
    if (_server) _server->send(200, "application/json", "{\"ok\":true}");
}

void WiFiManager_AF::handleStop() {
    if (!authenticateAdmin()) return;
    if (_onStop) _onStop();
    if (_server) _server->send(200, "application/json", "{\"ok\":true}");
}

void WiFiManager_AF::handleScan() {
    int n = WiFi.scanNetworks();
    JsonDocument doc;
    JsonArray arr = doc.to<JsonArray>();
    for (int i = 0; i < n; i++) {
        JsonObject net = arr.add<JsonObject>();
        net["ssid"] = WiFi.SSID(i);
        net["rssi"] = WiFi.RSSI(i);
        net["secure"] = (WiFi.encryptionType(i) != WIFI_AUTH_OPEN);
    }
    String out;
    serializeJson(doc, out);
    _server->send(200, "application/json", out);
}

void WiFiManager_AF::handleReboot() {
    if (_server) _server->send(200, "application/json", "{\"ok\":true}");
    delay(1000);
    ESP.restart();
}
