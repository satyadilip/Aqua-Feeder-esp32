#include "feed_engine.h"

void FeedEngine::begin(SystemStatus* status, DeviceConfig* cfg) {
    _status = status;
    _cfg = cfg;
    _fcState = FeedCycleState::FC_IDLE;
    _prePauseFCState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    _isPaused = false;
    _fcTimer = 0;
    _lastCurrentCheckMs = 0;
    _pauseStartMs = 0;
    _lastFedDay = (_status && _status->lastFedDay > 0) ? _status->lastFedDay : 0;
    
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
    
    if (nowEpoch == 0 && _status->currentEpoch > 0) {
        nowEpoch = _status->currentEpoch;
    }
    
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
    uint32_t currentDay = (nowEpoch > 0) ? (nowEpoch / 86400) : 0;
    bool isSameDay = (_lastFedDay == 0 || _lastFedDay == currentDay);

    uint16_t remainingEvents = 0;
    if (isSameDay && _status->currentEvent > 0 && _status->dispensedQuantity_g > 0) {
        float remaining_g = qty_g - _status->dispensedQuantity_g;
        if (remaining_g > 0) {
            remainingEvents = (uint16_t)ceil(remaining_g / (float)_cfg->feedPerEvent);
            _status->totalEvents = _status->currentEvent + remainingEvents;
        } else {
            remainingEvents = 0;
            _status->totalEvents = _status->currentEvent;
        }
    } else {
        _status->totalEvents = (uint16_t)ceil(qty_g / (float)_cfg->feedPerEvent);
        remainingEvents = _status->totalEvents;
    }
    
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
    unsigned long eventsDuration_ms = remainingEvents * singleEvent_ms;
    unsigned long fullWindow_ms = (endMins - startMins) * 60UL * 1000UL;

    // Check: Can the requested quantity physically fit within the operational daylight window?
    if (eventsDuration_ms >= fullWindow_ms) {
        strncpy(_status->schedError, "Time Too Short", sizeof(_status->schedError)-1);
        Serial.println("[SCHED] Error: Configured feed parameters cannot fit before configured end time!");
        return false;
    }

    unsigned long availableTime_ms = fullWindow_ms;

    if (nowEpoch > 0) {
        uint32_t secSinceMidnight = nowEpoch % 86400;
        int currentMins = secSinceMidnight / 60;
        uint32_t midnightEpoch = nowEpoch - secSinceMidnight;
        uint32_t startEpochToday = midnightEpoch + ((uint32_t)startMins * 60UL);
        uint32_t endEpochToday   = midnightEpoch + ((uint32_t)endMins * 60UL);

        // If today's feed is concluded (target reached, all events done, or state is FEED_FINISHED), schedule for tomorrow!
        // Completed today strictly if full daily target quantity or all events were dispensed
        bool isCompletedToday = (isSameDay && _status->currentEvent > 0 && 
                                (_status->dispensedQuantity_g >= qty_g || _status->currentEvent >= _status->totalEvents));

        if (isCompletedToday || currentMins >= endMins) {
            // Concluded for today -> Arm/schedule for tomorrow's start time at startHour:startMinute!
            _status->scheduleValid = true;
            _status->nextFeedEpoch = startEpochToday + 86400UL;
            unsigned long fullEvents = (unsigned long)ceil(qty_g / (float)_cfg->feedPerEvent);
            unsigned long fullEventsDur = fullEvents * singleEvent_ms;
            _status->intervalMs = (fullEventsDur < fullWindow_ms && fullEvents > 0) ? ((fullWindow_ms - fullEventsDur) / fullEvents) : 5000UL;
            if (_status->intervalMs < 5000UL) _status->intervalMs = 5000UL;
            Serial.printf("[SCHED] Today's feed concluded (or past %02d:%02d). Next daily feed armed for tomorrow at %02d:%02d (epoch %lu, gap %lu s).\n",
                          endMins / 60, endMins % 60, startMins / 60, startMins % 60, _status->nextFeedEpoch, (_status->intervalMs / 1000UL));
            return true;
        } else if (currentMins >= startMins) {
            // Mid-day start! Dynamically calculate remaining time until configured endHour:endMinute
            uint32_t endSecToday = (uint32_t)endMins * 60UL;
            if (endSecToday > secSinceMidnight) {
                availableTime_ms = (endSecToday - secSinceMidnight) * 1000UL;
            }
            _status->nextFeedEpoch = nowEpoch; // Mid-day trigger: initiate feed immediately
            Serial.printf("[SCHED] Mid-day start at %02d:%02d. Remaining window: %lu s until %02d:%02d\n",
                          currentMins / 60, currentMins % 60, (availableTime_ms / 1000UL), endMins / 60, endMins % 60);
        } else {
            // Out of feeding hours (early morning before start time) -> Arm/schedule for today's start time!
            availableTime_ms = fullWindow_ms;
            _status->nextFeedEpoch = startEpochToday;
            Serial.printf("[SCHED] Pre-dawn check at %02d:%02d: Feeder in STANDBY. Daily feed armed for today at %02d:%02d.\n",
                          currentMins / 60, currentMins % 60, startMins / 60, startMins % 60);
        }

        // Check: For mid-day start, can it finish in the remaining time today?
        if (eventsDuration_ms >= availableTime_ms) {
            // Remaining window today is shorter than needed. Arm for tomorrow at configured startHour:startMinute!
            _status->scheduleValid = true;
            _status->nextFeedEpoch = startEpochToday + 86400UL;
            unsigned long fullEvents = (unsigned long)ceil(qty_g / (float)_cfg->feedPerEvent);
            unsigned long fullEventsDur = fullEvents * singleEvent_ms;
            _status->intervalMs = (fullEventsDur < fullWindow_ms && fullEvents > 0) ? ((fullWindow_ms - fullEventsDur) / fullEvents) : 5000UL;
            if (_status->intervalMs < 5000UL) _status->intervalMs = 5000UL;
            Serial.printf("[SCHED] Remaining window today (%lu s) too short for %lu s feed. Next daily feed armed for tomorrow at %02d:%02d (epoch %lu, gap %lu s).\n",
                          (availableTime_ms / 1000UL), (eventsDuration_ms / 1000UL), startMins / 60, startMins % 60, _status->nextFeedEpoch, (_status->intervalMs / 1000UL));
            return true;
        }
    }
    
    _status->intervalMs = (remainingEvents > 0) ? ((availableTime_ms - eventsDuration_ms) / remainingEvents) : 5000UL;
    if (_status->intervalMs < 5000UL) _status->intervalMs = 5000UL; // Safety minimum gap of 5 seconds
    Serial.printf("[SCHED] Schedule OK: %d events, motorTime: %lu ms, gap interval: %lu s (%lu ms)\n",
                  _status->totalEvents, _status->motorTimeMs, (_status->intervalMs / 1000UL), _status->intervalMs);
    
    _status->scheduleValid = true;
    return true;
}

