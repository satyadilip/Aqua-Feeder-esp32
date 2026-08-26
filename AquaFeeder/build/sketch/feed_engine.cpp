#line 1 "C:\\Users\\nsaty\\Documents\\Dilip Work\\Aqua_feeder\\AquaFeeder\\feed_engine.cpp"
#include "feed_engine.h"

void FeedEngine::begin(SystemStatus* status, DeviceConfig* cfg) {
    _status = status;
    _cfg = cfg;
    _fcState = FeedCycleState::FC_IDLE;
    _prePauseFCState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    _fcTimer = 0;
    _lastCurrentCheckMs = 0;
    
    _setRelay = nullptr;
    _motorsOff = nullptr;
    _sendEvent = nullptr;
    _readCurrent = nullptr;
}

bool FeedEngine::calcSchedule() {
    if (!_status || !_cfg) return false;
    
    _status->scheduleValid = false;
    memset(_status->schedError, 0, sizeof(_status->schedError));
    
    if (_cfg->startHour < OP_START_HOUR || _cfg->startHour >= OP_END_HOUR) {
        strncpy(_status->schedError, "Invalid Start", sizeof(_status->schedError)-1);
        return false;
    }
    
    if (_cfg->feedQuantity <= 0 || _cfg->feedPerEvent <= 0 || _cfg->dischargeRate <= 0 || _cfg->feedTime <= 0) {
        strncpy(_status->schedError, "Invalid Params", sizeof(_status->schedError)-1);
        return false;
    }

    float qty_g = _cfg->feedQuantity * 1000.0f;
    _status->totalEvents = qty_g / _cfg->feedPerEvent;
    
    if (_status->totalEvents <= 0) {
        strncpy(_status->schedError, "Zero Events", sizeof(_status->schedError)-1);
        return false;
    }
    
    unsigned long motorTime_ms = (float(_cfg->feedPerEvent) / _cfg->dischargeRate) * 1000UL;
    if (motorTime_ms < MOTOR_MIN_RUN_MS) motorTime_ms = MOTOR_MIN_RUN_MS;
    _status->motorTimeMs = motorTime_ms;
    
    unsigned long totalMotor_ms = _status->totalEvents * motorTime_ms;
    unsigned long feedTime_ms = _cfg->feedTime * 3600UL * 1000UL;
    
    if (totalMotor_ms >= feedTime_ms) {
        strncpy(_status->schedError, "Time Too Short", sizeof(_status->schedError)-1);
        return false;
    }
    
    _status->intervalMs = (feedTime_ms - totalMotor_ms) / _status->totalEvents;
    
    // Calculate nextFeedEpoch - just an example implementation logic, 
    // real implementation depends on current epoch and start hour
    if (_status->rtcOK) {
        // We set nextFeedEpoch to today's start hour or tomorrow's if already passed
        // For simplicity we assume it's calculated correctly here based on rtc logic.
    }
    
    _status->scheduleValid = true;
    return true;
}

void FeedEngine::startFeed() {
    if (!_status) return;
    _status->feedActive = true;
    _status->currentEvent = 0;
    _status->feedState = FeedCycleState::FC_IDLE;
    _fcState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_STARTED);
}

void FeedEngine::stopFeed() {
    if (_motorsOff) _motorsOff();
    if (_status) {
        _status->feedActive = false;
        _status->feedState = FeedCycleState::FC_IDLE;
    }
    _fcState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
}

void FeedEngine::pauseFeed() {
    if (_fcState != FeedCycleState::FC_IDLE && _status && _status->feedActive) {
        _prePauseFCState = _fcState;
        if (_motorsOff) _motorsOff();
        _status->state = SystemState::FEED_PAUSED;
        _fcState = FeedCycleState::FC_IDLE; // wait in idle while paused
        if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_PAUSED);
    }
}

void FeedEngine::resumeFeed() {
    if (_status && _status->state == SystemState::FEED_PAUSED) {
        if (!_status->proximityTriggered) {
            _fcState = _prePauseFCState;
            _fcEntered = false; // re-enter the state to restart timers/relays
            if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_RESUMED);
        }
    }
}

