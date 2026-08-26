#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\gsm_manager.cpp"
#include "gsm_manager.h"
#include <HardwareSerial.h>

GSMManager::GSMManager() : _available(false), _status(ConnStatus::NOT_AVAILABLE), _gprsConnected(false) {}

bool GSMManager::begin() {
    Serial.println("[GSM] Initializing SIM800L...");

    bool ok = false;

    // Try 9600 baud first (SIM800L default)
    Serial1.begin(9600, SERIAL_8N1, PIN_GSM_RX, PIN_GSM_TX);
    delay(100);
    for (int i = 0; i < 5; i++) {
        String resp = sendAT("AT", 300, "OK");
        if (resp.indexOf("OK") != -1) { ok = true; break; }
    }

    if (!ok) {
        // Try 115200 baud
        Serial1.begin(115200, SERIAL_8N1, PIN_GSM_RX, PIN_GSM_TX);
        delay(100);
        for (int i = 0; i < 5; i++) {
            String resp = sendAT("AT", 300, "OK");
            if (resp.indexOf("OK") != -1) { ok = true; break; }
        }
    }

    if (!ok) {
        // Switch back to 9600 with newline
        Serial1.begin(9600, SERIAL_8N1, PIN_GSM_RX, PIN_GSM_TX);
        delay(100);
        for (int i = 0; i < 5; i++) {
            String resp = sendAT("AT\r\n", 300, "OK");
            if (resp.indexOf("OK") != -1) { ok = true; break; }
        }
    }

    if (ok) {
        sendAT("ATE0", 300, "OK");         // Echo off
        sendAT("AT+IPR=9600", 300, "OK");   // Lock baud rate to 9600
        Serial.println("[GSM] SIM800L detected & responsive.");
        _available = true;
        _status = ConnStatus::DISCONNECTED;

        // Check if SIM card is physically inserted
        String cpin = sendAT("AT+CPIN?", 1000, "CPIN:");
        if (cpin.indexOf("READY") != -1) {
            Serial.println("[GSM] SIM Card: INSERTED & READY");
        } else {
            Serial.println("[GSM] SIM Card: NOT INSERTED (insert SIM card for GPRS fallback)");
        }
        return true;
    }
    
    Serial.println("[GSM] SIM800L not responding (check power 3.8V-4.2V & TX/RX pin connections).");
    _available = false;
    _status = ConnStatus::NOT_AVAILABLE;
    return false;
}

bool GSMManager::isAvailable() {
    return _available;
}

ConnStatus GSMManager::getStatus() {
    return _status;
}

bool GSMManager::connectGPRS(const char* apn, const char* user, const char* pass) {
    if (!_available) return false;
    
    _status = ConnStatus::CONNECTING;
    Serial.println("[GSM] Connecting GPRS...");
    
    sendAT("AT+CGATT=1", 2000, "OK");
    
    String cmd = String("AT+CSTT=\"") + apn + "\",\"" + user + "\",\"" + pass + "\"";
    sendAT(cmd.c_str(), 1000, "OK");
    
    sendAT("AT+CIICR", 3000, "OK");
    String ipResp = sendAT("AT+CIFSR", 1000, "."); // Looking for IP
    
    if (ipResp.indexOf('.') != -1) {
        Serial.println("[GSM] GPRS Connected. IP: " + ipResp);
        _gprsConnected = true;
        _status = ConnStatus::CONNECTED;
        return true;
    }
    
    Serial.println("[GSM] GPRS Connection failed.");
    _gprsConnected = false;
    _status = ConnStatus::ERROR;
    return false;
}

bool GSMManager::isGPRSConnected() {
    return _gprsConnected;
}

int GSMManager::getSignalQuality() {
    if (!_available) return 99;
    
    String resp = sendAT("AT+CSQ", 1000, "+CSQ:");
    int idx = resp.indexOf("+CSQ:");
    if (idx != -1) {
        int commaIdx = resp.indexOf(',', idx);
        String valStr = resp.substring(idx + 5, commaIdx);
        valStr.trim();
        return valStr.toInt();
    }
    return 99;
}

bool GSMManager::mqttConnect(const char* server, uint16_t port, const char* clientId) {
    if (!_gprsConnected) return false;
    
    String cmd = String("AT+CIPSTART=\"TCP\",\"") + server + "\",\"" + port + "\"";
    String resp = sendAT(cmd.c_str(), 5000, "CONNECT OK");
    
    if (resp.indexOf("CONNECT OK") != -1) {
        Serial.println("[GSM] TCP Connected to MQTT server.");
        return true;
    }
    return false;
}

bool GSMManager::mqttPublish(const char* topic, const char* payload) {
    Serial.printf("[GSM] Publishing to %s: %s\n", topic, payload);
    return true;
}

void GSMManager::disconnect() {
    if (_available) {
        sendAT("AT+CIPSHUT", 1000, "SHUT OK");
        _gprsConnected = false;
        _status = ConnStatus::DISCONNECTED;
    }
}

void GSMManager::loop() {
    if (Serial1.available()) {
        String data = Serial1.readString();
    }
}

String GSMManager::sendAT(const char* cmd, uint32_t timeoutMs, const char* expectedResp) {
    while (Serial1.available()) Serial1.read(); // Flush RX buffer
    Serial1.println(cmd);
    unsigned long start = millis();
    String response = "";
    while (millis() - start < timeoutMs) {
        while (Serial1.available()) {
            char c = (char)Serial1.read();
            response += c;
        }
        if (expectedResp && response.indexOf(expectedResp) != -1) break;
        if (response.indexOf("OK") != -1 || response.indexOf("ERROR") != -1) break;
        delay(10);
    }
    return response;
}
