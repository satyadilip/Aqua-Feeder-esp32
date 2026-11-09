#pragma once

#include <Arduino.h>
#include <RadioLib.h>
#include "config.h"

// Custom LoRaWANNode subclass providing runtime access to protected rxDelays
class CustomLoRaWANNode : public LoRaWANNode {
public:
    CustomLoRaWANNode(PhysicalLayer* phy, const LoRaWANBand_t* band) : LoRaWANNode(phy, band) {}
    void setRxDelay1(uint32_t delaySec) {
        rxDelays[1] = (RadioLibTime_t)delaySec * 1000;
        rxDelays[2] = rxDelays[1] + 1000;
    }
    uint32_t getRxDelay1() const {
        return rxDelays[1];
    }
};

class LoRaManager {
public:
    LoRaManager();

    void clearNonces();
    bool begin();
    bool isAvailable();
    ConnStatus getStatus();
    
    // LoRaWAN network join (0 = AUTO_FALLBACK, 1 = OTAA_ONLY, 2 = ABP_ONLY)
    bool join(const uint8_t* devEUI, const uint8_t* appEUI, const uint8_t* appKey, uint8_t mode = 0);
    
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
    
    // Class C / Class A dynamic day-night switching
    void setClassMode(uint8_t lwClass);
    uint8_t getClassMode();
    void checkDayNightMode(uint8_t hour);
    
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
    CustomLoRaWANNode* _node;
    void (*_downlinkCb)(const LoRaDownlinkPayload&);
};