void FeedEngine::update(unsigned long nowMs, uint32_t nowEpoch) {
    if (!_status || !_status->feedActive) return;
    if (_status->state == SystemState::FEED_PAUSED) return;
    
    _status->feedState = _fcState;
    
    switch (_fcState) {
        case FeedCycleState::FC_IDLE:
            if (!_fcEntered) {
                _fcEntered = true;
                _fcState = FeedCycleState::FC_PRE;
                _fcEntered = false;
            }
            break;
            
        case FeedCycleState::FC_PRE:
            if (!_fcEntered) {
                if (_setRelay) _setRelay(2, true); // Dispenser ON
                _fcTimer = nowMs;
                _fcEntered = true;
                _status->state = SystemState::FEED_PRE_WARMUP;
            }
            if (nowMs - _fcTimer >= MOTOR_PRE_RUN_MS) {
                _fcState = FeedCycleState::FC_DISP;
                _fcEntered = false;
            }
            break;
            
        case FeedCycleState::FC_DISP:
            if (!_fcEntered) {
                if (_setRelay) _setRelay(1, true); // Loader ON
                _fcTimer = nowMs;
                _lastCurrentCheckMs = nowMs;
                _fcEntered = true;
                _status->state = SystemState::FEED_DISPENSING;
            }
            if (nowMs - _lastCurrentCheckMs >= INA219_SAMPLE_MS) {
                _lastCurrentCheckMs = nowMs;
                if (_readCurrent) {
                    float current = _readCurrent();
                    if (current > (_cfg ? _cfg->overcurrentLimit : OVERCURRENT_LIMIT_MA)) {
                        pauseFeed();
                        if (_sendEvent) _sendEvent(TelemetryMsgType::ALARM_OVERCURRENT);
                        return;
                    }
                }
            }
            if (nowMs - _fcTimer >= _status->motorTimeMs) {
                _fcState = FeedCycleState::FC_POST;
                _fcEntered = false;
            }
            break;
            
        case FeedCycleState::FC_POST:
            if (!_fcEntered) {
                if (_setRelay) _setRelay(1, false); // Loader OFF
                _fcTimer = nowMs;
                _fcEntered = true;
                _status->state = SystemState::FEED_POST_CLEAR;
            }
            if (nowMs - _fcTimer >= MOTOR_POST_RUN_MS) {
                if (_motorsOff) _motorsOff();
                _status->currentEvent++;
                
                if (_status->currentEvent >= _status->totalEvents) {
                    _status->state = SystemState::FEED_FINISHED;
                    _status->feedActive = false;
                    _fcState = FeedCycleState::FC_IDLE;
                    if (_sendEvent) _sendEvent(TelemetryMsgType::SESSION_COMPLETE);
                } else {
                    _status->nextFeedEpoch = nowEpoch + (_status->intervalMs / 1000);
                    _fcState = FeedCycleState::FC_WAIT;
                    _fcEntered = false;
                }
            }
            break;
            
        case FeedCycleState::FC_WAIT:
            if (!_fcEntered) {
                _status->state = SystemState::FEED_WAIT_NEXT;
                _fcEntered = true;
            }
            if (nowEpoch >= _status->nextFeedEpoch) {
                _fcState = FeedCycleState::FC_IDLE;
                _fcEntered = false;
            }
            break;
    }
}

bool FeedEngine::shouldAutoStart(uint32_t nowEpoch) {
    if (!_status || !_cfg) return false;
    if (!_status->rtcOK || _status->feedActive || !_status->scheduleValid) return false;
    
    // Check if within OP window
    // (Needs proper RTC hour checking, for now assuming nextFeedEpoch is accurate)
    if (nowEpoch >= _status->nextFeedEpoch && _status->currentEvent == 0) {
        return true;
    }
    return false;
}

bool FeedEngine::isActive() const {
    return _status && _status->feedActive;
}

bool FeedEngine::isPaused() const {
    return _status && _status->state == SystemState::FEED_PAUSED;
}

void FeedEngine::setRelayCallback(void (*setRelay)(int relay, bool on)) { _setRelay = setRelay; }
void FeedEngine::setMotorsOffCallback(void (*motorsOff)()) { _motorsOff = motorsOff; }
void FeedEngine::setTelemetryCallback(void (*sendEvent)(TelemetryMsgType type)) { _sendEvent = sendEvent; }
void FeedEngine::setCurrentReadCallback(float (*readCurrent)()) { _readCurrent = readCurrent; }
