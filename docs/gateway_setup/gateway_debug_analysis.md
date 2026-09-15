# SenseCAP M2 Gateway AWS IoT Core Integration Debug Analysis

This document details the issues, root causes, and solutions discovered while attempting to connect a SenseCAP M2 LoRaWAN Gateway to AWS IoT Core for LoRaWAN using Basic Station.

## 1. The "Connection was reset by peer" CUPS Error

**Symptom:**
When the Gateway attempted to connect to the AWS IoT Core CUPS (Configuration and Update Server) endpoint (`https://A3AIZAWV83NXIH.cups.lorawan.us-east-1.amazonaws.com:443`), the gateway successfully parsed the AWS TLS certificates, established a TCP connection, and sent its HTTP POST request. However, exactly 1 second later, AWS would forcefully drop the connection, and the gateway logged: `[AIO:ERRO] [3] Send failed: NET - Connection was reset by peer`.

**Root Cause 1: Firmware String Formatting Bug**
The physical SenseCAP M2 Gateway EUI (MAC address) contained a zero immediately following a 16-bit block boundary (e.g., the block `0354`). The SenseCAP Web UI correctly accepted the 16-character string `2CF7F11080100354`. However, an internal script in the SenseCAP firmware used a buggy string formatting function (`sprintf("%x:%x:%x:%x", ...)`) to convert this string into the internal `station.conf` JSON payload. 

Because it used `%x` instead of `%04x`, it dropped the leading zero, resulting in `2cf7:f110:8010:354`.
When this 15-character EUI was sent to AWS via the CUPS request payload, AWS IoT Core immediately rejected it because a LoRaWAN Gateway EUI must be exactly 16 hexadecimal characters.

**Solution 1: EUI Workaround**
Because we cannot directly patch the compiled internal firmware script without deeper root SSH access and risking a brick, we bypassed the bug entirely by registering a "Virtual" Gateway EUI in AWS IoT Core that contained no leading zeros. 
We changed the EUI in both AWS and the Web UI to `2CF7F11080101354` (replacing the `0` with a `1`). The buggy formatting script output `2cf7:f110:8010:1354`, which perfectly matches the 16 characters `2cf7f11080101354` when colons are stripped. AWS accepted the payload.

**Root Cause 2: Missing AWS IoT Wireless Certificate Association**
Even after fixing the EUI length, AWS still forcefully reset the connection. 
In a standard AWS IoT Core MQTT setup, you only need to attach an AWS Certificate to an IoT Thing. However, AWS IoT Core *for LoRaWAN* requires the certificate to be explicitly associated with the `WirelessGateway` entity in a completely separate internal database used by the CUPS service.
The original automated scripts ran `iot.attach_thing_principal` but failed to run the crucial `iotwireless.associate_wireless_gateway_with_certificate` API call.

**Solution 2: Boto3 Association**
We explicitly ran `iotwireless.associate_wireless_gateway_with_certificate(Id=gateway_id, IotCertificateId=cert_id)` on the backend. This instantly authorized the gateway's TLS handshake in the CUPS server.

## 2. The "No CUPS URI Configured" Error

**Symptom:**
After modifying the EUI in the Web UI, the gateway failed to start with the error `[CUP:ERRO] No CUPS URI configured`.

**Root Cause:**
The SenseCAP Web UI is prone to silent failures when saving settings, especially if the user accidentally adds a trailing space or a duplicate port (`:443:443`). When the UI fails validation silently in the background, it erases the URI from the internal UCI (Unified Configuration Interface) database. 

**Solution:**
We wrote a custom Python script (`fix_uri.py`) that bypassed the Web UI and sent an RPC command directly to the gateway's internal UBUS interface, forcefully hardcoding the `cups_boot` server mode and the correct `cups.uri` directly into the database.

## Key Understandings Acquired
1. **CUPS is Mandatory for AWS**: Attempting to connect directly to the AWS LNS endpoint (WebSockets) using standard TLS certificates fails because AWS IoT Core expects a dynamically generated `station.conf` and a temporary SigV4 token that can *only* be acquired by booting through the CUPS server first. 
2. **Double Association**: AWS IoT certificates for LoRaWAN gateways must be associated with the IoT Thing AND the Wireless Gateway.
3. **Web UI Instability**: The SenseCAP M2 Web UI cannot be fully trusted to write complex UCI configurations properly, making UBUS Python scripts highly valuable for debugging and overriding settings.
