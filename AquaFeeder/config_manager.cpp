#include "config_manager.h"
#include <Preferences.h>
#include <esp_mac.h>

ConfigManager configManager;
static Preferences prefs;

void ConfigManager::begin() {
    // Preferences initialized as needed to keep scope clean
}

void ConfigManager::loadConfig(DeviceConfig& cfg) {
    prefs.begin(NVS_NAMESPACE, true); // read-only
    
    cfg.feedQuantity = prefs.getFloat("qty", FEED_QTY_DEFAULT);
    cfg.feedPerEvent = prefs.getInt("fpe", FEED_FPE_DEFAULT);
    cfg.startHour = prefs.getInt("shour", FEED_START_HOUR_DEFAULT);
    cfg.startMinute = prefs.getInt("smin", FEED_START_MIN_DEFAULT);
    cfg.endHour = prefs.getInt("ehour", FEED_END_HOUR_DEFAULT);
    cfg.endMinute = prefs.getInt("emin", FEED_END_MIN_DEFAULT);
    cfg.dischargeRate = prefs.getInt("drate", FEED_RATE_DEFAULT);
    
    cfg.telemetryIntervalS = prefs.getUInt("txIntv", TELEMETRY_INTERVAL_DEFAULT_S);
    cfg.uplinkMode = (UplinkMode)prefs.getUChar("uplnk", (uint8_t)UplinkMode::AUTO_FAILOVER);
    
    const uint8_t defaultAppEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05 };
    const uint8_t defaultAppKey[16] = { 
        0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6, 
        0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C 
    };

    // Auto-generate DevEUI from ESP32 default MAC address (EUI-64 format)
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    cfg.loraDevEUI[0] = mac[0];
    cfg.loraDevEUI[1] = mac[1];
    cfg.loraDevEUI[2] = mac[2];
    cfg.loraDevEUI[3] = 0xFF;
    cfg.loraDevEUI[4] = 0xFE;
    cfg.loraDevEUI[5] = mac[3];
    cfg.loraDevEUI[6] = mac[4];
    cfg.loraDevEUI[7] = mac[5];
    
    if (prefs.getBytesLength("appEUI") == 8) prefs.getBytes("appEUI", cfg.loraAppEUI, 8);
    else memcpy(cfg.loraAppEUI, defaultAppEUI, 8);
    
    if (prefs.getBytesLength("appKey") == 16) prefs.getBytes("appKey", cfg.loraAppKey, 16);
    else memcpy(cfg.loraAppKey, defaultAppKey, 16);

    cfg.loraOTAA = prefs.getBool("loraOTAA", true);
    
    prefs.getString("wSSID", WIFI_AP_SSID_DEFAULT).toCharArray(cfg.wifiSSID, sizeof(cfg.wifiSSID));
    prefs.getString("wPass", WIFI_AP_PASS_DEFAULT).toCharArray(cfg.wifiPass, sizeof(cfg.wifiPass));
    prefs.getString("mqSrv", "").toCharArray(cfg.mqttServer, sizeof(cfg.mqttServer));
    cfg.mqttPort = prefs.getUShort("mqPort", 1883);
    prefs.getString("mqClId", "AquaFeeder").toCharArray(cfg.mqttClientId, sizeof(cfg.mqttClientId));
    
    prefs.getString("gAPN", APN_AIRTEL).toCharArray(cfg.gsmAPN, sizeof(cfg.gsmAPN));
    prefs.getString("gUser", "").toCharArray(cfg.gsmUser, sizeof(cfg.gsmUser));
    prefs.getString("gPass", "").toCharArray(cfg.gsmPass, sizeof(cfg.gsmPass));
    prefs.getString("gMqSrv", "").toCharArray(cfg.gsmMqttServer, sizeof(cfg.gsmMqttServer));
    cfg.gsmMqttPort = prefs.getUShort("gMqPrt", 1883);
    
    prefs.getString("apSSID", WIFI_AP_SSID_DEFAULT).toCharArray(cfg.apSSID, sizeof(cfg.apSSID));
    prefs.getString("apPass", WIFI_AP_PASS_DEFAULT).toCharArray(cfg.apPass, sizeof(cfg.apPass));
    
    prefs.getString("devId", "AQUA_001").toCharArray(cfg.deviceId, sizeof(cfg.deviceId));
    
    cfg.overcurrentLimit = prefs.getUShort("ocLimit", OVERCURRENT_LIMIT_MA);
    cfg.hasBeenRun = prefs.getBool("hasRun", false);
    
    prefs.end();
    
    Serial.println("[CONFIG] Configuration loaded from NVS");
    Serial.printf("[CONFIG] Qty: %.1f kg, FPE: %d g, Time: %02d:%02d to %02d:%02d\n", cfg.feedQuantity, cfg.feedPerEvent, cfg.startHour, cfg.startMinute, cfg.endHour, cfg.endMinute);
}

