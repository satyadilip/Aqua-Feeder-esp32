#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\config.h"
// ============================================================================
// AQUA FEEDER AG_V1 — Central Configuration Header
// ============================================================================
// Platform: YD-ESP32-S3 N16R8 (16MB Flash, 8MB PSRAM)
// Board:    AG_V1 (Athena Engineering Corp)
// ============================================================================
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ── FIRMWARE VERSION ────────────────────────────────────────────────────────
#define FW_VERSION        "4.0.0"
#define FW_NAME           "Aqua Feeder AG_V1"
#define FW_BUILD_DATE     __DATE__
#define FW_BUILD_TIME     __TIME__

// ── GPIO PIN DEFINITIONS (AG_V1 Schematic) ──────────────────────────────────

// Relay Outputs (Active HIGH)
#define PIN_RELAY_LOADER    41    // RLY1 — Loader Motor
#define PIN_RELAY_DISPENSER 39    // RLY2 — Dispenser Motor
#define PIN_HOOTER          38    // Alarm Horn / Buzzer

// Status LEDs (Active HIGH)
#define PIN_LED_RED         40    // STAT1 — Red  (Error / Fault)
#define PIN_LED_GREEN       42    // STAT2 — Green (Heartbeat / OK)

// Button Inputs (Active LOW, external pull-up 1kΩ)
#define PIN_BTN_UP          4     // SW1 — Navigation UP
#define PIN_BTN_DOWN        5     // SW2 — Navigation DOWN
#define PIN_BTN_SELECT      6     // SW3 — SELECT / Confirm
#define PIN_BTN_CONFIG      7     // SW4 — AP Config Mode / Back

// Proximity Sensor (Active LOW, PC817 optocoupler, pull-up 10kΩ)
#define PIN_PROXIMITY       16    // PROX-SW — Hopper obstruction sensor

// I2C Bus (Shared: DS3231 RTC, INA219, JHD629-204A LCD)
#define PIN_I2C_SDA         8     // I2C Data
#define PIN_I2C_SCL         9     // I2C Clock

// SPI Bus (Shared: LoRa SX1262, MicroSD)
#define PIN_SPI_SCK         21    // SPI Clock
#define PIN_SPI_MOSI        47    // ESP32 Pin 47 → U4 Pin 17 (MOSI)
#define PIN_SPI_MISO        48    // ESP32 Pin 48 → U4 Pin 16 (MISO)

// MicroSD Card
#define PIN_SD_CS           15    // SD Chip Select (Active LOW)

// LoRa E22-900M22S (SX1262)
#define PIN_LORA_NSS        13    // LoRa SPI Chip Select
#define PIN_LORA_BUSY       11    // SX1262 BUSY status
#define PIN_LORA_DIO1       10    // SX1262 Interrupt (DIO1)
#define PIN_LORA_DIO2       14    // SX1262 RF Switch (DIO2)
#define PIN_LORA_NRST       12    // SX1262 Hardware Reset

// SIM800L Cellular Modem (UART1)
#define PIN_GSM_RX          18    // ESP32 RX (Pin 18) ← SIM800L TX (Net GSM-TX)
#define PIN_GSM_TX          17    // ESP32 TX (Pin 17) → SIM800L RX (Net GSM-RX)
#define GSM_BAUD_RATE       9600  // SIM800L default baud

// ── I2C DEVICE ADDRESSES ────────────────────────────────────────────────────
#define I2C_ADDR_RTC        0x68  // DS3231 Real-Time Clock
#define I2C_ADDR_INA219     0x40  // INA219 Power Monitor
#define I2C_ADDR_LCD_PRIMARY 0x27 // PCF8574 LCD backpack (primary)
#define I2C_ADDR_LCD_ALT    0x3F  // PCF8574A LCD backpack (alternate)

// ── LCD PARAMETERS ──────────────────────────────────────────────────────────
#define LCD_COLS            20    // JHD629-204A columns
#define LCD_ROWS            4     // JHD629-204A rows

// ── FEED ENGINE DEFAULTS & LIMITS ───────────────────────────────────────────
#define FEED_QTY_DEFAULT    15.0f   // kg
#define FEED_QTY_MIN        0.5f
#define FEED_QTY_MAX        120.0f
#define FEED_QTY_STEP       0.5f

#define FEED_FPE_DEFAULT    100     // grams per event
#define FEED_FPE_MIN        10
#define FEED_FPE_MAX        500
#define FEED_FPE_STEP       5

#define FEED_TIME_DEFAULT   12      // hours (feed window duration)
#define FEED_TIME_MIN       1
#define FEED_TIME_MAX       12

#define FEED_RATE_DEFAULT   50      // grams/second (discharge rate)
#define FEED_RATE_MIN       1
#define FEED_RATE_MAX       100

#define FEED_START_HOUR_DEFAULT  6
#define FEED_START_MIN_DEFAULT   0

// Operational Window
#define OP_START_HOUR       6       // 06:00
#define OP_END_HOUR         18      // 18:00

