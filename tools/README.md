# AquaFeeder Technician Scripts

This directory contains Python scripts designed for field technicians and developers to manage, diagnose, and flash AquaFeeder ESP32-S3 nodes.

## Requirements
These scripts require Python 3 and the `pyserial` module.
```cmd
python -m pip install pyserial
```

## Scripts Overview

### `read_node_status.py`
This script connects to the node over Serial, reboots it, authenticates with the `1234` PIN, and prints out a clean, live log of the device's boot process and telemetry events.
**Usage:**
```cmd
python read_node_status.py
```
- It will automatically scan for available COM ports and ask you to select one.
- Use this to verify LoRaWAN connectivity (`LoRaWAN OTAA Session active! Joined successfully.`).

### `erase_lora_node.py`
This script connects to the node, authenticates, and sends the `ERASE LORA` command to wipe the LoRaWAN nonces and DevEUI from the Non-Volatile Storage (NVS).
**Usage:**
```cmd
python erase_lora_node.py
```
- Use this when a node fails to join the network and gets rate-limited/blacklisted by AWS IoT Core. Erasing the node forces it to forget its previous session and attempt a fresh OTAA Join.

### `batch_compile.py`
This script automates the process of compiling firmware binaries for multiple nodes. It dynamically modifies the `lora_manager.cpp` and `config_manager.cpp` to set the unique DevEUI and DevAddr for Nodes 1 through 5, and invokes the `arduino-cli` to compile them.
**Usage:**
```cmd
python batch_compile.py
```
- The output binaries are saved in `AquaFeeder/build/` as `AquaFeeder_Node_1.bin` through `AquaFeeder_Node_5.bin`.
- Ensure `arduino-cli` is installed and the `esp32:esp32:esp32s3` core is downloaded before running.
