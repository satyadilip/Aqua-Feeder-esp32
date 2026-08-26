#include "power_monitor.h"

bool PowerMonitor::begin() {
    statusOK = ina219.begin();
    if (!statusOK) {
        Serial.println("[POWER] Failed to find INA219");
        return false;
    }
    Serial.println("[POWER] Initialized successfully");
    return true;
}

bool PowerMonitor::isOK() {
    return statusOK;
}

void PowerMonitor::update() {
    if (!statusOK) return;
    voltage_V = ina219.getBusVoltage_V();
    current_mA = ina219.getCurrent_mA();
    power_mW = ina219.getPower_mW();
}

float PowerMonitor::getVoltage() {
    return voltage_V;
}

float PowerMonitor::getCurrent() {
    return current_mA;
}

float PowerMonitor::getPower() {
    return power_mW;
}

bool PowerMonitor::isOvercurrent(uint16_t limitMA) {
    return (current_mA > limitMA);
}

uint16_t PowerMonitor::getVoltage_mV() {
    return (uint16_t)(voltage_V * 1000.0f);
}

uint16_t PowerMonitor::getCurrent_mA() {
    if (current_mA < 0) return 0;
    return (uint16_t)current_mA;
}
