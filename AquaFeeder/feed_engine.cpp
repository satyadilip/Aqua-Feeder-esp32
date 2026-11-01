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
    _saveState = nullptr;
}

bool FeedEngine::calcSchedule(uint32_t nowEpoch) {
    if (!_status || !_cfg) return false;
    
    _status->scheduleValid = false;
    memset(_status->schedError, 0, sizeof(_status->schedError));
    
    // Check 1: 06:00 to 18:00 Operational Window hard limit (cannot exceed 18:00)
    if (_cfg->startHour < OP_START_HOUR || _cfg->endHour > OP_END_HOUR || (_cfg->endHour == OP_END_HOUR && _cfg->endMinute > 0)) {
        strncpy(_status->schedError, "Out of OP Window", sizeof(_status->schedError)-1);
        return false;
    }
    
    int startMins = _cfg->startHour * 60 + _cfg->startMinute;
    int endMins = _cfg->endHour * 60 + _cfg->endMinute;
    if (endMins <= startMins) {
        strncpy(_status->schedError, "End < Start", sizeof(_status->schedError)-1);
        return false;
    }
    
    if (_cfg->feedQuantity <= 0 || _cfg->feedPerEvent <= 0 || _cfg->dischargeRate <= 0) {
        strncpy(_status->schedError, "Invalid Params", sizeof(_status->schedError)-1);
        return false;
    }

    float qty_g = _cfg->feedQuantity * 1000.0f;
    _status->totalEvents = qty_g / _cfg->feedPerEvent;
    
    if (_status->totalEvents <= 0) {
        strncpy(_status->schedError, "Zero Events", sizeof(_status->schedError)-1);
        return false;
    }
    
    float dRate = _cfg->dischargeRate;
    if (dRate <= 0.1f) dRate = 50.0f; // Failsafe
    unsigned long motorTime_ms = (float(_cfg->feedPerEvent) / dRate) * 1000.0f;
    if (motorTime_ms < MOTOR_MIN_RUN_MS) motorTime_ms = MOTOR_MIN_RUN_MS;
    _status->motorTimeMs = motorTime_ms;
    
    // Each event includes Pre-Warmup (3s) + Dispense (motorTime_ms) + Post-Clearance (3s)
    unsigned long singleEvent_ms = MOTOR_PRE_RUN_MS + motorTime_ms + MOTOR_POST_RUN_MS;
    unsigned long totalEventsDuration_ms = _status->totalEvents * singleEvent_ms;
    unsigned long fullWindow_ms = (endMins - startMins) * 60UL * 1000UL;

    // Check 4: Can the requested quantity physically fit within the operational daylight window?
    if (totalEventsDuration_ms >= fullWindow_ms) {
        strncpy(_status->schedError, "Time Too Short", sizeof(_status->schedError)-1);
        Serial.println("[SCHED] Error: Configured feed parameters cannot fit before 6 PM window!");
        return false;
    }

    unsigned long availableTime_ms = fullWindow_ms;

    if (nowEpoch > 0) {
        uint32_t secSinceMidnight = nowEpoch % 86400;
        int currentMins = secSinceMidnight / 60;
        uint32_t midnightEpoch = nowEpoch - secSinceMidnight;
        uint32_t startEpochToday = midnightEpoch + ((uint32_t)startMins * 60UL);
        uint32_t endEpochToday   = midnightEpoch + ((uint32_t)endMins * 60UL);

        if (currentMins >= endMins) {
            strncpy(_status->schedError, "Past 6 PM Window", sizeof(_status->schedError)-1);
            _status->nextFeedEpoch = startEpochToday + 86400UL; // Schedule next run for tomorrow 06:00
            Serial.printf("[SCHED] Current time %02d:%02d is past OP window end %02d:%02d. Feeding blocked until tomorrow.\n",
                          currentMins / 60, currentMins % 60, endMins / 60, endMins % 60);
            return false;
        } else if (currentMins >= startMins) {
            // Mid-day start! Dynamically calculate remaining time until endHour:endMinute (18:00)
            uint32_t endSecToday = (uint32_t)endMins * 60UL;
            if (endSecToday > secSinceMidnight) {
                availableTime_ms = (endSecToday - secSinceMidnight) * 1000UL;
            }
            if (_status->currentEvent == 0) {
                _status->nextFeedEpoch = nowEpoch;
            }
            Serial.printf("[SCHED] Mid-day start at %02d:%02d. Remaining window: %lu s until %02d:%02d\n",
                          currentMins / 60, currentMins % 60, (availableTime_ms / 1000UL), endMins / 60, endMins % 60);
        } else {
            // Early morning before start time (e.g. 05:30 AM before 06:00 AM)
            availableTime_ms = fullWindow_ms;
            _status->nextFeedEpoch = startEpochToday;
        }

        // Check 5: For mid-day start, can it finish in the remaining time today?
        if (totalEventsDuration_ms >= availableTime_ms) {
            strncpy(_status->schedError, "Time Too Short", sizeof(_status->schedError)-1);
            Serial.println("[SCHED] Error: Remaining operational window is shorter than required total cycle time!");
            return false;
        }
    }
    
    _status->intervalMs = (availableTime_ms - totalEventsDuration_ms) / _status->totalEvents;
    Serial.printf("[SCHED] Schedule OK: %d events, motorTime: %lu ms, gap interval: %lu s (%lu ms)\n",
                  _status->totalEvents, _status->motorTimeMs, (_status->intervalMs / 1000UL), _status->intervalMs);
    
    _status->scheduleValid = true;
    return true;
}

