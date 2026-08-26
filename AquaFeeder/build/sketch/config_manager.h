#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\config_manager.h"
#pragma once

#include "config.h"

class ConfigManager {
public:
    void begin();
    void loadConfig(DeviceConfig& cfg);
    void saveConfig(const DeviceConfig& cfg);
    void saveFeedParams(const DeviceConfig& cfg);
    void saveNetworkConfig(const DeviceConfig& cfg);
    void resetToDefaults(DeviceConfig& cfg);
    bool isFirstBoot();
    void markInitialized();
};

extern ConfigManager configManager;
