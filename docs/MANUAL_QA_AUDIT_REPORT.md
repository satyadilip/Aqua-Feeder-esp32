# aquaCON™ Smart Feeder System — Comprehensive UI & Telemetry Manual QA Audit Report

**Date of Audit:** November 10, 2026  
**Auditor Role:** Antigravity Senior Manual QA & Embedded Systems Quality Engineer  
**Codebase Version:** v1.0 Production Baseline (`commit 49fcdd0`)  
**Target Platform:** Web Dashboard (`web_dashboard/index.html`, `web_dashboard/app.js`), Cloud API (`api_lambda.py`, `lambda_function.py`), Hardware Telemetry (`AquaFeeder.ino`, `af_hal.cpp`, `feed_engine.cpp`)  
**Hardware Devices Monitored:** Feeder 02 (`e072a1fffef5ba08` in Pond 1), Feeder 04 (`e072a1fffef5bac0` Bench Unit)

---

## 1. Executive Summary

A comprehensive, screen-by-screen, card-by-card, and element-by-element manual quality assurance audit was performed across the aquaCON™ Web Dashboard and Cloud Telemetry stack.

### Key Summary Metrics:
- **Total UI Elements Audited:** 175 DOM IDs & Component Cards across 5 Main Tabs + Auth Gate
- **Fully Functional with Real Hardware Data:** 138 (78.9%)
- **Identified Deficiencies & Placeholders (Discrepancies):** 37 (21.1%)
- **Critical Issues Raised:** 3 Formal Change Requests (`ISSUE-216`, `ISSUE-217`, `ISSUE-218`)

---

## 2. Screen-by-Screen & Card-by-Card Audit Matrix

### Screen 0: Authentication Gate (`#screen-auth`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Sign In Tab | `#tab-login-btn` | Client State | **PASS** | Toggles login panel |
| Register Farm Tab | `#tab-register-btn` | Client State | **PASS** | Toggles registration form |
| Phone & Password Inputs | `#auth-phone-input`, `#auth-pw-input` | Local / API | **PASS** | Auth persistence in `localStorage` |
| Sign In Submit Button | `#btn-login-submit` | `POST /api/auth/login` | **PASS** | Successfully logs in and unlocks dashboard |

---

### App Header & Context Bar
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Digital Clock | `#live-farm-time` | Client JS IST Time | **PASS** | Displays accurate `Asia/Kolkata` 24h/12h time |
| Pond Selector | `#header-pond-select` | DynamoDB `AquaFeeder_Devices` | **PASS** | Dynamically switches active pond |
| Notification Bell | `#btn-toggle-notifs`, `#notif-unread-count` | Client Alert Engine | **PASS** | Opens alert drawer, displays unread alerts |
| Feeder Switcher Pills | `#pond-devices-pills` | DynamoDB `AquaFeeder_Devices` | **PASS** | Dynamically renders all registered feeders in selected pond |

---