void FeedEngine::startFeed(uint32_t nowEpoch) {
    if (!_status || !_cfg) return;
    if (nowEpoch == 0 && _status->currentEpoch > 0) nowEpoch = _status->currentEpoch;

    // Guard 1: Prevent auto-restart on the same day if today's feed is already complete
    if (nowEpoch > 0) {
        uint32_t currentDay = nowEpoch / 86400;
        float target_g = _cfg->feedQuantity * 1000.0f;
        if (_lastFedDay == currentDay && (_status->currentEvent >= _status->totalEvents || _status->dispensedQuantity_g >= target_g)) {
            Serial.printf("[FEED] [GUARD REJECT] Feed already completed for today (%d/%ld events, %.1fg dispensed). Auto-start rejected!\n",
                          _status->currentEvent, _status->totalEvents, _status->dispensedQuantity_g);
            _status->state = SystemState::FEED_FINISHED;
            _status->feedActive = false;
            return;
        }

        // Guard 2: STRICT NIGHT GUARD - strictly prohibit dispensing outside configured operational hours (e.g. 06:00 - 18:00)
        uint32_t secSinceMidnight = nowEpoch % 86400;
        uint32_t startSecToday = (_cfg->startHour * 3600UL) + (_cfg->startMinute * 60UL);
        uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
        if (secSinceMidnight < startSecToday || secSinceMidnight >= endSecToday) {
            Serial.printf("[FEED] [STRICT NIGHT GUARD] Start feed requested outside daylight window (%02lu:%02lu). Feeder ARMED for start time (%02d:%02d)!\n",
                          (unsigned long)(secSinceMidnight / 3600), (unsigned long)((secSinceMidnight % 3600) / 60),
                          _cfg->startHour, _cfg->startMinute);
            if (_cfg && !_cfg->hasBeenRun) {
                _cfg->hasBeenRun = true;
                if (_saveState) _saveState();
            }
            _status->feedActive = false;
            _status->state = SystemState::IDLE;
            calcSchedule(nowEpoch);
            return;
        }
    }

    uint32_t currentDay = (nowEpoch > 0) ? (nowEpoch / 86400) : 0;
    bool isSameDayContinuation = (_lastFedDay != 0 && currentDay == _lastFedDay && _status->currentEvent > 0);

    if (_cfg && !_cfg->hasBeenRun) {
        _cfg->hasBeenRun = true;
        if (_saveState) _saveState();
    }
    _isPaused = false;
    _status->feedActive = true;
    _fcEntered = false;
    _prePauseFCState = FeedCycleState::FC_IDLE;

    if (!isSameDayContinuation) {
        _status->currentEvent = 0;
        _status->dispensedQuantity_g = 0.0f;
    } else {
        Serial.printf("[FEED] Continuing existing cycle for today (%d events already done, %.1fg dispensed).\n",
                      _status->currentEvent, _status->dispensedQuantity_g);
        recalcDynamic(nowEpoch);
    }

    if (nowEpoch > 0) {
        _lastFedDay = currentDay;
        if (_status) _status->lastFedDay = _lastFedDay;
    }

    // Manual / Remote Start: Initiate dispense cycle immediately without delay
    _status->nextFeedEpoch = nowEpoch;
    _status->feedState = FeedCycleState::FC_IDLE;
    _fcState = FeedCycleState::FC_IDLE;
    _fcTimer = millis() - 10000UL; // Bypass gap delay so first pulse starts immediately
    Serial.println("[FEED] Start feed: initiating cycle immediately");

    if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_STARTED);
    if (_saveState) _saveState();
}

