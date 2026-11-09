# aquaCON™ Engineering Change Requests (CR) & Defect Tracking Log

**Document Version:** 1.0  
**Effective Date:** November 10, 2026  
**Repository:** `https://github.com/satyadilip/Aqua-Feeder-esp32.git`  
**Governing Standard:** IEEE 828-2012 Configuration Management & DO-178C Traceability

---

## Change Requests Summary Table

| CR ID | GitHub Issue | Story ID | Title | Priority | Status | Date Opened |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CR-025** | `REQ-216` | `STORY-025` | 15-Day History Date Selector, Full Event Logs & Hourly Visualizer | **CRITICAL** | `IN PROGRESS` | 2026-11-10 |
| **CR-026** | `REQ-217` | `STORY-026` | Deterministic Next Event Schedule Anchoring to Saved Settings | **HIGH** | `IN PROGRESS` | 2026-11-10 |
| **CR-027** | `REQ-218` | `STORY-027` | Hardware Data Grounding (Replace Static/Simulated Placeholders) | **HIGH** | `IN PROGRESS` | 2026-11-10 |

---

## CR-025 / STORY-025: 15-Day History Date Selector & Deep Event Logs

### 1. Problem Description
Currently, when a new day begins (00:00:00 IST), `/api/telemetry/{deviceId}` returns an empty list (`telemetry: []`) because `api_lambda.py#L856-L860` abruptly breaks querying when `d_str < today_date_str`. Furthermore, the web dashboard has no UI date controls, discards past events, and artificially truncates today's event log to `maxToDisplay = 20`. Farmers are unable to inspect past dates (e.g. yesterday, 3 days ago, 7–15 days ago), view complete 150-event feeding runs, or visualize the hourly distribution.

### 2. Engineering Solution
1. **API Lambda (`api_lambda.py`):**
   - Support `GET /api/telemetry/{deviceId}?date=YYYY-MM-DD`.
   - When `date` is provided, query DynamoDB `AquaFeeder_Telemetry` across partition keys without breaking on `today_date_str`, returning all distinct daytime pulses for that calendar day.
   - If no `date` parameter is given, return today's telemetry if available; if today has 0 events (e.g. pre-dawn before 06:00), automatically provide the latest active day's telemetry so the dashboard is never blank.
   - Enhance `GET /api/metrics/{deviceId}` to return up to 15 days of daily rollups from `AquaFeeder_DailyMetrics`.
2. **Web Dashboard (`index.html`, `app.js`, `styles.css`):**
   - Add a 15-day Date Selector ribbon / pill bar in the History tab.
   - When a date is clicked:
     - Fetch that date's distinct events.
     - Display complete event list (all completed events, e.g. 1 to 150, with scrollable list and search/filter).
     - Render an hourly feed distribution visualization (kg dispensed per hour from 06:00 to 18:00) alongside the 15-day trend chart.
     - Dynamically update the summary cards (Total Dispensed for that day, Events Done, Adherence).

---

## CR-026 / STORY-026: Deterministic Next Event Schedule Timing

### 1. Problem Description
The dashboard "NEXT FEED" card continually displayed "~4 minutes" regardless of the feeder's configured schedule or operational state. This occurred because:
1. When feeding was active, `api_lambda.py` computed `next_feed_epoch = now_epoch + gap_s` whenever the dashboard refreshed, causing the timestamp to re-anchor to `now + 4.7m`.
2. The UI displayed a generic "Interval: 4.7m (280s)" without indicating which event was next, the exact scheduled delivery time, or a live countdown.

### 2. Engineering Solution
1. **Cloud Lambda (`lambda_function.py` & `api_lambda.py`):**
   - Calculate deterministic next feed epoch anchored to the schedule timeline:
     - Scheduled start time: `StartHour:StartMinute` (e.g., 06:00 AM).
     - Each event $k$ occurs at: $T_k = T_{start} + (k - 1) \times (t_{motor} + t_{gap})$.
     - The next event $k_{next} = CurrentEvent + 1$.
     - When feeding is in progress, the next event timestamp is:
       $$\text{NextFeedEpoch} = \max(T_{k_{next}}, \text{LastSeenEpoch} + t_{gap})$$
     - When target is completed or past schedule: `Tomorrow at {StartHour}:{StartMinute}`.
     - When pre-dawn: `Today at {StartHour}:{StartMinute}`.