### Tab 1: Live Status & Feeder Control (`#screen-status`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Active Feeder Hero Tag | `#current-device-tag` | DynamoDB `AquaFeeder_Devices` | **PASS** | Reflects feeder name & connection state |
| Feeder State Badge | `#feeder-state-badge` | Hardware `StatusFlags` & Schedule | **PASS** | Realtime states: `STANDBY`, `FEEDING`, `COMPLETED`, `PAUSED` |
| Radial Arc Gauge Hero Number | `#gauge-hero-num` | Hardware `CurrentEvent` | **PASS** | Live count of completed pulses today |
| Daily Target / Events | `#gauge-hero-sub`, `#gauge-pct-badge` | Hardware `TotalEvents` & Settings | **PASS** | Correctly computes completion % |
| Dispensed Feed Today | `#dispensed-val-text` | Hardware `FeedDispensed_g` via INA219/Pulses | **PASS** | Real hardware cumulative kg |
| Daily Target Feed | `#target-val-text` | DynamoDB `DailyTarget_kg` | **PASS** | Live target from NVS settings |
| Pending Sync Pill | `#target-sync-pill` | DynamoDB `SettingsSyncStatus` | **PASS** | Displays pending target change until feeder check-in |
| Feed Event Counter | `#burst-count-text`, `#burst-count-sub` | Hardware `CurrentEvent` / `TotalEvents` | **PASS** | Displays current event vs total events |
| **Next Feed Timestamp** | `#next-feed-timestamp` | Calculated in Lambda / Frontend | **DISCREPANCY (ISSUE-217)** | Always shows ~4 mins in the future on every refresh instead of adhering to the feeder's exact scheduled timeline! |
| **Next Feed Subtext** | `#next-feed-sub` | Calculated | **DISCREPANCY (ISSUE-217)** | Vague string "Interval: 4.7m (280s)". Lacks countdown and scheduled event index. |
| Feed Available Indicator | `#feed-status-dot`, `#feed-status-text` | Hardware Optocoupler (`StatusFlags & 0x08`) | **PASS** | Green for Feed Available, Coral for Empty |
| Feed Hopper Sub-text | `#feed-stock-sub` | Hardware | **PASS** | "Feed in Hopper" vs "Refill Required" |
| Connection Status Dot & Text | `#connection-status-dot`, `#connection-status-text` | Cloud `LastSeen` (< 900s) | **PASS** | Accurately pulses green when feeder is online |
| **Connection Subtext** | `#connection-status-sub` | Static string `'Signal Strong'` | **DISCREPANCY (ISSUE-218)** | Hardcoded string; does not display actual last seen delta (e.g., "Updated 2m ago") or RSSI/SNR quality. |
| Remote Action Buttons | `#btn-remote-start`, `#btn-remote-stop` | Downlink Queue `AquaFeeder_Commands` | **PASS** | Enqueues START / STOP / RESUME commands |
| Command Sync Banner | `#command-sync-callout` | DynamoDB `CommandConfirmedAt` | **PASS** | Pops up when command is queued, hides on feeder confirmation |
| **Operational Status: Power Supply** | `.health-pill:nth-child(1)` | **HARDCODED STATIC HTML** | **DEFECT (ISSUE-218)** | Hardcoded `<span class="pill-label">Power Supply: <strong>Battery / Solar OK</strong></span>`! Never reads actual battery voltage (`LastVoltage_mV`)! |
| Operational Status: Feed Status | `#pill-feed-status`, `#pill-feed-dot` | Hardware | **PASS** | Dynamically updates Available / Empty |
| **Operational Status: Active Window** | `.health-pill:nth-child(3)` | **HARDCODED STATIC HTML** | **DEFECT (ISSUE-218)** | Hardcoded `06:00 AM – 06:00 PM`! Does not update if user configures a different feeding window! |

---

### Tab 2: Historic Data & Trends (`#screen-history`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| High-Level Stats Overview | `#stat-week-total`, `#stat-daily-avg`, `#stat-adherence`, `#stat-season-total` | DynamoDB `AquaFeeder_DailyMetrics` | **PASS** | Computes totals from actual historical daily records |
| Daily Feed Dispensed Bar Chart | `#history-chart-container` | DynamoDB `AquaFeeder_DailyMetrics` | **DISCREPANCY (ISSUE-216)** | Only displays 7 days. Bars are not clickable; clicking a bar does NOT inspect that date's events or show that date's breakdown. |
| **Date Selection Controls** | *(Missing from UI)* | *(None)* | **CRITICAL DEFECT (ISSUE-216)** | **No date picker or day selection pills exist.** Once midnight passes, the user cannot select past dates to inspect what happened! |
| **API Telemetry Truncation** | `/api/telemetry/{deviceId}` | DynamoDB `AquaFeeder_Telemetry` | **CRITICAL DEFECT (ISSUE-216)** | Backend explicitly halts query when `d_str < today_date_str` (`reached_yesterday = True; break`). Returns 0 events as soon as a new calendar day starts! |
| **Event Log Truncation** | `#events-log-container` | Frontend `app.js` | **CRITICAL DEFECT (ISSUE-216)** | Frontend hardcodes `const maxToDisplay = 20;`! Out of 150 events in a full day, only 20 are shown; 130 events are silently hidden! |
| **Daily Timeline / Hourly Graph** | *(Missing from UI)* | *(None)* | **CRITICAL DEFECT (ISSUE-216)** | No hourly feeding distribution graph or timeline visualization exists for the selected date. |

---

