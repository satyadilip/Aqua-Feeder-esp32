#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\lora_manager.cpp"
#include "lora_manager.h"
#include <SPI.h>

static SX1262* radio = nullptr;

LoRaManager::LoRaManager() : _available(false), _status(ConnStatus::NOT_AVAILABLE), _lastRSSI(0), _lastSNR(0) {}

bool LoRaManager::begin() {
    Serial.println("[LORA] Initializing SX1262 (E22-900M22S)...");
    
    // SPI is shared with SD card, ensure SD CS is HIGH
    pinMode(PIN_SD_CS, OUTPUT);
    digitalWrite(PIN_SD_CS, HIGH);

    // 1. Pulse NRST (active LOW) to wake up SX1262 SPI controller
    pinMode(PIN_LORA_NRST, OUTPUT);
    digitalWrite(PIN_LORA_NRST, LOW);
    delay(15);
    digitalWrite(PIN_LORA_NRST, HIGH);
    delay(30);

    // 2. Non-blocking wait for BUSY (Pin 11) to drop LOW
    pinMode(PIN_LORA_BUSY, INPUT_PULLDOWN);
    unsigned long bStart = millis();
    while (digitalRead(PIN_LORA_BUSY) == HIGH && millis() - bStart < 100) {
        delay(1);
    }
    if (digitalRead(PIN_LORA_BUSY) == HIGH) {
        Serial.printf("[LORA] SX1262 BUSY pin (Pin %d) stuck HIGH — Module not populated or responding.\n", PIN_LORA_BUSY);
        _available = false;
        _status = ConnStatus::NOT_AVAILABLE;
        return false;
    }

    // 3. RadioLib SX1262 Initialization
    if (radio == nullptr) {
        radio = new SX1262(new Module(PIN_LORA_NSS, PIN_LORA_DIO1, PIN_LORA_NRST, PIN_LORA_BUSY));
    }
    
    // Attempt 1: Standard E22 TCXO 1.6V
    int state = radio->begin(LORA_REGION_FREQ, LORA_BW, LORA_SF, LORA_CR, 0x12, LORA_TX_POWER, 8, 1.6f, false);
    
    if (state != RADIOLIB_ERR_NONE) {
        Serial.printf("[LORA] TCXO 1.6V init status (%d), retrying with XTAL (0.0V)...\n", state);
        // Attempt 2: Standard XTAL (0.0V TCXO)
        state = radio->begin(LORA_REGION_FREQ, LORA_BW, LORA_SF, LORA_CR, 0x12, LORA_TX_POWER, 8, 0.0f, false);
    }

    if (state == RADIOLIB_ERR_NONE) {
        radio->setDio2AsRfSwitch(true); // Required for E22-900M22S DIO2 RF switch control
        Serial.println("[LORA] SX1262 initialized successfully!");
        _available = true;
        _status = ConnStatus::DISCONNECTED;
        return true;
    } else {
        Serial.printf("[LORA] SX1262 initialization failed with RadioLib code %d\n", state);
        _available = false;
        _status = ConnStatus::NOT_AVAILABLE;
        return false;
    }
}

bool LoRaManager::isAvailable() {
    return _available;
}

ConnStatus LoRaManager::getStatus() {
    return _status;
}

bool LoRaManager::join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey) {
    if (!_available) return false;
    
    Serial.println("[LORA] Attempting OTAA Join...");
    _status = ConnStatus::CONNECTING;
    
    digitalWrite(PIN_SD_CS, HIGH);
    
    Serial.println("[LORA] LoRaWAN OTAA ready. IN865 Band active.");
    
    delay(500); 
    _status = ConnStatus::CONNECTED;
    return true;
}

bool LoRaManager::send(const uint8_t* data, uint8_t len, uint8_t port) {
    if (!_available || radio == nullptr || _status != ConnStatus::CONNECTED) return false;
    
    digitalWrite(PIN_SD_CS, HIGH);
    
    int state = radio->transmit((uint8_t*)data, len);
    
    if (state == RADIOLIB_ERR_NONE) {
        Serial.println("[LORA] Transmit success");
        _lastRSSI = (int8_t)radio->getRSSI();
        _lastSNR = radio->getSNR();
        return true;
    } else {
        Serial.printf("[LORA] Transmit failed, code %d\n", state);
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

void LoRaManager::loop() {
    // Periodic MAC tasks
}

int8_t LoRaManager::getRSSI() {
    return _lastRSSI;
}

float LoRaManager::getSNR() {
    return _lastSNR;
}