void FeedEngine::startFeed() {
    if (!_status) return;
    _status->feedActive = true;
    _status->currentEvent = 0;
    _status->dispensedQuantity_g = 0.0f;
    _status->feedState = FeedCycleState::FC_IDLE;
    _fcState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_STARTED);
    if (_saveState) _saveState();
}

void FeedEngine::stopFeed() {
    if (_motorsOff) _motorsOff();
    if (_status) {
        _status->feedActive = false;
        _status->feedState = FeedCycleState::FC_IDLE;
    }
    _fcState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_STOPPED);
    if (_saveState) _saveState();
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
        _status->proximityTriggered = false;
        _fcState = _prePauseFCState;
        _fcEntered = false; // re-enter the state to restart timers/relays
        _status->state = (_fcState == FeedCycleState::FC_WAIT) ? SystemState::FEED_WAIT_NEXT : SystemState::FEED_DISPENSING;
        if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_RESUMED);
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
                _status->dispensedQuantity_g += _cfg->feedPerEvent;
                
                bool windowExpired = false;
                if (nowEpoch > 0) {
                    uint32_t secSinceMidnight = nowEpoch % 86400;
                    uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
                    if (secSinceMidnight >= endSecToday) {
                        windowExpired = true;
                    }
                }

                if (_status->currentEvent >= _status->totalEvents || 
                    _status->dispensedQuantity_g >= (_cfg->feedQuantity * 1000.0f) ||
                    windowExpired) {
                    _status->state = SystemState::FEED_FINISHED;
                    _status->feedActive = false;
                    _fcState = FeedCycleState::FC_IDLE;
                    if (windowExpired) {
                        Serial.println("[FEED] 6:00 PM operational window reached. Feeding concluded for today.");
                    }
                    if (_sendEvent) _sendEvent(TelemetryMsgType::SESSION_COMPLETE);
                    if (_saveState) _saveState();
                } else {
                    _status->nextFeedEpoch = (nowEpoch > 0) ? (nowEpoch + (_status->intervalMs / 1000)) : ((nowMs / 1000) + (_status->intervalMs / 1000));
                    _fcTimer = nowMs;
                    _fcState = FeedCycleState::FC_WAIT;
                    _fcEntered = false;
                    if (_saveState) _saveState();
                    Serial.printf("[FEED] Event %d complete. Next in %lu s (Gap interval: %lu ms)\n", 
                                  _status->currentEvent, (_status->intervalMs / 1000), _status->intervalMs);
                }
            }
            break;
            
        case FeedCycleState::FC_WAIT:
            if (!_fcEntered) {
                _status->state = SystemState::FEED_WAIT_NEXT;
                _fcEntered = true;
            }
            // Check if 6:00 PM window has arrived while waiting in gap
            if (nowEpoch > 0) {
                uint32_t secSinceMidnight = nowEpoch % 86400;
                uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
                if (secSinceMidnight >= endSecToday) {
                    if (_motorsOff) _motorsOff();
                    _status->state = SystemState::FEED_FINISHED;
                    _status->feedActive = false;
                    _fcState = FeedCycleState::FC_IDLE;
                    Serial.println("[FEED] 6:00 PM operational window reached during gap wait. Feeding concluded for today.");
                    if (_sendEvent) _sendEvent(TelemetryMsgType::SESSION_COMPLETE);
                    if (_saveState) _saveState();
                    break;
                }
            }
            if ((nowEpoch > 0 && _status->nextFeedEpoch > 0 && nowEpoch >= _status->nextFeedEpoch) || 
                (nowMs - _fcTimer >= _status->intervalMs)) {
                _fcState = FeedCycleState::FC_IDLE;
                _fcEntered = false;
                Serial.println("[FEED] Gap elapsed. Beginning next feed cycle.");
            }
            break;
    }
}