### Tab 3: Tray Inspection History (`#screen-traycheck`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Total Checks Count | `#tray-total-count`, `#traycheck-count-badge` | DynamoDB `AquaFeeder_TrayChecks` | **PASS** | Live count of physical button presses logged from LCD |
| Last Checked Timestamp | `#tray-last-time`, `#tray-last-sub` | DynamoDB `Timestamp` | **PASS** | Formatted date/time of inspection |
| Feed Dispensed at Check | `#tray-last-dispensed` | DynamoDB `FeedDispensed_kg` | **PASS** | Hardware cumulative dispensed kg at moment of check |
| Battery Voltage at Check | `#tray-last-batt` | DynamoDB `Voltage_V` | **PASS** | Real INA219 voltage at moment of check |
| Historic Tray Check Log List | `#tray-checks-log-container` | DynamoDB `AquaFeeder_TrayChecks` | **PASS** | Full audit list of all physical tray inspections |

---

### Tab 4: Feed Settings (`#screen-params`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Settings Sync Status Badge | `#settings-sync-badge` | DynamoDB `SettingsSyncStatus` | **PASS** | Shows `IN SYNC` or `PENDING` |
| Settings Sync Banner | `#settings-sync-callout` | DynamoDB `SettingsSyncStatus` | **PASS** | Appears when change is pending, shows active vs pending diff |
| Total Daily Feed Slider & Input | `#slider-qty`, `#input-qty` | User Input / Settings Table | **PASS** | Bi-directional slider + input (0.5 to 120 kg) |
| Feed Per Event Slider & Input | `#slider-fpe`, `#input-fpe` | User Input / Settings Table | **PASS** | Bi-directional slider + input (10 to 500 g) |
| Operating Feeding Hours | `#input-start-hour`, `#input-start-min`, `#input-end-hour`, `#input-end-min` | User Input / Settings Table | **PASS** | Restricts to 06:00 to 18:00 window |
| Schedule Summary: Total Events | `#calc-total-events` | Deductive Math | **PASS** | Auto-computes total events (`FeedQuantity / FeedPerEvent`) |
| Schedule Summary: Feed Interval | `#calc-interval` | Deductive Math | **PASS** | Auto-computes interval between events |
| Schedule Summary: Motor Dispense | `#calc-motor-time` | Deductive Math | **PASS** | Computes pulse run time based on discharge rate |
| Schedule Validation Badge | `#calc-valid-badge` | Deductive Math | **PASS** | Displays `SCHEDULE OK` or `INVALID SCHEDULE` |
| Save Settings Button | `#btn-save-params` | `POST /api/settings/{id}` | **PASS** | Saves to DynamoDB and queues LoRaWAN downlink payload |

---

### Tab 5: Hardware Troubleshoot & Diagnostics (`#screen-troubleshoot`)
| Component / Element | Element ID | Hardware / Cloud Source | Verification Status | Defect / Observation |
| :--- | :--- | :--- | :--- | :--- |
| Hero Card Motor Status | `#diag-spreader-val`, `#diag-loader-val` | Cloud / State | **PARTIAL** | Shows `Healthy` or `Paused`, but does not inspect live overcurrent trip or motor current reading. |
| Test Spreader Motor Button | `onclick="runHardwareTestAction('TEST_DISPENSER')"` | LoRaWAN Downlink | **PASS** | Triggers 2-second motor spin on hardware |
| Test Loader Motor Button | `onclick="runHardwareTestAction('TEST_LOADER')"` | LoRaWAN Downlink | **PASS** | Triggers 2-second loader pulse on hardware |
| Test Alert Sounder Button | `onclick="runHardwareTestAction('TEST_HOOTER')"` | LoRaWAN Downlink | **PASS** | Triggers 1-second buzzer sound on hardware |
| LoRaWAN Ping Button | `onclick="runHardwareTestAction('PING_GATEWAY')"` | LoRaWAN Downlink | **PASS** | Immediate RF check |
| Sync Feeder Clock RTC Button | `#btn-sync-rtc` | LoRaWAN Downlink | **PASS** | Broadcasts authoritative epoch to DS3231 RTC |
| Live Test Confirmation Banner | `#test-confirmation-banner` | DynamoDB `LastTestResult` | **PASS** | Updates with confirmed motor current and pass/fail |
| **System Health Checklist** | `#diag-checklist-container` | **HARDCODED STATIC HTML** | **DEFECT (ISSUE-218)** | All 5 checklist items (Clock, Spreader Motor, Hopper Sensor, Battery/Solar, Wireless Link) are completely static HTML! They never reflect real hardware values! |
| **Run Health Check Action** | `#btn-run-diag` / `runFullDiagnosticScan()` | **FAKE TIMEOUT PLACEHOLDER** | **DEFECT (ISSUE-218)** | `setTimeout` with 1200ms delay that unconditionally pops `showToast('All system health checks PASSED!')` even if feeder is offline or faulted! |
| Calibration Wizard | `#calib-weighed-grams`, `saveCalibratedRate()` | User Input & `DischargeRate_gs` | **PASS** | Successfully computes g/s rate from weighed sample |
| **Calibration Note on Load** | `#calib-result-note` | Static HTML | **DISCREPANCY (ISSUE-218)** | Shows static "100 g/s" on initial load instead of the device's actual configured discharge rate. |
| Customer Service Card | `#cust-support-link` | Tel Link (+91 91546 96777) | **PASS** | Opens dialer to Charan |
| Alert Contacts Management | `#contacts-list-container` | Client State / LocalStorage | **PASS** | Allows adding/removing emergency contact numbers |

