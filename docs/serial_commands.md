# AquaFeeder Serial Command Reference

The AquaFeeder nodes support a diagnostic and configuration serial interface. By default, the terminal listens on the USB Serial port at `115200` baud. Commands must be terminated with a newline (`\n` or `\r\n`).

## Authentication
By default, the serial interface is locked to prevent unauthorized tampering.

### `AUTH <PIN>`
- **Description:** Unlocks the serial interface for 15 minutes.
- **Example:** `AUTH 1234`
- **When to use:** Required before running any diagnostic or configuration commands. The default PIN is `1234`.

## Diagnostic Commands
Once authenticated, the following commands are available:

### `DIAG`
- **Description:** Runs a full hardware self-test on the I2C and SPI buses.
- **Output:** Prints a formatted table indicating the pass/fail status of the RTC, Power Monitor, LCD, LoRa Module, MicroSD Card, GSM Modem, Push Buttons, and Optocoupler.
- **When to use:** Use this when a newly assembled node is powered on for the first time, or if a specific hardware component (like the display or motor) is failing.

### `TEST MOTOR <1|2>`
- **Description:** Engages the specified motor for a brief 2-second burst.
- **Example:** `TEST MOTOR 1`
- **When to use:** Use this to verify that the motor drivers and relays are wired correctly and that the auger is free of jams.

### `TEST LORA`
- **Description:** Transmits a generic ping payload over the LoRaWAN interface to verify connectivity.
- **When to use:** Use to check signal strength (RSSI/SNR) on the gateway or AWS IoT Core without waiting for a scheduled feed cycle.

### `TEST GSM`
- **Description:** Issues AT commands to the SIM800L module to verify SIM card presence and network registration.
- **When to use:** Use when the LoRa network is unavailable and you need to troubleshoot GPRS fallback connectivity.

## Configuration Commands

### `SET ID <serial>`
- **Description:** Updates the human-readable Device ID of the node (e.g., `AF_9C2472E0`).
- **Example:** `SET ID AF_1234ABCD`
- **When to use:** Use during initial provisioning to assign a unique asset tag to the node.

### `ERASE LORA`
- **Description:** Completely clears the LoRaWAN OTAA nonces and session keys from the Non-Volatile Storage (NVS).
- **When to use:** Use this if the node is stuck in a join loop, if AWS IoT Core has blacklisted the current session due to rapid retries, or if you need to force the node to perform a completely fresh OTAA Join procedure. After running this command, you **must** reboot the node.

### `REBOOT`
- **Description:** Triggers a software reset of the ESP32 microcontroller.
- **When to use:** Use to apply new configurations, or after running `ERASE LORA`.

## Basic Navigation
### `H` or `HELP`
- **Description:** Lists all available commands and their current lock status.
