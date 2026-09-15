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
    
    // Dynamic Run State Persistence
    void saveRunState(const SystemStatus& status);
    void loadRunState(SystemStatus& status);
    void clearRunState();
};

extern ConfigManager configManager;
