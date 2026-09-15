# AquaFeeder LoRaWAN Connectivity Fix - Knowledge Base

This document outlines the root causes and solutions for the LoRaWAN connectivity issues experienced by the AquaFeeder nodes on the IN865 band.

## Symptoms
- Nodes failed to join the AWS IoT Core network via the SenseCAP Gateway.
- Node logs showed `[LORA] activateOTAA failed, status code: -1118` (or `-1116`).
- Nodes were repeatedly transmitting Join Requests every 30 seconds, leading to AWS IoT Core rate-limiting / blacklisting the DevEUI.
- Node firmware failed to update the DevEUI via NVS even when the Erase Script was run.

## Root Causes & Solutions

### 1. RF Switch Pin Configuration
**Problem:** The custom AG_V1 hardware uses a GPIO pin (GPIO 14) to toggle the antenna's RF switch (TX/RX state) on the E22-900M22S (SX1262) module. RadioLib was not automatically toggling this pin during transmission and reception, leading to failed downlink reception (the node could transmit Join Requests, but could not physically receive the Join Accept from the gateway).
**Fix:** Explicitly configured the RF switch pin in `lora_manager.cpp` during initialization:
```cpp
// PIN_LORA_DIO2 is defined as 14
radio->setRfSwitchPins(PIN_LORA_DIO2, RADIOLIB_NC);
```

### 2. RadioLib MAC State Handling (`-1118`)
**Problem:** `RadioLib` defines status code `-1118` as `RADIOLIB_LORAWAN_NEW_SESSION`. This status code is returned by `activateOTAA()` when the Node **successfully** receives and decrypts a Join Accept, establishing a new active session. However, the legacy firmware logic treated `-1118` as a generic failure, causing the node to discard the successful Join Accept and retry the Join process infinitely.
**Fix:** Updated the `activateOTAA` state check in `lora_manager.cpp` to correctly interpret `-1118` and `-1117` (Session Restored) as success states.
```cpp
if (state == RADIOLIB_ERR_NONE || state == -1118 || state == -1117 || state >= 0) {
    // Success
}
```

### 3. NVS Nonce Retention & DevEUI Blacklisting
**Problem:** AWS IoT Core has strict protections against Join Request replay attacks. Rapidly retrying Join Requests (caused by bug #2) caused AWS to silently drop subsequent Join Requests for 15+ minutes. To bypass this, we needed to issue a new DevEUI to the Node. However, the Node was stubbornly retaining the old DevEUI and Nonces in NVS, causing the OTAA join to fail instantly.
**Fix:** We updated the `clearNonces()` function in `lora_manager.cpp` to explicitly clear the `lorawan` NVS namespace. We then exposed the `ERASE LORA` command via the Serial Port, allowing technicians to factory-reset the LoRa credentials dynamically.

## Summary
The combination of physically enabling the RF switch for reception, correctly interpreting RadioLib's "New Session" success code, and providing a clean mechanism to erase NVS nonces fully resolved the OTAA Join failures.
