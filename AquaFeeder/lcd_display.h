#pragma once

#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include "config.h"

class LCDDisplay {
public:
    LCDDisplay();
    
    // Initialize the LCD, show splash screen, return true on success
    bool begin();
    
    // Check if the LCD was successfully initialized
    bool isOK();
    
    // Main render function to update the display based on state
    void update(const SystemStatus& status, const DeviceConfig& cfg, MenuState menuState, int menuCursor, int editValue, int editField);
    
    // Display boot splash
    void showSplash();
    
    // Display a 2-line error message
    void showError(const char* line1, const char* line2);
    
    // Display a temporary 2-line message for durationMs
    void showMessage(const char* line1, const char* line2, int durationMs);
    
    // Control backlight
    void setBacklight(bool on);

private:
    LiquidCrystal_I2C* lcd;
    bool lcdOK;
    MenuState prevMenuState;
    unsigned long lastUpdateMs;
    unsigned long msgClearMs;
    bool showingMsg;

    void drawProgressBar(int row, float percent);
    void drawMainStatus(const SystemStatus& status);
    void drawMenuList(int menuCursor);
    void drawEditQty(int editValue);
    void drawEditFPE(int editValue);
    void drawEditTime(int editValue);
    void drawEditStartTime(int editValue, int editField);
    void drawEditRate(int editValue);
    void drawEditClock(const SystemStatus& status, int editValue, int editField);
    void drawRunning(const SystemStatus& status);
    void drawPaused(const SystemStatus& status);
    void drawFinished(const SystemStatus& status);
    void drawNetworkInfo(const SystemStatus& status);
    void drawPowerInfo(const SystemStatus& status);
    
    const char* getConnStatusStr(ConnStatus s);
};
