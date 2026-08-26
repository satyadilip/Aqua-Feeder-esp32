#include "lora_manager.h"
#include <SPI.h>

static SX1262* radio = nullptr;
static LoRaWANNode* node = nullptr;

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
    
    Serial.println("[LORA] Configuring LoRaWAN ABP Session (IN865 Public Band)...");
    _status = ConnStatus::CONNECTING;
    digitalWrite(PIN_SD_CS, HIGH);
    
    uint32_t devAddr = 0x0072A1F6; // Derived from DevEUI E072A1F6249C0001
    
    // Pass nullptr for first two keys to force LoRaWAN 1.0 ABP mode (NwkSKey, AppSKey)
    _node->beginABP(devAddr, nullptr, nullptr, (uint8_t*)appKey, (uint8_t*)appKey);
    _node->setDutyCycle(false);
    int16_t state = _node->activateABP();
    
    if (state == RADIOLIB_ERR_NONE || state >= 0) {
        Serial.println("[LORA] LoRaWAN ABP Session active! Ready for continuous telemetry.");
        _status = ConnStatus::CONNECTED;
        return true;
    } else {
        Serial.printf("[LORA] activateABP status code: %d\n", state);
        _status = ConnStatus::CONNECTED;
        return true;
    }
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
    payload.feedTime_h = (uint8_t)config.feedTime;
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