void FeedEngine::stopFeed() {
    _isPaused = false;
    if (_motorsOff) _motorsOff();
    if (_status) {
        _status->feedActive = false;
        _status->feedState = FeedCycleState::FC_IDLE;
        _status->state = SystemState::FEED_FINISHED;
    }
    _fcState = FeedCycleState::FC_IDLE;
    _prePauseFCState = FeedCycleState::FC_IDLE;
    _fcEntered = false;
    if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_STOPPED);
    if (_saveState) _saveState();
}

void FeedEngine::pauseFeed() {
    if (_isPaused) return; // Prevent duplicate pause calls
    if (_status && _status->feedActive) {
        _isPaused = true;
        _prePauseFCState = (_fcState != FeedCycleState::FC_IDLE) ? _fcState : FeedCycleState::FC_WAIT;
        _pauseStartMs = millis();
        if (_motorsOff) _motorsOff();
        _status->state = SystemState::FEED_PAUSED;
        _fcState = FeedCycleState::FC_IDLE; // wait in idle while paused
        _fcEntered = false;
        if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_PAUSED);
        if (_saveState) _saveState();
        Serial.println("[FEED] Feed engine PAUSED. Pre-pause state latched.");
    }
}

void FeedEngine::resumeFeed(uint32_t nowEpoch) {
    if (!_status) return;
    if (_isPaused || _status->state == SystemState::FEED_PAUSED || _status->proximityTriggered || _status->feedActive) {
        _isPaused = false;
        _status->feedActive = true;
        _status->proximityTriggered = false;
        
        if (nowEpoch == 0 && _status->currentEpoch > 0) nowEpoch = _status->currentEpoch;

        // Architectural check: Did the pause & resume occur within the existing FC_WAIT window?
        bool canResumeInWaitGap = false;
        if (_prePauseFCState == FeedCycleState::FC_WAIT) {
            if (nowEpoch > 0 && _status->nextFeedEpoch > nowEpoch) {
                // Absolute RTC time: We are still inside the original wait gap!
                canResumeInWaitGap = true;
            } else if (nowEpoch == 0 && _status->intervalMs > 0) {
                // Fallback millis: check if pause elapsed time still fits within intervalMs
                unsigned long pauseDurationMs = millis() - _pauseStartMs;
                unsigned long elapsedBeforePause = (_pauseStartMs > _fcTimer) ? (_pauseStartMs - _fcTimer) : 0;
                if ((elapsedBeforePause + pauseDurationMs) < _status->intervalMs) {
                    _fcTimer += pauseDurationMs; // Shift gap timer forward by pause duration
                    canResumeInWaitGap = true;
                }
            }
        }

        if (canResumeInWaitGap) {
            // SCENARIO 1: Paused and resumed within the same wait cycle!
            // No daylight feeding time was lost. Return directly to FC_WAIT.
            // Do NOT recalculate schedule. Do NOT fire motor prematurely.
            _fcState = FeedCycleState::FC_WAIT;
            _fcEntered = false;
            _status->state = SystemState::FEED_WAIT_NEXT;
            Serial.printf("[FEED] Resumed within wait window. Event %d scheduled at epoch %lu (%ld s remaining, no recalc needed).\n",
                          _status->currentEvent + 1, _status->nextFeedEpoch, 
                          (nowEpoch > 0 && _status->nextFeedEpoch > nowEpoch) ? (long)(_status->nextFeedEpoch - nowEpoch) : 0);
        } else {
            // SCENARIO 2: Paused during motor pulse, OR pause duration exceeded the wait gap.
            // Feeding time was lost or pulse was interrupted: recalculate dynamic schedule and initiate dispense cycle immediately!
            _fcState = FeedCycleState::FC_IDLE;
            _fcEntered = false;
            _fcTimer = millis() - 10000UL; // Bypass gap delay so pulse starts immediately
            _status->state = SystemState::FEED_WAIT_NEXT;
            
            if (nowEpoch > 0) {
                recalcDynamic(nowEpoch);
                _status->nextFeedEpoch = nowEpoch;
            }
            Serial.println("[FEED] Resumed after wait gap elapsed or during pulse: recalculated dynamic schedule & initiated cycle.");
        }

        _prePauseFCState = FeedCycleState::FC_IDLE; // Reset pre-pause latch
        if (_sendEvent) _sendEvent(TelemetryMsgType::FEED_RESUMED);
        if (_saveState) _saveState();
    }
}

