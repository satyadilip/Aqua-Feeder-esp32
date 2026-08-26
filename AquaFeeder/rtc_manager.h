#pragma once
#include <Arduino.h>
#include <RTClib.h>
#include "config.h"

class RTCManager {
public:
    bool begin();
    bool isOK();
    uint32_t getEpoch();
    void getTime(int& h, int& m, int& s);
    void getDate(int& y, int& mo, int& d);
    String getTimeStr();
    String getDateTimeStr();
    void setTime(int h, int m, int s);
    void setDateTime(int y, int mo, int d, int h, int m, int s);
    DateTime getNow();
    float getTemperature();

private:
    RTC_DS3231 rtc;
    bool statusOK;
};