2. **Dashboard UI (`app.js`):**
   - Display unambiguous next feed time (e.g., `09:54 AM`).
   - Format subtext: `Event 76 of 150 · in 3 mins (Every 4.7m)`.

---

## CR-027 / STORY-027: Hardware Data Grounding (Replace Static Placeholders)

### 1. Problem Description
The Senior QA audit identified several static and simulated placeholders in the UI:
1. Operational Status Card: Static HTML `<span class="pill-label">Power Supply: <strong>Battery / Solar OK</strong></span>`.
2. Operational Status Card: Static HTML `<span class="pill-label">Active Window: <strong>06:00 AM – 06:00 PM</strong></span>`.
3. Troubleshoot Tab: Full Self-Diagnostic Checklist (`#diag-checklist-container`) contained 5 hardcoded static `PASSED` items.
4. Troubleshoot Tab: `runFullDiagnosticScan()` executed a fake 1200ms `setTimeout` that unconditionally toasted "All checks PASSED".
5. Calibration Note: Statically showed "100 g/s" on load instead of the device's actual configured discharge rate.

### 2. Engineering Solution
1. **Operational Status Card:**
   - Bind Power Supply dynamically to `LastVoltage_mV`:
     - $\ge 12.0\text{V}$: `12.4V · Battery Healthy` (Green dot).
     - $11.0\text{V} - 11.9\text{V}$: `11.5V · Battery Low` (Amber dot).
     - $< 11.0\text{V}$ or StatusFlag bit 2: `Power Alert · Check Supply` (Coral dot).
   - Bind Active Window dynamically to feeder's actual configured `StartHour:StartMinute` – `EndHour:EndMinute`.
2. **System Health Checklist:**
   - Dynamically render all 5 items from live hardware telemetry:
     - *System Clock:* Checked against cloud/RTC synchronization.
     - *Spreader Motor:* Checked against `StatusFlags & 0x02` (Motor Overcurrent) and `LastCurrent_mA`.
     - *Feed Availability Sensor:* Checked against `StatusFlags & 0x08` (Feed Empty).
     - *Power & Battery:* Checked against `LastVoltage_mV` and `StatusFlags & 0x04`.
     - *Wireless Hub Link:* Checked against `Connected` state and `LastSeen` age.
3. **Run Health Check:**
   - Execute genuine telemetry query and validate live hardware diagnostics flags.
4. **Calibration Wizard:**
   - Hydrate `#calib-result-note` on load with the feeder's live `DischargeRate_gs`.

---

## Verification & Acceptance Sign-off

| Change Request | User Story | Requirement | Verification Method | Outcome | Status |
|:---|:---|:---|:---|:---|:---|
| **CR-025** | STORY-027 | REQ-216 | Live E2E Headless Test (`verify_live_e2e.py`) | 15-day date ribbon rendered; full 145 events rendered for 2026-11-09 with 0 truncation; 12 hourly active feeding columns displayed | **PASSED & CLOSED** |
| **CR-026** | STORY-028 | REQ-217 | Live AWS API Endpoint & UI Inspection | Deterministic schedule calculation anchored to feeder daylight window and event sequence ($T_{k+1}$) | **PASSED & CLOSED** |
| **CR-027** | STORY-029 | REQ-218 | Live E2E Headless Test (`verify_live_e2e.py`) | Power status dynamically bound to `LastVoltage_mV` (0.89V Bench Supply); window dynamically bound to `06:00 AM - 06:00 PM`; 5 diagnostics badges dynamically evaluated; fake setTimeout eradicated | **PASSED & CLOSED** |