void ConfigManager::saveConfig(const DeviceConfig& cfg) {
    saveFeedParams(cfg);
    saveNetworkConfig(cfg);
    
    prefs.begin(NVS_NAMESPACE, false);
    prefs.putUInt("txIntv", cfg.telemetryIntervalS);
    prefs.putUChar("uplnk", (uint8_t)cfg.uplinkMode);
    
    prefs.putBytes("devEUI", cfg.loraDevEUI, 8);
    prefs.putBytes("appEUI", cfg.loraAppEUI, 8);
    prefs.putBytes("appKey", cfg.loraAppKey, 16);
    prefs.putBool("loraOTAA", cfg.loraOTAA);
    
    prefs.putString("devId", cfg.deviceId);
    prefs.putUShort("ocLimit", cfg.overcurrentLimit);
    prefs.putBool("hasRun", cfg.hasBeenRun);
    prefs.end();
    
    Serial.println("[CONFIG] Full configuration saved to NVS");
}

void ConfigManager::saveFeedParams(const DeviceConfig& cfg) {
    prefs.begin(NVS_NAMESPACE, false);
    prefs.putFloat("qty", cfg.feedQuantity);
    prefs.putInt("fpe", cfg.feedPerEvent);
    prefs.putInt("shour", cfg.startHour);
    prefs.putInt("smin", cfg.startMinute);
    prefs.putInt("ehour", cfg.endHour);
    prefs.putInt("emin", cfg.endMinute);
    prefs.putInt("drate", cfg.dischargeRate);
    prefs.end();
    Serial.println("[CONFIG] Feed parameters saved to NVS");
}

void ConfigManager::saveNetworkConfig(const DeviceConfig& cfg) {
    prefs.begin(NVS_NAMESPACE, false);
    prefs.putString("wSSID", cfg.wifiSSID);
    prefs.putString("wPass", cfg.wifiPass);
    prefs.putString("mqSrv", cfg.mqttServer);
    prefs.putUShort("mqPort", cfg.mqttPort);
    prefs.putString("mqClId", cfg.mqttClientId);
    
    prefs.putString("gAPN", cfg.gsmAPN);
    prefs.putString("gUser", cfg.gsmUser);
    prefs.putString("gPass", cfg.gsmPass);
    prefs.putString("gMqSrv", cfg.gsmMqttServer);
    prefs.putUShort("gMqPrt", cfg.gsmMqttPort);
    
    prefs.putString("apSSID", cfg.apSSID);
    prefs.putString("apPass", cfg.apPass);
    prefs.end();
    Serial.println("[CONFIG] Network config saved to NVS");
}

