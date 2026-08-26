#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\af_hal.h"
#pragma once

#include "config.h"

class HardwareLayer {
public:
    void begin();
    void setRgbLed(uint8_t r, uint8_t g, uint8_t b);
    void setRelay(int relay, bool on);
    void motorsOff();
    void setHooter(bool on);
    void setLedRed(bool on);
    void setLedGreen(bool on);
    void blinkGreen(int count, int ms);
    void updateButtons();
    ButtonState& btnUp();
    ButtonState& btnDown();
    ButtonState& btnSelect();
    ButtonState& btnConfig();
    bool isProximityTriggered();
    void heartbeatTick();

private:
    ButtonState m_btnUp;
    ButtonState m_btnDown;
    ButtonState m_btnSelect;
    ButtonState m_btnConfig;

    void initButton(ButtonState& btn, uint8_t pin);
    void processButton(ButtonState& btn);
};

extern HardwareLayer hal;