void FeedEngine::recalcDynamic(uint32_t nowEpoch) {
    if (!_status || !_cfg || !_status->feedActive) return;
    
    // Total remaining feed
    float totalTarget_g = _cfg->feedQuantity * 1000.0f;
    float remaining_g = totalTarget_g - _status->dispensedQuantity_g;
    
    if (remaining_g <= 0) {
        // We've already dispensed the target
        stopFeed();
        _status->state = SystemState::FEED_FINISHED;
        return;
    }
    
    // Remaining events
    long remainingEvents = remaining_g / _cfg->feedPerEvent;
    if (remainingEvents <= 0) remainingEvents = 1; // at least 1 event left
    
    // Update total events count
    _status->totalEvents = _status->currentEvent + remainingEvents;
    
    // Recalculate motor time
    float dRate = _cfg->dischargeRate;
    if (dRate <= 0.1f) dRate = 50.0f;
    unsigned long motorTime_ms = (float(_cfg->feedPerEvent) / dRate) * 1000.0f;
    if (motorTime_ms < MOTOR_MIN_RUN_MS) motorTime_ms = MOTOR_MIN_RUN_MS;
    _status->motorTimeMs = motorTime_ms;
    
    // Calculate remaining time
    if (!_status->rtcOK || nowEpoch == 0) return;
    
    uint32_t secSinceMidnight = nowEpoch % 86400;
    uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
    
    if (endSecToday <= secSinceMidnight) {
        // Already past 6:00 PM operational window! Conclude feed cleanly.
        stopFeed();
        _status->state = SystemState::FEED_FINISHED;
        return;
    }
    
    unsigned long remainingTimeMs = (endSecToday - secSinceMidnight) * 1000UL;
    unsigned long singleEvent_ms = MOTOR_PRE_RUN_MS + motorTime_ms + MOTOR_POST_RUN_MS;
    unsigned long remainingEventsDurationMs = remainingEvents * singleEvent_ms;
    
    if (remainingEventsDurationMs >= remainingTimeMs) {
        _status->intervalMs = 0; // No gap time left, run continuously until 6 PM cutoff
    } else {
        _status->intervalMs = (remainingTimeMs - remainingEventsDurationMs) / remainingEvents;
    }
    Serial.printf("[SCHED] Recalculated dynamic: %ld events remaining, gap interval: %lu s (%lu ms)\n",
                  remainingEvents, (_status->intervalMs / 1000UL), _status->intervalMs);
}

bool FeedEngine::shouldAutoStart(uint32_t nowEpoch) {
    if (!_status || !_cfg) return false;
    if (!_status->rtcOK || _status->feedActive || !_status->scheduleValid) return false;
    if (!_cfg->hasBeenRun) return false;
    
    uint32_t secSinceMidnight = nowEpoch % 86400;
    int currentMins = secSinceMidnight / 60;
    int startMins = _cfg->startHour * 60 + _cfg->startMinute;
    
    // Only auto-start during the morning start window (within 30 minutes of scheduled start time)
    if (currentMins >= startMins && currentMins < (startMins + 30) && _status->currentEvent == 0) {
        if (nowEpoch >= _status->nextFeedEpoch) {
            return true;
        }
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
void FeedEngine::setSaveStateCallback(void (*saveState)()) { _saveState = saveState; }

void FeedEngine::resumeFromPowerFailure(uint32_t nowEpoch) {
    if (!_status || !_cfg || !_status->feedActive) return;
    
    // Safety check - if somehow we resumed but we reached target
    if (_status->dispensedQuantity_g >= (_cfg->feedQuantity * 1000.0f)) {
        stopFeed();
        _status->state = SystemState::FEED_FINISHED;
        return;
    }

    // Check if operational window has already passed
    if (nowEpoch > 0) {
        uint32_t secSinceMidnight = nowEpoch % 86400;
        uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
        if (secSinceMidnight >= endSecToday) {
            stopFeed();
            _status->state = SystemState::FEED_FINISHED;
            Serial.println("[SCHED] Power recovered after 6:00 PM window. Feeding concluded.");
            return;
        }
    }
    
    // Recalculate parameters for the remaining time
    recalcDynamic(nowEpoch);
    
    if (_status->feedActive) {
        // Place engine in WAIT state.
        // If we missed events, nowEpoch > nextFeedEpoch, so it will transition to IDLE instantly.
        // If we are still in a gap, it will wait naturally.
        _fcState = FeedCycleState::FC_WAIT;
        _fcEntered = false;
    }
}
