#pragma once
#include <Arduino.h>
#include <Adafruit_INA219.h>
#include "config.h"

class PowerMonitor {
public:
    bool begin();
    bool isOK();
    void update();
    float getVoltage();
    float getCurrent();
    float getPower();
    bool isOvercurrent(uint16_t limitMA);
    uint16_t getVoltage_mV();
    uint16_t getCurrent_mA();

private:
    Adafruit_INA219 ina219;
    bool statusOK;
    float voltage_V;
    float current_mA;
    float power_mW;
};