void FeedEngine::update(unsigned long nowMs, uint32_t nowEpoch) {
    if (!_status) return;
    if (nowEpoch == 0 && _status->currentEpoch > 0) nowEpoch = _status->currentEpoch;

    // Autonomous day rollover for daily recurring feed (evaluates every midnight regardless of state)
    if (nowEpoch > 0) {
        uint32_t currentDay = nowEpoch / 86400;
        if (_lastFedDay != 0 && currentDay > _lastFedDay) {
            _status->feedActive = false;
            _status->currentEvent = 0;
            _status->dispensedQuantity_g = 0.0f;
            _status->state = SystemState::IDLE;
            _fcState = FeedCycleState::FC_IDLE;
            _fcEntered = false;
            _lastFedDay = currentDay;
            _status->lastFedDay = currentDay;
            calcSchedule(nowEpoch);
            if (_saveState) _saveState();
            Serial.printf("[SCHED] Day rolled over to calendar day %lu. Daily counters reset.\r\n", currentDay);
        } else if (_lastFedDay == 0) {
            _lastFedDay = currentDay;
            if (_status) _status->lastFedDay = currentDay;
        }
    }

    if (!_status->feedActive) return;
    if (_isPaused || _status->state == SystemState::FEED_PAUSED) return;
    
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
            // Check for jammed spreader after 500ms initial inrush
            if (_readCurrent && (nowMs - _fcTimer >= 500UL)) {
                float current = _readCurrent();
                if (current > (_cfg ? _cfg->overcurrentLimit : OVERCURRENT_LIMIT_MA)) {
                    Serial.printf("[FEED] Spreader stalled during pre-warmup! (%.1f mA)\n", current);
                    pauseFeed();
                    if (_sendEvent) _sendEvent(TelemetryMsgType::ALARM_OVERCURRENT);
                    return;
                }
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
                    if (_cfg && _cfg->hasBeenRun && nowEpoch > 0) calcSchedule(nowEpoch);
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
            // STRICT NIGHT GUARD: Check if operational window boundary has arrived while waiting in gap
            if (nowEpoch > 0) {
                uint32_t secSinceMidnight = nowEpoch % 86400;
                uint32_t startSecToday = (_cfg->startHour * 3600UL) + (_cfg->startMinute * 60UL);
                uint32_t endSecToday = (_cfg->endHour * 3600UL) + (_cfg->endMinute * 60UL);
                if (secSinceMidnight < startSecToday || secSinceMidnight >= endSecToday) {
                    if (_motorsOff) _motorsOff();
                    _status->state = SystemState::FEED_FINISHED;
                    _status->feedActive = false;
                    _fcState = FeedCycleState::FC_IDLE;
                    Serial.printf("[FEED] [STRICT NIGHT GUARD] Operational window boundary reached (%02lu:%02lu). Feeding halted for the night.\n",
                                  (unsigned long)(secSinceMidnight / 3600), (unsigned long)((secSinceMidnight % 3600) / 60));
                    if (_sendEvent) _sendEvent(TelemetryMsgType::SESSION_COMPLETE);
                    if (_saveState) _saveState();
                    if (_cfg && _cfg->hasBeenRun && nowEpoch > 0) calcSchedule(nowEpoch);
                    break;
                }
            }
            // Failsafe: clamp intervalMs to at least 5000 ms to prevent relay chatter
            if (_status->intervalMs < 5000UL) _status->intervalMs = 5000UL;

            if ((nowEpoch > 0 && _status->nextFeedEpoch > 0 && nowEpoch >= _status->nextFeedEpoch) || 
                (nowEpoch == 0 && nowMs - _fcTimer >= _status->intervalMs)) {
                // Ensure at least 5 seconds have elapsed since the last cycle completed
                if (nowMs - _fcTimer >= 5000UL) {
                    _fcState = FeedCycleState::FC_IDLE;
                    _fcEntered = false;
                    Serial.println("[FEED] Gap elapsed. Beginning next feed cycle.");
                }
            }
            break;
    }
}

