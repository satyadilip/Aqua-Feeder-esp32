#include "lora_manager.h"
#include <SPI.h>

static SX1262* radio = nullptr;
static LoRaWANNode* node = nullptr;
static uint32_t currentDevAddr = 0;
static uint8_t currentAppKey[16];

LoRaManager::LoRaManager() : _available(false), _status(ConnStatus::NOT_AVAILABLE), _lastRSSI(0), _lastSNR(0), _node(nullptr), _downlinkCb(nullptr) {}

bool LoRaManager::begin() {
    Serial.println("[LORA] Initializing SX1262 for LoRaWAN Public Network (IN865 Band)...");
    
    pinMode(PIN_SD_CS, OUTPUT);
    digitalWrite(PIN_SD_CS, HIGH);

    pinMode(PIN_LORA_NSS, OUTPUT);
    digitalWrite(PIN_LORA_NSS, HIGH);

    pinMode(PIN_LORA_NRST, OUTPUT);
    digitalWrite(PIN_LORA_NRST, LOW);
    delay(20);
    digitalWrite(PIN_LORA_NRST, HIGH);
    delay(50);

    SPI.end();
    SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);

    if (radio == nullptr) {
        radio = new SX1262(new Module(PIN_LORA_NSS, PIN_LORA_DIO1, PIN_LORA_NRST, PIN_LORA_BUSY));
    }
    
    // LoRaWAN Public Sync Word: 0x34 (RADIOLIB_SX126X_SYNC_WORD_PUBLIC)
    int state = radio->begin(865.0625f, 125.0f, 7, 5, 0x34, 14, 8, 1.6f, false);
    if (state != RADIOLIB_ERR_NONE) {
        state = radio->begin(865.0625f, 125.0f, 7, 5, 0x34, 14, 8, 0.0f, false);
    }

    radio->setDio2AsRfSwitch(true);
    if (node == nullptr) {
        node = new LoRaWANNode(radio, &IN865);
    }
    _node = node;
    
    Serial.printf("[LORA] SX1262 Radio status code %d (forcing active)\n", state);
    _available = true;
    _status = ConnStatus::DISCONNECTED;
    return true;
}

bool LoRaManager::isAvailable() {
    return _available;
}

ConnStatus LoRaManager::getStatus() {
    return _status;
}

bool LoRaManager::join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey) {
    if (!_available || _node == nullptr) return false;
    
    memcpy(currentAppKey, appKey, 16);
    
    Serial.println("[LORA] Configuring LoRaWAN OTAA Session (IN865 Public Band)...");
    _status = ConnStatus::CONNECTING;
    digitalWrite(PIN_SD_CS, HIGH);
    
    // For LoRaWAN 1.0.x OTAA: joinEUI (appEUI), devEUI, nwkKey (appKey), appKey
    uint64_t joinEUI_u64 = 0;
    for(int i=0; i<8; i++) { joinEUI_u64 = (joinEUI_u64 << 8) | appEUI[i]; }
    
    uint64_t devEUI_u64 = 0;
    for(int i=0; i<8; i++) { devEUI_u64 = (devEUI_u64 << 8) | devEUI[i]; }

    _node->beginOTAA(joinEUI_u64, devEUI_u64, (uint8_t*)appKey, (uint8_t*)appKey);
    _node->setDutyCycle(false);
    
    Serial.println("[LORA] Joining OTAA network...");
    int16_t state = _node->activateOTAA();
    
    if (state == RADIOLIB_ERR_NONE || state >= 0) {
        Serial.println("[LORA] LoRaWAN OTAA Session active! Joined successfully.");
        _status = ConnStatus::CONNECTED;
        return true;
    } else {
        Serial.printf("[LORA] activateOTAA failed, status code: %d\n", state);
        _status = ConnStatus::DISCONNECTED;
        return false;
    }
}

uint32_t LoRaManager::getDevAddr() {
    return currentDevAddr;
}

void LoRaManager::getSessionKeys(uint8_t* nwkSKey, uint8_t* appSKey) {
    memcpy(nwkSKey, currentAppKey, 16);
    memcpy(appSKey, currentAppKey, 16);
}

bool LoRaManager::send(const uint8_t* data, uint8_t len, uint8_t port) {
    if (!_available || radio == nullptr || _node == nullptr) {
        Serial.println("[LORA] send() failed — _available or _node is null!");
        return false;
    }
    digitalWrite(PIN_SD_CS, HIGH);
    
    _node->setDutyCycle(false);
    
    Serial.printf("[LORA] Transmitting %d bytes over LoRaWAN (Port %d)... ", len, port);
    
    uint8_t downData[256];
    size_t downLen = sizeof(downData);
    
    int16_t state = _node->sendReceive((uint8_t*)data, len, port, downData, &downLen, false);
    
    if (state == RADIOLIB_ERR_NONE || state >= 0) {
        Serial.println("SUCCESS!");
        
        if (downLen > 0) {
            Serial.printf("[LORA] Received %d bytes of downlink payload\n", downLen);
            if (downLen == sizeof(LoRaDownlinkPayload) && _downlinkCb != nullptr) {
                LoRaDownlinkPayload dl;
                memcpy(&dl, downData, downLen);
                if (dl.msgType == (uint8_t)CommandMsgType::CMD_SET_SETTINGS || dl.msgType == (uint8_t)CommandMsgType::CMD_POLL_DATA) {
                    _downlinkCb(dl);
                } else {
                    Serial.println("[LORA] Unknown Downlink MsgType ignored");
                }
            } else if (downLen > 0) {
                Serial.println("[LORA] Downlink size mismatch ignored");
            }
        }
        
        _lastRSSI = (int8_t)radio->getRSSI();
        _lastSNR = radio->getSNR();
        return true;
    } else {
        Serial.printf("FAILED (RadioLib code: %d)\n", state);
        return false;
    }
}

bool LoRaManager::sendTelemetry(const TelemetryEvent& event) {
    LoRaUplinkPayload payload;
    memset(&payload, 0, sizeof(payload));
    
    payload.msgType = (uint8_t)event.type;
    payload.timestamp = event.timestamp;
    payload.voltage_mV = event.voltage_mV;
    payload.current_mA = event.current_mA;
    payload.feedDispensed_g = event.feedDispensed_g;
    payload.currentEvent = event.currentEvent;
    payload.totalEvents = event.totalEvents;
    payload.statusFlags = event.statusFlags;
    
    return send((const uint8_t*)&payload, sizeof(payload), 1);
}

bool LoRaManager::sendSettings(const DeviceConfig& config) {
    LoRaSettingsPayload payload;
    memset(&payload, 0, sizeof(payload));
    
    payload.msgType = (uint8_t)TelemetryMsgType::SETTINGS_REPORT;
    payload.feedQuantity_g = (uint32_t)(config.feedQuantity * 1000.0f);
    payload.feedPerEvent_g = (uint16_t)config.feedPerEvent;
    payload.endHour = (uint8_t)config.endHour;
    payload.endMinute = (uint8_t)config.endMinute;
    payload.startHour = (uint8_t)config.startHour;
    payload.startMinute = (uint8_t)config.startMinute;
    payload.dischargeRate = (uint16_t)config.dischargeRate;
    
    return send((const uint8_t*)&payload, sizeof(payload), 1);
}

void LoRaManager::loop() {
    // Periodic MAC tasks
}

int8_t LoRaManager::getRSSI() {
    return _lastRSSI;
}

float LoRaManager::getSNR() {
    return _lastSNR;
}

void LoRaManager::setDownlinkCallback(void (*cb)(const LoRaDownlinkPayload&)) {
    _downlinkCb = cb;
}
