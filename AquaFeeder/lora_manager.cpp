#include "lora_manager.h"

#include <SPI.h>

#include <Preferences.h>



Preferences loraPrefs;



static SX1262* radio = nullptr;

static CustomLoRaWANNode* node = nullptr;

static uint32_t currentDevAddr = 0;

static uint8_t currentAppKey[16];



LoRaManager::LoRaManager() : _available(false), _status(ConnStatus::NOT_AVAILABLE), _lastRSSI(0), _lastSNR(0), _node(nullptr), _downlinkCb(nullptr) {}



void LoRaManager::clearNonces() {
    loraPrefs.begin("lorawan", false);
    loraPrefs.clear();
    loraPrefs.end();
    Serial.println("[LORA] LoRaWAN Nonces & Session CLEARED from NVS.");
}



bool LoRaManager::begin() {

    Serial.println("[LORA] Initializing SX1262 for LoRaWAN Public Network (IN865 Band)...");

    

    pinMode(PIN_SD_CS, OUTPUT);

    digitalWrite(PIN_SD_CS, HIGH);



    pinMode(PIN_LORA_NSS, OUTPUT);

    digitalWrite(PIN_LORA_NSS, HIGH);



    // Pull BUSY pin down so if module is missing/unpowered, it never floats HIGH and hangs RadioLib

    pinMode(PIN_LORA_BUSY, INPUT_PULLDOWN);



    // Hardware Reset pulse

    pinMode(PIN_LORA_NRST, OUTPUT);

    digitalWrite(PIN_LORA_NRST, LOW);

    delay(20);

    digitalWrite(PIN_LORA_NRST, HIGH);

    delay(50);



    // Fast check: Wait for BUSY line to drop LOW (max 80ms)

    unsigned long busyStart = millis();

    while (digitalRead(PIN_LORA_BUSY) == HIGH && (millis() - busyStart < 80)) {

        delay(5);

    }

    if (digitalRead(PIN_LORA_BUSY) == HIGH) {

        Serial.println("[LORA] SX1262 BUSY line held HIGH — hardware not responding.");

        _available = false;

        _status = ConnStatus::NOT_AVAILABLE;

        return false;

    }



    SPI.end();

    SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);



    // Fast SPI probe: Read SX1262 status (Opcode 0xC0)

    digitalWrite(PIN_LORA_NSS, LOW);

    SPI.transfer(0xC0); // GetStatus

    uint8_t chipStatus = SPI.transfer(0x00);

    digitalWrite(PIN_LORA_NSS, HIGH);



    if (chipStatus == 0x00 || chipStatus == 0xFF) {

        Serial.printf("[LORA] SX1262 SPI check failed (status: 0x%02X). Chip not detected.\n", chipStatus);

        _available = false;

        _status = ConnStatus::NOT_AVAILABLE;

        return false;

    }



    if (radio == nullptr) {

        radio = new SX1262(new Module(PIN_LORA_NSS, PIN_LORA_DIO1, PIN_LORA_NRST, PIN_LORA_BUSY));

    }

    

    // LoRaWAN Public Sync Word: 0x34 (RADIOLIB_SX126X_SYNC_WORD_PUBLIC)

    int state = radio->begin(865.0625f, 125.0f, 7, 5, 0x34, 14, 8, 1.6f, false);

    if (state != RADIOLIB_ERR_NONE) {

        state = radio->begin(865.0625f, 125.0f, 7, 5, 0x34, 14, 8, 0.0f, false);

    }



    if (state != RADIOLIB_ERR_NONE) {

        Serial.printf("[LORA] SX1262 init failed (RadioLib code: %d). Module offline.\n", state);

        _available = false;

        _status = ConnStatus::NOT_AVAILABLE;

        return false;

    }



    // Configure RF switch on AG_V1 board (GPIO 14 controls RXEN)
    radio->setRfSwitchPins(PIN_LORA_DIO2, RADIOLIB_NC);
    radio->setDio2AsRfSwitch(true); // Keep internal DIO2 switch enabled for TX

    if (node == nullptr) {
        node = new CustomLoRaWANNode(radio, &IN865);
    }
    _node = node;
    _node->scanGuard = 150; // 150ms window padding tolerance for clock drift & jitter

    

    Serial.println("[LORA] SX1262 Radio initialized successfully!");

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



