#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\lora_manager.h"
#pragma once

#include <Arduino.h>
#include <RadioLib.h>
#include "config.h"

class LoRaManager {
public:
    LoRaManager();

    bool begin();
    bool isAvailable();
    ConnStatus getStatus();
    
    // OTAA join. Blocking up to LORA_JOIN_TIMEOUT_S. Return success.
    bool join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey);
    
    // Send uplink on specified port. Return true if ACK received or unconfirmed sent.
    bool send(const uint8_t* data, uint8_t len, uint8_t port);
    
    // Pack into LoRaUplinkPayload and send on port 1.
    bool sendTelemetry(const TelemetryEvent& event);
    
    // Handle LoRaWAN MAC events (RX windows, etc.)
    void loop();
    
    // Link quality
    int8_t getRSSI();
    float getSNR();

private:
    bool _available;
    ConnStatus _status;
    int8_t _lastRSSI;
    float _lastSNR;
};
