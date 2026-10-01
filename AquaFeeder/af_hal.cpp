#include "af_hal.h"
#include <driver/gpio.h>
// Global instance defined in AquaFeeder.ino via af_hal.h extern declaration

void HardwareLayer::begin() {
    // Relays (Active LOW)
    gpio_reset_pin(GPIO_NUM_41);
    pinMode(PIN_RELAY_LOADER, OUTPUT);
    digitalWrite(PIN_RELAY_LOADER, HIGH);
    
    gpio_reset_pin(GPIO_NUM_39);
    pinMode(PIN_RELAY_DISPENSER, OUTPUT);
    digitalWrite(PIN_RELAY_DISPENSER, HIGH);
    
    // LEDs & Hooter
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_LED_RED, LOW); // Assuming LEDs are active HIGH based on normal design, if not we will invert later
    
    pinMode(PIN_LED_GREEN, OUTPUT);
    digitalWrite(PIN_LED_GREEN, LOW);
    pinMode(PIN_HOOTER, OUTPUT);
    digitalWrite(PIN_HOOTER, HIGH); // Hooter is Active LOW

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
    // GPIO 48 is PIN_SPI_MISO — do not execute neopixelWrite on GPIO 48!
    (void)r; (void)g; (void)b;
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
    digitalWrite(pin, on ? LOW : HIGH); // Active LOW
    delay(100); // 100ms delay for relay settle
    Serial.printf("[HAL] Relay %d set to %s\n", relay, on ? "ON" : "OFF");
}

void HardwareLayer::motorsOff() {
    digitalWrite(PIN_RELAY_LOADER, HIGH); // Active LOW
    digitalWrite(PIN_RELAY_DISPENSER, HIGH);
    delay(100);
    
    bool r1 = digitalRead(PIN_RELAY_LOADER);
    bool r2 = digitalRead(PIN_RELAY_DISPENSER);
    
    if (r1 != HIGH || r2 != HIGH) {
        Serial.println("[HAL] Mismatch reading relay state. Retrying...");
        digitalWrite(PIN_RELAY_LOADER, HIGH);
        digitalWrite(PIN_RELAY_DISPENSER, HIGH);
        delay(100);
        r1 = digitalRead(PIN_RELAY_LOADER);
        r2 = digitalRead(PIN_RELAY_DISPENSER);
    }
    
    Serial.printf("[HAL] Motors OFF. R1: %d, R2: %d\n", r1, r2);
}

void HardwareLayer::setHooter(bool on) {
    digitalWrite(PIN_HOOTER, on ? LOW : HIGH); // Active LOW
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

void HardwareLayer::updateStatusLed(SystemState state, bool hasError) {
    if (hasError || state == SystemState::ERROR_FATAL) {
        setLedGreen(false);
        return;
    }

    static unsigned long lastUpdate = 0;
    static int blinkPhase = 0;
    unsigned long now = millis();

    // Determine intervals based on state
    int timeOn = 0;
    int timeOff = 0;
    bool isDoubleBlip = false;

    switch (state) {
        case SystemState::INIT:
        case SystemState::AP_CONFIG:
            timeOn = 100; timeOff = 100;
            break;
            
        case SystemState::IDLE:
        case SystemState::FEED_PAUSED:
            timeOn = 500; timeOff = 500;
            break;
            
        case SystemState::FEED_PRE_WARMUP:
        case SystemState::FEED_DISPENSING:
        case SystemState::FEED_POST_CLEAR:
            setLedGreen(true);
            return; // Solid ON
            
        case SystemState::FEED_WAIT_NEXT:
            timeOn = 1500; timeOff = 1500;
            break;
            
        case SystemState::FEED_FINISHED:
            isDoubleBlip = true;
            break;
            
        default:
            timeOn = 500; timeOff = 500;
            break;
    }

    if (isDoubleBlip) {
        // Phase 0: ON (100ms), Phase 1: OFF (100ms), Phase 2: ON (100ms), Phase 3: OFF (2000ms)
        unsigned long phaseTimes[] = {100, 100, 100, 2000};
        if (now - lastUpdate >= phaseTimes[blinkPhase % 4]) {
            lastUpdate = now;
            blinkPhase++;
        }
        setLedGreen((blinkPhase % 4) == 0 || (blinkPhase % 4) == 2);
    } else {
        // Standard blinking
        // Phase 0: ON, Phase 1: OFF
        unsigned long currentInterval = (blinkPhase % 2 == 0) ? timeOn : timeOff;
        if (now - lastUpdate >= currentInterval) {
            lastUpdate = now;
            blinkPhase++;
        }
        setLedGreen(blinkPhase % 2 == 0);
    }
}

void HardwareLayer::updateErrorLed(ErrorCode err) {
    if (err == ErrorCode::NONE) {
        setLedRed(false);
        return;
    }

    if (err == ErrorCode::SCHED_FAULT) {
        setLedRed(true);
        return;
    }

    static ErrorCode lastErr = ErrorCode::NONE;
    static unsigned long lastUpdate = 0;
    static int phase = 0;
    unsigned long now = millis();

    if (err != lastErr) {
        lastErr = err;
        phase = 0;
        lastUpdate = now;
    }

    int blinks = static_cast<int>(err);
    int totalPhases = blinks * 2;

    if (phase >= totalPhases) {
        // Gap time (1000ms)
        if (now - lastUpdate >= 1000) {
            lastUpdate = now;
            phase = 0;
        }
        setLedRed(false);
    } else {
        // Fast blink (150ms ON / 150ms OFF)
        if (now - lastUpdate >= 150) {
            lastUpdate = now;
            phase++;
        }
        setLedRed(phase % 2 == 0 && phase < totalPhases);
    }
}
