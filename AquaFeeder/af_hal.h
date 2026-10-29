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
    bool readRawProximity() const;
    void setProxAlarmHigh(bool alarmHigh);
    bool getProxAlarmHigh() const { return m_proxAlarmHigh; }
    void updateStatusLed(SystemState state, bool hasError);
    void updateErrorLed(ErrorCode err);
    void triggerMinorWarning(MinorWarning warning);

private:
    ButtonState m_btnUp;
    ButtonState m_btnDown;
    ButtonState m_btnSelect;
    ButtonState m_btnConfig;
    bool m_proxAlarmHigh = true;

    void initButton(ButtonState& btn, uint8_t pin);
    void processButton(ButtonState& btn);
};

extern HardwareLayer hal;
