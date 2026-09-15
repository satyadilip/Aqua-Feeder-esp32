#pragma once

#include <Arduino.h>
#include <RadioLib.h>
#include "config.h"

class LoRaManager {
public:
    LoRaManager();

    void clearNonces();
    bool begin();
    bool isAvailable();
    ConnStatus getStatus();
    
    // OTAA join. Blocking up to LORA_JOIN_TIMEOUT_S. Return success.
    bool join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey);
    
    // Key Extraction for CLI
    uint32_t getDevAddr();
    void getSessionKeys(uint8_t* nwkSKey, uint8_t* appSKey);

    // Send uplink on specified port. Return true if ACK received or unconfirmed sent.
    bool send(const uint8_t* data, uint8_t len, uint8_t port);
    
    // Pack into LoRaUplinkPayload and send on port 1.
    bool sendTelemetry(const TelemetryEvent& event);
    
    // Pack into LoRaSettingsPayload and send on port 1.
    bool sendSettings(const DeviceConfig& config);
    
    // Handle LoRaWAN MAC events (RX windows, etc.)
    void loop();
    
    // Set callback for incoming downlinks
    void setDownlinkCallback(void (*cb)(const LoRaDownlinkPayload&));
    
    // Link quality
    int8_t getRSSI();
    float getSNR();

private:
    bool _available;
    ConnStatus _status;
    int8_t _lastRSSI;
    float _lastSNR;
    LoRaWANNode* _node;
    void (*_downlinkCb)(const LoRaDownlinkPayload&);
};