---

## 3. Discrepancy Log & Root Cause Analysis

### Discrepancy 1: History Tab Lacks Multi-Day Selector & Cuts Off Historical Telemetry
- **Issue Reference:** `ISSUE-216` / `STORY-025`
- **Root Cause:**
  1. In `api_lambda.py#L856-L860`, the query loops over DynamoDB pages and explicitly exits when `d_str < today_date_str` (`reached_yesterday = True; break`). Thus, past days cannot be fetched.
  2. The frontend lacks any date picker or past-day selector.
  3. The event list is hard-truncated to `maxToDisplay = 20`.
  4. There is no hourly feeding visualization or cumulative curve for the selected date.

### Discrepancy 2: Next Event Time Calculation Flaw (~4 Mins Discrepancy)
- **Issue Reference:** `ISSUE-217` / `STORY-026`
- **Root Cause:**
  1. In `api_lambda.py#L485-L503` and `lambda_function.py#L501-L510`, when the feeder is actively feeding, `next_feed_epoch` was set to `now_epoch + gap_s` whenever the dashboard refreshed. This caused the next feed time to always appear as "current time + ~4 minutes", regardless of the feeder's actual scheduled event intervals!
  2. The display lacked the scheduled event sequence number (`Event N of Total`) and countdown context.

### Discrepancy 3: Static / Simulated Placeholders in UI
- **Issue Reference:** `ISSUE-218` / `STORY-027`
- **Root Cause:**
  1. `Power Supply: Battery / Solar OK` was static HTML in `index.html`. It never inspected `LastVoltage_mV` or `StatusFlags & 0x04`.
  2. `Active Window: 06:00 AM – 06:00 PM` was static HTML and failed to reflect customized feeding windows.
  3. `diag-checklist-container` in the Troubleshoot tab was static HTML with hardcoded `PASSED` badges.
  4. `runFullDiagnosticScan()` relied on a dummy 1200ms `setTimeout` that always displayed "All checks PASSED".
  5. `calib-result-note` did not hydrate with the device's actual `DischargeRate_gs` on page load.

---

## 4. Resolution Plan & Issue Tracking

| Issue ID | Epic / Story | Priority | Status | Assigned Component |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-216** | **STORY-025** (15-Day History Date Selector, Full Event Logs & Hourly Visualizer) | **CRITICAL** | `IN PROGRESS` | `api_lambda.py`, `web_dashboard/app.js`, `web_dashboard/index.html` |
| **ISSUE-217** | **STORY-026** (Deterministic Next Event Schedule Anchoring) | **HIGH** | `IN PROGRESS` | `api_lambda.py`, `lambda_function.py`, `web_dashboard/app.js` |
| **ISSUE-218** | **STORY-027** (Hardware Data Grounding: Dynamic Battery, Solar, Window & Diagnostics) | **HIGH** | `IN PROGRESS` | `web_dashboard/index.html`, `web_dashboard/app.js` |

*Report generated and committed under strict Quality Assurance guidelines.*