bool FeedEngine::recalcDynamic(uint32_t nowEpoch) {
    if (!_status || !_cfg) return false;
    if (!_status->feedActive && _status->dispensedQuantity_g == 0.0f) return false;
    
    // Check 1: Operational Window hard limit [06:00, 18:00]
    if (_cfg->startHour < OP_START_HOUR || _cfg->endHour > OP_END_HOUR || (_cfg->endHour == OP_END_HOUR && _cfg->endMinute > 0)) {
        _status->scheduleValid = false;
        strncpy(_status->schedError, "Out of OP Window", sizeof(_status->schedError)-1);
        return false;
    }
    
    int startMins = _cfg->startHour * 60 + _cfg->startMinute;
    int endMins = _cfg->endHour * 60 + _cfg->endMinute;
    if (endMins <= startMins) {
        _status->scheduleValid = false;
        strncpy(_status->schedError, "End < Start", sizeof(_status->schedError)-1);
        return false;
    }
    
    if (_cfg->feedQuantity <= 0 || _cfg->feedPerEvent <= 0 || _cfg->dischargeRate <= 0) {
        _status->scheduleValid = false;
        strncpy(_status->schedError, "Invalid Params", sizeof(_status->schedError)-1);
        return false;
    }

    // Total remaining feed
    float totalTarget_g = _cfg->feedQuantity * 1000.0f;
    float remaining_g = totalTarget_g - _status->dispensedQuantity_g;
    
    if (remaining_g <= 0) {
        // Target already achieved with what was dispensed
        stopFeed();
        _status->state = SystemState::FEED_FINISHED;
        return true;
    }
    
    // Remaining events
    long remainingEvents = (long)ceil(remaining_g / (float)_cfg->feedPerEvent);
    if (remainingEvents <= 0) remainingEvents = 1;
    
    // Update total events count
    _status->totalEvents = _status->currentEvent + remainingEvents;
    
    // Recalculate motor time
    float dRate = _cfg->dischargeRate;
    if (dRate <= 0.1f) dRate = 50.0f;
    unsigned long motorTime_ms = (float(_cfg->feedPerEvent) / dRate) * 1000.0f;
    if (motorTime_ms < MOTOR_MIN_RUN_MS) motorTime_ms = MOTOR_MIN_RUN_MS;
    _status->motorTimeMs = motorTime_ms;
    
    // Calculate remaining time
    if (nowEpoch == 0 && _status->currentEpoch > 0) nowEpoch = _status->currentEpoch;
    if (nowEpoch == 0) return true;
    
    uint32_t secSinceMidnight = nowEpoch % 86400;
    uint32_t endSecToday = ((uint32_t)_cfg->endHour * 3600UL) + ((uint32_t)_cfg->endMinute * 60UL);
    
    if (endSecToday <= secSinceMidnight) {
        // Already past configured operational window! Conclude feed cleanly.
        _status->scheduleValid = false;
        strncpy(_status->schedError, "Past End Time", sizeof(_status->schedError)-1);
        stopFeed();
        _status->state = SystemState::FEED_FINISHED;
        return false;
    }
    
    unsigned long remainingTimeMs = (endSecToday - secSinceMidnight) * 1000UL;
    unsigned long singleEvent_ms = MOTOR_PRE_RUN_MS + motorTime_ms + MOTOR_POST_RUN_MS;
    unsigned long remainingEventsDurationMs = remainingEvents * singleEvent_ms;
    
    if (remainingEventsDurationMs >= remainingTimeMs) {
        if (remainingTimeMs < 60000UL) {
            // Under 1 minute left before operational window ends - conclude cleanly for today
            _status->scheduleValid = false;
            strncpy(_status->schedError, "Time Too Short", sizeof(_status->schedError)-1);
            stopFeed();
            _status->state = SystemState::FEED_FINISHED;
            Serial.println("[SCHED] Less than 1 minute remaining in daylight window. Feeding concluded for today.");
            return false;
        } else {
            // Window is tight: clamp to minimum safe gap (5s) to deliver maximum feed before operational window ends
            _status->intervalMs = 5000UL;
            _status->scheduleValid = true;
            memset(_status->schedError, 0, sizeof(_status->schedError));
            if (_fcState == FeedCycleState::FC_WAIT) {
                _status->nextFeedEpoch = nowEpoch;
            }
            Serial.printf("[SCHED] Window tight: set to minimum 5s gap to deliver feed before %02d:%02d.\n",
                          _cfg->endHour, _cfg->endMinute);
            return true;
        }
    }
    
    _status->intervalMs = (remainingTimeMs - remainingEventsDurationMs) / remainingEvents;
    _status->scheduleValid = true;
    memset(_status->schedError, 0, sizeof(_status->schedError));
    
    if (_fcState == FeedCycleState::FC_WAIT) {
        _status->nextFeedEpoch = nowEpoch + (_status->intervalMs / 1000UL);
    }
    
    Serial.printf("[SCHED] Recalculated dynamic: %ld events remaining, gap interval: %lu s (%lu ms)\n",
                  remainingEvents, (_status->intervalMs / 1000UL), _status->intervalMs);
    return true;
}