// Motor Timing
#define MOTOR_PRE_RUN_MS    3000    // 3s dispenser warm-up
#define MOTOR_POST_RUN_MS   3000    // 3s dispenser clearance
#define MOTOR_MIN_RUN_MS    1000    // 1s minimum motor time
#define MOTOR_MIN_GAP_S     10      // 10s minimum gap between events

// INA219 Safety Thresholds
#define OVERCURRENT_LIMIT_MA 3500   // 3.5A motor overcurrent threshold
#define INA219_SAMPLE_MS     50     // Sample current every 50ms during dispense

// ── BUTTON DEBOUNCE ─────────────────────────────────────────────────────────
#define BUTTON_DEBOUNCE_MS  50      // Debounce interval
#define BUTTON_POLL_MS      20      // Button scan interval

// ── TELEMETRY ───────────────────────────────────────────────────────────────
#define TELEMETRY_INTERVAL_DEFAULT_S  1      // 1 second for live cloud testing
#define TELEMETRY_INTERVAL_MIN_S      1      // 1 second minimum
#define TELEMETRY_INTERVAL_MAX_S      86400  // 24 hours maximum
#define TELEMETRY_QUEUE_SIZE          32     // Max queued telemetry events
#define TELEMETRY_RETRY_COUNT         3      // Retry attempts per channel
#define TELEMETRY_RETRY_DELAY_MS      5000   // Delay between retries

// ── WIFI ────────────────────────────────────────────────────────────────────
#define WIFI_AP_SSID_DEFAULT   "AquaFeeder-Config"
#define WIFI_AP_PASS_DEFAULT   "aqua1234"
#define WIFI_AP_CHANNEL        1
#define WIFI_AP_MAX_CONN       4
#define WIFI_AP_IP             IPAddress(192, 168, 4, 1)
#define WIFI_WEB_PORT          80

// ── LoRaWAN (IN865) ─────────────────────────────────────────────────────────
#define LORA_REGION_FREQ       865.0  // IN865 base frequency MHz
#define LORA_BAND_IN865        true
#define LORA_TX_POWER          14     // dBm (max for IN865)
#define LORA_SF                7      // Spreading Factor
#define LORA_BW                125.0  // Bandwidth kHz
#define LORA_CR                5      // Coding Rate 4/5
#define LORA_JOIN_TIMEOUT_S    30     // OTAA join timeout
#define LORA_JOIN_RETRY_MAX    5      // Max join attempts before failover

// ── SIM800L APN PRESETS ─────────────────────────────────────────────────────
#define APN_AIRTEL             "airtelgprs.com"
#define APN_JIO                "jionet"
#define APN_VI                 "www"
#define APN_BSNL               "bsnlnet"

// ── SD CARD ─────────────────────────────────────────────────────────────────
#define SD_LOG_DIR             "/logs"
#define SD_TELEMETRY_FILE      "/logs/telemetry.csv"
#define SD_EVENT_FILE          "/logs/events.csv"
#define SD_MAX_FILE_SIZE_KB    4096   // Rotate after 4MB

// ── NVS NAMESPACE ───────────────────────────────────────────────────────────
#define NVS_NAMESPACE          "aquafeeder"

// ═══════════════════════════════════════════════════════════════════════════
// SHARED ENUMERATIONS
// ═══════════════════════════════════════════════════════════════════════════

// System-wide operational state
enum class SystemState : uint8_t {
    INIT = 0,
    IDLE,
    AP_CONFIG,
    FEED_PRE_WARMUP,
    FEED_DISPENSING,
    FEED_POST_CLEAR,
    FEED_WAIT_NEXT,
    FEED_PAUSED,
    FEED_FINISHED,
    ERROR_FATAL
};

// Feed cycle sub-states
enum class FeedCycleState : uint8_t {
    FC_IDLE = 0,
    FC_PRE,        // Dispenser pre-warmup
    FC_DISP,       // Loader + Dispenser active
    FC_POST,       // Post-clearance
    FC_WAIT        // Waiting for next event
};

// Cloud uplink channel priority
enum class UplinkMode : uint8_t {
    AUTO_FAILOVER = 0,  // LoRa → WiFi → GSM → SD
    LORAWAN_ONLY,
    WIFI_ONLY,
    GSM_ONLY
};

// Telemetry message types
enum class TelemetryMsgType : uint8_t {
    PERIODIC_HEARTBEAT = 0x01,
    SESSION_COMPLETE   = 0x02,
    FEED_STARTED       = 0x03,
    FEED_PAUSED        = 0x04,
    FEED_RESUMED       = 0x05,
    ALARM_OVERCURRENT  = 0x0E,
    ALARM_PROXIMITY    = 0x0F,
    ALARM_RTC_FAULT    = 0x10,
    DEVICE_BOOT        = 0x20,
    CONFIG_CHANGED     = 0x21
};

// Connection status for each channel
enum class ConnStatus : uint8_t {
    DISCONNECTED = 0,
    CONNECTING,
    CONNECTED,
    ERROR,
    NOT_AVAILABLE    // Hardware not detected
};

