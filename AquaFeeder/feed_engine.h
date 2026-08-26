#pragma once

#include "config.h"

class FeedEngine {
public:
    void begin(SystemStatus* status, DeviceConfig* cfg);
    bool calcSchedule();
    void startFeed();
    void stopFeed();
    void pauseFeed();
    void resumeFeed();
    void update(unsigned long nowMs, uint32_t nowEpoch);
    bool shouldAutoStart(uint32_t nowEpoch);
    bool isActive() const;
    bool isPaused() const;

    void setRelayCallback(void (*setRelay)(int relay, bool on));
    void setMotorsOffCallback(void (*motorsOff)());
    void setTelemetryCallback(void (*sendEvent)(TelemetryMsgType type));
    void setCurrentReadCallback(float (*readCurrent)());

private:
    SystemStatus* _status;
    DeviceConfig* _cfg;
    FeedCycleState _fcState;
    FeedCycleState _prePauseFCState;
    bool _fcEntered;
    unsigned long _fcTimer;
    unsigned long _lastCurrentCheckMs;

    void (*_setRelay)(int relay, bool on);
    void (*_motorsOff)();
    void (*_sendEvent)(TelemetryMsgType type);
    float (*_readCurrent)();
};