bool LoRaManager::join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey, uint8_t mode) {
    if (!_available || _node == nullptr) return false;
    
    memcpy(currentAppKey, appKey, 16);
    _status = ConnStatus::CONNECTING;
    digitalWrite(PIN_SD_CS, HIGH);

    loraPrefs.begin("lorawan", false);

    // 1. Determine DevAddr deterministically from silicon MAC in devEUI (Zero Hardcoding!)
    // devEUI structure: [mac0, mac1, mac2, 0xFF, 0xFE, mac3, mac4, mac5]
    // Any custom DevAddr previously set via CLI/portal takes precedence if configured (> 0)
    uint32_t devAddr = loraPrefs.getUInt("devAddr", 0);
    if (devAddr == 0) {
        if (devEUI[2] == 0xA1 && devEUI[3] == 0xF6) {
            devAddr = ((uint32_t)devEUI[1] << 16) | ((uint32_t)devEUI[2] << 8) | ((uint32_t)devEUI[3]);
        } else {
            devAddr = ((uint32_t)devEUI[1] << 16) | ((uint32_t)devEUI[6] << 8) | ((uint32_t)devEUI[7]);
        }
    }
    currentDevAddr = devAddr;

    uint64_t joinEUI_u64 = 0;
    for(int i=0; i<8; i++) { joinEUI_u64 = (joinEUI_u64 << 8) | appEUI[i]; }
    uint64_t devEUI_u64 = 0;
    for(int i=0; i<8; i++) { devEUI_u64 = (devEUI_u64 << 8) | devEUI[i]; }

    // 2. Attempt OTAA if mode is AUTO_FALLBACK (0) or OTAA_ONLY (1)
    if (mode == 0 || mode == 1) {
        Serial.println("[LORA] Configuring LoRaWAN OTAA Session (IN865 Band)...");
        _node->beginOTAA(joinEUI_u64, devEUI_u64, nullptr, (uint8_t*)appKey);
        _node->scanGuard = 150; // 150ms window padding tolerance

        // Restore nonces (DevNonce, JoinNonce)
        size_t noncesLen = loraPrefs.getBytesLength("nonces");
        if (noncesLen == RADIOLIB_LORAWAN_NONCES_BUF_SIZE) {
            uint8_t bufferNonces[RADIOLIB_LORAWAN_NONCES_BUF_SIZE];
            loraPrefs.getBytes("nonces", bufferNonces, RADIOLIB_LORAWAN_NONCES_BUF_SIZE);
            _node->setBufferNonces(bufferNonces);
            Serial.println("[LORA] Restored LoRaWAN Nonces from NVS.");
        }

        _node->setDutyCycle(false);
        int16_t state = RADIOLIB_ERR_UNKNOWN;
        for (uint8_t attempt = 1; attempt <= 3; attempt++) {
            Serial.printf("[LORA] Joining OTAA network (Attempt %d of 3)...\n", attempt);
            state = _node->activateOTAA();

            // Always save updated nonces
            uint8_t* currentNonces = _node->getBufferNonces();
            loraPrefs.putBytes("nonces", currentNonces, RADIOLIB_LORAWAN_NONCES_BUF_SIZE);

            if (state == RADIOLIB_ERR_NONE || state == -1118 || state == -1117 || state >= 0) {
                Serial.printf("[LORA] LoRaWAN OTAA Session ACTIVE! Joined successfully on attempt %d.\n", attempt);
                currentDevAddr = _node->getDevAddr();
                _status = ConnStatus::CONNECTED;
                loraPrefs.end();
                return true;
            }

            Serial.printf("[LORA] OTAA attempt %d failed, status code: %d\n", attempt, state);
            if (attempt < 3) {
                delay(2000);
            }
        }

        if (mode == 1) { // OTAA_ONLY
            _status = ConnStatus::DISCONNECTED;
            loraPrefs.end();
            return false;
        }

        // Mode 0: AUTO_FALLBACK triggered!
        Serial.println("[LORA] OTAA Join timed out after 3 attempts — initiating seamless ABP fallback...");
    }

    // 3. ABP Activation (Instant & Zero Dependency on Gateway Downlink Jitter)
    Serial.printf("[LORA] Activating LoRaWAN ABP Session (IN865 Band, DevAddr: 0x%08X)...\n", devAddr);
    _node->beginABP(devAddr, nullptr, nullptr, (uint8_t*)appKey, (uint8_t*)appKey);
    _node->scanGuard = 150;

    size_t sessionLen = loraPrefs.getBytesLength("session");
    if (sessionLen == RADIOLIB_LORAWAN_SESSION_BUF_SIZE) {
        uint8_t bufferSession[RADIOLIB_LORAWAN_SESSION_BUF_SIZE];
        loraPrefs.getBytes("session", bufferSession, RADIOLIB_LORAWAN_SESSION_BUF_SIZE);
        int16_t restState = _node->setBufferSession(bufferSession);
        if (restState == RADIOLIB_ERR_NONE) {
            Serial.printf("[LORA] Restored ABP Session from NVS (fCntUp: %u).\n", _node->getFCntUp());
        }
    }

    _node->setDutyCycle(false);
    int16_t abpState = _node->activateABP();

    if (abpState == RADIOLIB_ERR_NONE || abpState == RADIOLIB_LORAWAN_NEW_SESSION || abpState == RADIOLIB_LORAWAN_SESSION_RESTORED || abpState >= 0) {
        Serial.printf("[LORA] LoRaWAN ABP Session ACTIVE! Joined successfully (fCntUp: %u).\n", _node->getFCntUp());
        uint8_t* curSession = _node->getBufferSession();
        loraPrefs.putBytes("session", curSession, RADIOLIB_LORAWAN_SESSION_BUF_SIZE);
        loraPrefs.end();
        _status = ConnStatus::CONNECTED;
        return true;
    } else {
        Serial.printf("[LORA] activateABP failed, status code: %d\n", abpState);
        loraPrefs.end();
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
    _node->scanGuard = 150; // Ensure 150ms window padding tolerance

    Serial.printf("[LORA] Transmitting %d bytes (Port %d, RX1: %ums, RX2: %ums)... ", 
                  len, port, _node->getRxDelay1(), _node->getRxDelay1() + 1000);

    uint8_t downData[256];
    size_t downLen = 0;

    int16_t state = _node->sendReceive((uint8_t*)data, len, port, downData, &downLen, false);

    Serial.printf("state = %d\n", state);

    if (state == RADIOLIB_ERR_NONE || state >= 0) {
        Serial.println("[LORA] Uplink SUCCESS!");

        loraPrefs.begin("lorawan", false);
        uint8_t* curSession = _node->getBufferSession();
        loraPrefs.putBytes("session", curSession, RADIOLIB_LORAWAN_SESSION_BUF_SIZE);
        loraPrefs.end();

        if (state == 1) {
            Serial.println("[LORA] >>> DOWNLINK RECEIVED IN RX1 WINDOW! <<<");
        } else if (state == 2) {
            Serial.println("[LORA] >>> DOWNLINK RECEIVED IN RX2 WINDOW! <<<");
        } else if (state == 0) {
            Serial.println("[LORA] No downlink received in either RX1 or RX2 window.");
        }

        if (downLen > 0) {
            Serial.printf("[LORA] Received %d bytes of downlink payload: ", downLen);
            for (size_t b = 0; b < downLen && b < 16; b++) Serial.printf("%02X ", downData[b]);
            Serial.println();

            if (downLen == sizeof(LoRaDownlinkPayload) && _downlinkCb != nullptr) {
                LoRaDownlinkPayload dl;
                memcpy(&dl, downData, downLen);
                if (dl.msgType == (uint8_t)CommandMsgType::CMD_SET_SETTINGS || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_POLL_DATA || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_TEST_MOTOR || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_SYNC_TIME || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_START_FEED || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_STOP_FEED || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_RESUME_FEED || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_OTA_START || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_OTA_CHUNK || 
                    dl.msgType == (uint8_t)CommandMsgType::CMD_OTA_APPLY) {
                    Serial.printf("[LORA] Executing Downlink Callback for MsgType 0x%02X...\n", dl.msgType);
                    _downlinkCb(dl);
                } else {
                    Serial.printf("[LORA] Unknown Downlink MsgType (0x%02X) ignored. Raw %d bytes: ", dl.msgType, downLen);
                    for (size_t b = 0; b < downLen && b < 16; b++) Serial.printf("%02X ", downData[b]);
                    Serial.println();
                }
            } else if (downLen > 0) {
                Serial.printf("[LORA] Downlink size mismatch (%d vs %d) ignored\n", downLen, sizeof(LoRaDownlinkPayload));
            }
        }

        _lastRSSI = (int8_t)radio->getRSSI();
        _lastSNR = radio->getSNR();
        return true;
    } else {
        Serial.printf("[LORA] Uplink/Downlink FAILED (RadioLib code: %d)\n", state);
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
    payload.reserved = FW_VERSION_BYTE; // 0x10 -> v1.0

    

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



void LoRaManager::setClassMode(uint8_t lwClass) {
    if (_node == nullptr || !_available) return;
    uint8_t currentCls = _node->getClass();
    if (currentCls == lwClass) return;

    int16_t state = _node->setClass(lwClass);
    Serial.printf("[LORA] Switching Operating Class: %s (RadioLib code: %d)\n",
                  lwClass == RADIOLIB_LORAWAN_CLASS_C ? "CLASS C (Continuous RX)" : "CLASS A (Low Power)", state);
}

uint8_t LoRaManager::getClassMode() {
    if (_node == nullptr || !_available) return RADIOLIB_LORAWAN_CLASS_A;
    return _node->getClass();
}

void LoRaManager::checkDayNightMode(uint8_t hour) {
    // Keep in Class A to strictly synchronize with AWS IoT Core Wireless Class A ABP profile
    setClassMode(RADIOLIB_LORAWAN_CLASS_A);
}

void LoRaManager::loop() {
    if (_node == nullptr || !_available || _status != ConnStatus::CONNECTED) return;

    // In Class C (Daylight operation), poll for downlinks directly from the radio receiver
    if (_node->getClass() == RADIOLIB_LORAWAN_CLASS_C) {
        static unsigned long lastClassCPoll = 0;
        if (millis() - lastClassCPoll >= 100) { // Check every 100ms
            lastClassCPoll = millis();
            uint8_t downData[256];
            size_t downLen = 0;
            int16_t state = _node->getDownlinkClassC(downData, &downLen);
            if (state == RADIOLIB_ERR_NONE && downLen > 0) {
                Serial.printf("[LORA-ClassC] Immediate Downlink Received! (%d bytes)\n", downLen);
                if (downLen == sizeof(LoRaDownlinkPayload) && _downlinkCb != nullptr) {
                    LoRaDownlinkPayload dl;
                    memcpy(&dl, downData, downLen);
                    _downlinkCb(dl);
                }
            }
        }
    }
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

