#pragma once

#include "config.h"

class FeedEngine {
public:
    void begin(SystemStatus* status, DeviceConfig* cfg);
    bool calcSchedule(uint32_t nowEpoch = 0);
    void startFeed(uint32_t nowEpoch = 0);
    void stopFeed();
    void pauseFeed();
    void resumeFeed(uint32_t nowEpoch = 0);
    void update(unsigned long nowMs, uint32_t nowEpoch);
    bool recalcDynamic(uint32_t nowEpoch = 0);
    bool shouldAutoStart(uint32_t nowEpoch);
    void resumeFromPowerFailure(uint32_t nowEpoch);

    bool isActive() const;
    bool isPaused() const;
    uint32_t getLastFedDay() const { return _lastFedDay; }

    void setRelayCallback(void (*setRelay)(int relay, bool on));
    void setMotorsOffCallback(void (*motorsOff)());
    void setTelemetryCallback(void (*sendEvent)(TelemetryMsgType type));
    void setCurrentReadCallback(float (*readCurrent)());
    void setSaveStateCallback(void (*saveState)());

private:
    SystemStatus* _status;
    DeviceConfig* _cfg;
    FeedCycleState _fcState;
    FeedCycleState _prePauseFCState;
    bool _fcEntered;
    bool _isPaused;
    unsigned long _fcTimer;
    unsigned long _lastCurrentCheckMs;
    unsigned long _pauseStartMs;
    uint32_t _lastFedDay;

    void (*_setRelay)(int relay, bool on);
    void (*_motorsOff)();
    void (*_sendEvent)(TelemetryMsgType type);
    float (*_readCurrent)();
    void (*_saveState)();
};