void ConfigManager::resetToDefaults(DeviceConfig& cfg) {
    cfg.feedQuantity = FEED_QTY_DEFAULT;
    cfg.feedPerEvent = FEED_FPE_DEFAULT;
    cfg.startHour = FEED_START_HOUR_DEFAULT;
    cfg.startMinute = FEED_START_MIN_DEFAULT;
    cfg.endHour = FEED_END_HOUR_DEFAULT;
    cfg.endMinute = FEED_END_MIN_DEFAULT;
    cfg.dischargeRate = FEED_RATE_DEFAULT;
    
    cfg.telemetryIntervalS = TELEMETRY_INTERVAL_DEFAULT_S;
    cfg.uplinkMode = UplinkMode::AUTO_FAILOVER;
    
    const uint8_t defaultDevEUI[8] = { 0xE0, 0x72, 0xA1, 0xF6, 0x24, 0x9C, 0x00, 0x05 };
    const uint8_t defaultAppEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05 };
    const uint8_t defaultAppKey[16] = { 
        0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6, 
        0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C 
    };
    memcpy(cfg.loraDevEUI, defaultDevEUI, 8);
    memcpy(cfg.loraAppEUI, defaultAppEUI, 8);
    memcpy(cfg.loraAppKey, defaultAppKey, 16);
    cfg.loraOTAA = true;
    
    strncpy(cfg.wifiSSID, WIFI_AP_SSID_DEFAULT, sizeof(cfg.wifiSSID));
    strncpy(cfg.wifiPass, WIFI_AP_PASS_DEFAULT, sizeof(cfg.wifiPass));
    strncpy(cfg.mqttServer, "", sizeof(cfg.mqttServer));
    cfg.mqttPort = 1883;
    strncpy(cfg.mqttClientId, "AquaFeeder", sizeof(cfg.mqttClientId));
    
    strncpy(cfg.gsmAPN, APN_AIRTEL, sizeof(cfg.gsmAPN));
    strncpy(cfg.gsmUser, "", sizeof(cfg.gsmUser));
    strncpy(cfg.gsmPass, "", sizeof(cfg.gsmPass));
    strncpy(cfg.gsmMqttServer, "", sizeof(cfg.gsmMqttServer));
    cfg.gsmMqttPort = 1883;
    
    strncpy(cfg.apSSID, WIFI_AP_SSID_DEFAULT, sizeof(cfg.apSSID));
    strncpy(cfg.apPass, WIFI_AP_PASS_DEFAULT, sizeof(cfg.apPass));
    
    strncpy(cfg.deviceId, "AQUA_001", sizeof(cfg.deviceId));
    cfg.overcurrentLimit = OVERCURRENT_LIMIT_MA;
    cfg.hasBeenRun = false;
    
    saveConfig(cfg);
    Serial.println("[CONFIG] Reset to defaults");
}

bool ConfigManager::isFirstBoot() {
    prefs.begin(NVS_NAMESPACE, true);
    bool inited = prefs.getBool("inited", false);
    prefs.end();
    return !inited;
}

void ConfigManager::markInitialized() {
    prefs.begin(NVS_NAMESPACE, false);
    prefs.putBool("inited", true);
    prefs.end();
    Serial.println("[CONFIG] NVS marked as initialized");
}

void ConfigManager::saveRunState(const SystemStatus& status) {
    prefs.begin("runstate", false);
    prefs.putBool("active", status.feedActive);
    prefs.putInt("curEvt", status.currentEvent);
    prefs.putFloat("dispQty", status.dispensedQuantity_g);
    prefs.putUInt("nxtEpoc", status.nextFeedEpoch);
    prefs.end();
}

void ConfigManager::loadRunState(SystemStatus& status) {
    prefs.begin("runstate", true);
    status.feedActive = prefs.getBool("active", false);
    status.currentEvent = prefs.getInt("curEvt", 0);
    status.dispensedQuantity_g = prefs.getFloat("dispQty", 0.0f);
    status.nextFeedEpoch = prefs.getUInt("nxtEpoc", 0);
    prefs.end();
}

void ConfigManager::clearRunState() {
    prefs.begin("runstate", false);
    prefs.putBool("active", false);
    prefs.end();
}
