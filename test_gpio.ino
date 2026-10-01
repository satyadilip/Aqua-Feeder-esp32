
#include <Arduino.h>
#include <driver/gpio.h>
void setup() {
    gpio_reset_pin(GPIO_NUM_41);
    pinMode(41, OUTPUT);
    digitalWrite(41, HIGH);
}
void loop() {}
