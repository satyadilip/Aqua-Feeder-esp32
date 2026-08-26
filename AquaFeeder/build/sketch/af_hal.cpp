#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\af_hal.cpp"
#include "af_hal.h"

// Global instance defined in AquaFeeder.ino via af_hal.h extern declaration

void HardwareLayer::begin() {
    // Relays
    pinMode(PIN_RELAY_LOADER, OUTPUT);
    digitalWrite(PIN_RELAY_LOADER, LOW);
    pinMode(PIN_RELAY_DISPENSER, OUTPUT);
    digitalWrite(PIN_RELAY_DISPENSER, LOW);
    
    // LEDs & Hooter
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_LED_RED, LOW);
    pinMode(PIN_LED_GREEN, OUTPUT);
    digitalWrite(PIN_LED_GREEN, LOW);
    pinMode(PIN_HOOTER, OUTPUT);
    digitalWrite(PIN_HOOTER, LOW);

    // Proximity
    pinMode(PIN_PROXIMITY, INPUT_PULLUP);

    // Buttons
    initButton(m_btnUp, PIN_BTN_UP);
    initButton(m_btnDown, PIN_BTN_DOWN);
    initButton(m_btnSelect, PIN_BTN_SELECT);
    initButton(m_btnConfig, PIN_BTN_CONFIG);
    
    Serial.println("[HAL] Initialized GPIOs.");
}

void HardwareLayer::setRgbLed(uint8_t r, uint8_t g, uint8_t b) {
#ifdef RGB_BUILTIN
    neopixelWrite(RGB_BUILTIN, r, g, b);
#else
    neopixelWrite(48, r, g, b);
#endif
}

void HardwareLayer::initButton(ButtonState& btn, uint8_t pin) {
    btn.pin = pin;
    pinMode(pin, INPUT_PULLUP);
    btn.rawState = HIGH;
    btn.lastState = HIGH;
    btn.stableState = HIGH;
    btn.risingEdge = false;
    btn.fallingEdge = false;
    btn.lastDebounceTime = 0;
}

void HardwareLayer::setRelay(int relay, bool on) {
    uint8_t pin = (relay == 1) ? PIN_RELAY_LOADER : PIN_RELAY_DISPENSER;
    digitalWrite(pin, on ? HIGH : LOW);
    delay(100); // 100ms delay for relay settle
    Serial.printf("[HAL] Relay %d set to %s\n", relay, on ? "ON" : "OFF");
}

void HardwareLayer::motorsOff() {
    digitalWrite(PIN_RELAY_LOADER, LOW);
    digitalWrite(PIN_RELAY_DISPENSER, LOW);
    delay(100);
    
    bool r1 = digitalRead(PIN_RELAY_LOADER);
    bool r2 = digitalRead(PIN_RELAY_DISPENSER);
    
    if (r1 != LOW || r2 != LOW) {
        Serial.println("[HAL] Mismatch reading relay state. Retrying...");
        digitalWrite(PIN_RELAY_LOADER, LOW);
        digitalWrite(PIN_RELAY_DISPENSER, LOW);
        delay(100);
        r1 = digitalRead(PIN_RELAY_LOADER);
        r2 = digitalRead(PIN_RELAY_DISPENSER);
    }
    
    Serial.printf("[HAL] Motors OFF. R1: %d, R2: %d\n", r1, r2);
}

void HardwareLayer::setHooter(bool on) {
    digitalWrite(PIN_HOOTER, on ? HIGH : LOW);
}

void HardwareLayer::setLedRed(bool on) {
    digitalWrite(PIN_LED_RED, on ? HIGH : LOW);
}

void HardwareLayer::setLedGreen(bool on) {
    digitalWrite(PIN_LED_GREEN, on ? HIGH : LOW);
}

void HardwareLayer::blinkGreen(int count, int ms) {
    for (int i = 0; i < count; i++) {
        setLedGreen(true);
        delay(ms);
        setLedGreen(false);
        delay(ms);
    }
}

void HardwareLayer::processButton(ButtonState& btn) {
    bool reading = digitalRead(btn.pin);
    btn.risingEdge = false;
    btn.fallingEdge = false;
    
    if (reading != btn.lastState) {
        btn.lastDebounceTime = millis();
    }
    
    if ((millis() - btn.lastDebounceTime) > BUTTON_DEBOUNCE_MS) {
        if (reading != btn.stableState) {
            btn.stableState = reading;
            
            // Buttons are Active LOW, so LOW means pressed
            if (btn.stableState == LOW) {
                btn.risingEdge = true; // Pressed
            } else {
                btn.fallingEdge = true; // Released
            }
        }
    }
    
    btn.lastState = reading;
}

void HardwareLayer::updateButtons() {
    processButton(m_btnUp);
    processButton(m_btnDown);
    processButton(m_btnSelect);
    processButton(m_btnConfig);
}

ButtonState& HardwareLayer::btnUp() { return m_btnUp; }
ButtonState& HardwareLayer::btnDown() { return m_btnDown; }
ButtonState& HardwareLayer::btnSelect() { return m_btnSelect; }
ButtonState& HardwareLayer::btnConfig() { return m_btnConfig; }

bool HardwareLayer::isProximityTriggered() {
    return digitalRead(PIN_PROXIMITY) == LOW;
}

void HardwareLayer::heartbeatTick() {
    static unsigned long lastTick = 0;
    static bool ledState = false;
    if (millis() - lastTick >= 1000) {
        lastTick = millis();
        ledState = !ledState;
        setLedGreen(ledState);
    }
}