// Menu navigation states (LCD UI)
enum class MenuState : uint8_t {
    MAIN_STATUS = 0,
    MENU_LIST,
    EDIT_QTY,
    EDIT_FPE,
    EDIT_TIME,
    EDIT_START_TIME,
    EDIT_RATE,
    EDIT_CLOCK,
    RUNNING,
    PAUSED,
    FINISHED,
    INFO_NETWORK,
    INFO_POWER
};

// ═══════════════════════════════════════════════════════════════════════════
// SHARED DATA STRUCTURES
// ═══════════════════════════════════════════════════════════════════════════

// Persistent device configuration (stored in NVS)
struct DeviceConfig {
    // Feed parameters
    float    feedQuantity;       // kg
    int      feedPerEvent;       // grams
    int      feedTime;           // hours (feed window)
    int      startHour;
    int      startMinute;
    int      dischargeRate;      // grams/second

    // Telemetry
    uint32_t telemetryIntervalS; // Periodic uplink interval in seconds

    // Cloud uplink
    UplinkMode uplinkMode;

    // LoRaWAN (IN865)
    uint8_t  loraDevEUI[8];
    uint8_t  loraAppEUI[8];
    uint8_t  loraAppKey[16];
    bool     loraOTAA;           // true = OTAA, false = ABP

    // WiFi Station (for cloud MQTT)
    char     wifiSSID[33];
    char     wifiPass[65];
    char     mqttServer[65];     // AWS IoT endpoint
    uint16_t mqttPort;
    char     mqttClientId[33];

    // SIM800L / GSM
    char     gsmAPN[33];
    char     gsmUser[17];
    char     gsmPass[17];
    char     gsmMqttServer[65];
    uint16_t gsmMqttPort;

    // WiFi AP settings
    char     apSSID[33];
    char     apPass[33];

    // Device identity
    char     deviceId[33];

    // Overcurrent threshold (mA)
    uint16_t overcurrentLimit;
};

struct HardwareDiagnostics {
    bool ds3231_rtc;
    bool ina219_power;
    bool lcd_display;
    uint8_t lcd_i2c_addr;
    bool sd_card;
    bool lora_sx1262;
    bool gsm_sim800l;
    int gsm_csq;
    bool sw1_ok;
    bool sw2_ok;
    bool sw3_ok;
    bool sw4_ok;
    bool prox_sensor_clear;
    uint8_t i2c_count;
    uint8_t i2c_addrs[16];
};

// Real-time system status (not persisted)
struct SystemStatus {
    SystemState     state;
    FeedCycleState  feedState;
    bool            feedActive;
    int             currentEvent;
    long            totalEvents;
    bool            scheduleValid;
    char            schedError[32];

    // Timing
    unsigned long   motorTimeMs;
    unsigned long   intervalMs;
    uint32_t        nextFeedEpoch;      // Next feed start (epoch seconds)

    // Sensor readings
    float           voltageV;
    float           currentMA;
    float           powerMW;
    bool            proximityTriggered;

    // RTC
    bool            rtcOK;
    uint32_t        currentEpoch;

    // Network status
    ConnStatus      loraStatus;
    ConnStatus      wifiStatus;
    ConnStatus      gsmStatus;
    bool            sdCardOK;

    // Hardware Diagnostics
    HardwareDiagnostics diag;

    // Uptime
    unsigned long   bootTimeMs;
};

// Telemetry event entry (for queue)
struct TelemetryEvent {
    TelemetryMsgType type;
    uint32_t         timestamp;         // Epoch seconds
    uint16_t         voltage_mV;
    uint16_t         current_mA;
    uint16_t         feedDispensed_g;
    uint8_t          currentEvent;
    uint8_t          totalEvents;
    uint8_t          statusFlags;
    // Bit 0: Proximity triggered
    // Bit 1: Overcurrent fault
    // Bit 2: RTC fault
    // Bit 3: SD card fault
    // Bit 4: LoRa connected
    // Bit 5: WiFi connected
    // Bit 6: GSM connected
    bool             sent;              // Has been successfully sent
    uint8_t          retries;           // Transmission retry count
};

// LoRa binary uplink packet (16 bytes, packed for LoRaWAN airtime efficiency)
struct __attribute__((packed)) LoRaUplinkPayload {
    uint8_t  msgType;
    uint32_t timestamp;
    uint16_t voltage_mV;
    uint16_t current_mA;
    uint16_t feedDispensed_g;
    uint8_t  currentEvent;
    uint8_t  totalEvents;
    uint8_t  statusFlags;
    uint8_t  reserved;
};

// Button state (for debounce logic)
struct ButtonState {
    uint8_t  pin;
    bool     rawState;
    bool     lastState;
    bool     stableState;
    bool     risingEdge;    // Just pressed
    bool     fallingEdge;   // Just released
    unsigned long lastDebounceTime;
};

#endif // CONFIG_H