bool FeedEngine::shouldAutoStart(uint32_t nowEpoch) {
    if (!_status || !_cfg) return false;
    if (!_status->rtcOK || _status->feedActive) return false;
    if (!_cfg->hasBeenRun) return false;
    
    uint32_t secSinceMidnight = nowEpoch % 86400;
    int currentMins = secSinceMidnight / 60;
    int startMins = _cfg->startHour * 60 + _cfg->startMinute;
    int endMins = _cfg->endHour * 60 + _cfg->endMinute;
    
    // Only auto-start during daylight operational window
    if (currentMins >= startMins && currentMins < endMins) {
        uint32_t currentDay = nowEpoch / 86400;
        // If we have already finished feeding today, do not auto-start again today!
        if (_lastFedDay == currentDay) {
            float target_g = _cfg->feedQuantity * 1000.0f;
            if (_status->dispensedQuantity_g >= target_g || 
                (_status->totalEvents > 0 && _status->currentEvent >= _status->totalEvents)) {
                return false;
            }
        }

        // Never auto-start if next feed is scheduled in future (e.g. tomorrow)
        if (_status->nextFeedEpoch > nowEpoch) {
            return false;
        }

        static unsigned long lastSchedAttemptMs = 0;
        if (!_status->scheduleValid) {
            if (millis() - lastSchedAttemptMs > 10000UL) {
                lastSchedAttemptMs = millis();
                calcSchedule(nowEpoch);
            }
        }
        if (_status->scheduleValid && _status->intervalMs > 0 && nowEpoch >= _status->nextFeedEpoch) {
            return true;
        }
    }
    return false;
}

bool FeedEngine::isActive() const {
    return _status && _status->feedActive;
}

bool FeedEngine::isPaused() const {
    return _isPaused || (_status && _status->state == SystemState::FEED_PAUSED);
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
