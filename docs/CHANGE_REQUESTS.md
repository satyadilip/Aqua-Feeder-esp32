# aquaCON™ Engineering Change Requests (CR) & Defect Tracking Log

**Document Version:** 1.0  
**Effective Date:** November 10, 2026  
**Repository:** `https://github.com/satyadilip/Aqua-Feeder-esp32.git`  
**Governing Standard:** IEEE 828-2012 Configuration Management & DO-178C Traceability

---

## Change Requests Summary Table

| CR ID | GitHub Issue | Story ID | Title | Priority | Status | Date Opened |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CR-025** | `REQ-216` | `STORY-025` | 15-Day History Date Selector, Full Event Logs & Hourly Visualizer | **CRITICAL** | `CLOSED` | 2026-11-10 |
| **CR-026** | `REQ-217` | `STORY-026` | Deterministic Next Event Schedule Anchoring to Saved Settings | **HIGH** | `CLOSED` | 2026-11-10 |
| **CR-027** | `REQ-218` | `STORY-027` | Hardware Data Grounding (Replace Static/Simulated Placeholders) | **HIGH** | `CLOSED` | 2026-11-10 |
| **CR-028** | `REQ-219` | `STORY-030` | Enterprise History Date Explorer & Available-Day Dynamic Window | **HIGH** | `CLOSED` | 2026-11-10 |
| **CR-029** | `REQ-220` | `STORY-031` | Sliding Daily Feed Dispensed Bar Chart & Boundary Encapsulation | **HIGH** | `CLOSED` | 2026-11-10 |
| **CR-030** | `REQ-221` | `STORY-032` | Daily Feed Master Chart with Interactive Day Inspection Modal | **CRITICAL** | `CLOSED` | 2026-11-10 |

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
| **CR-028** | STORY-030 | REQ-219 | Live Headless E2E Test (`verify_enterprise_history.py`) | Date Explorer card aligned inside standard `.card` layout; available history dynamic (1 day on Feeder 04, 13 days on Feeder 02, zero forced 15 blank days); left/right chevrons, wheel horizontal scroll, and calendar picker fully operational; 0 hanging 'Loading dates...' states | **PASSED & CLOSED** |
| **CR-029** | STORY-031 | REQ-220 | Live Headless E2E Test (`verify_sliding_barchart.py`) | Daily Feed Dispensed chart encapsulated in `.barchart-slider-wrapper` inside card boundaries; fixed 62px column widths prevent label collision; left/right sliding chevrons & wheel scrolling operational; single-day charts centered cleanly | **PASSED & CLOSED** |
| **CR-030** | STORY-032 | REQ-221 | Live Headless E2E Test (`verify_day_inspector_modal.py`) | Master Daily Bar Chart with kg on top; Day Inspection Modal with 4 summary KPIs, dual-view toggle (Hourly Graph & Event Timeline), date stepping, and close button ✕ verified across 8/8 automated test cases | **PASSED & CLOSED** |

---

## CR-028 / STORY-030: Enterprise History Date Explorer, Dynamic Available-Day History & Boundary Alignment

### 1. Problem Description
User review identified critical issues in the History tab UI:
1. **Hanging State:** UI remained stuck displaying "Loading dates..." in `#history-active-date-lbl`.
2. **Boundary Crossing & Misalignment:** The date selector ribbon was placed outside a `.card` container without margin alignment (`margin: 10px 0 14px`), causing it to spill 16px past the edges of the cards above and below it.
3. **Scroll Deficiency:** The horizontal date ribbon lacked scroll controls (chevrons), mouse-wheel interception, or scroll-snap, making it difficult or impossible to scroll across dates on desktop and mobile.
4. **Forced 15-Day History:** Devices with only 1 or 4 days of history (such as Feeder 04 with 1 day, or Feeder 02 with 5 days) were forced into 15 days of dummy placeholder records, displaying a cluttered ribbon of empty dates back into October.

### 2. Engineering Solution
1. **Dynamic Available-Day History (`api_lambda.py` & `app.js`):**
   - In `GET /api/metrics/{deviceId}`, determine the earliest recorded activity date within the 15-day window.
   - If a device has records from `2026-11-06`, span exactly 5 days (Nov 6 to Nov 10).
   - If a device has 0 records prior to today (e.g. Feeder 04), span only 1 day (`Today`).
   - Eliminate hardcoded 15-day fallbacks that generate fake empty days.
2. **Enterprise Card Encapsulation (`index.html` & `styles.css`):**
   - Wrap the date selector inside a standard dashboard card: `<div class="card history-date-card">`.
   - Adhere strictly to the dashboard's `margin: 0 16px 14px` and border-radius rules.
3. **Smooth Scroll & Navigation Chevrons (`index.html`, `styles.css`, `app.js`):**
   - Add left (`◀`) and right (`▶`) navigation buttons with `scrollDateRibbon(delta)`.
   - Add horizontal wheel event handler (`e.deltaY` translated to `scrollLeft`).
   - Add native calendar picker `<input type="date">` for direct date selection.
4. **Eliminate Hanging "Loading dates...":**
   - Automatically hydrate `#history-active-date-lbl` upon render with selected date and dispensed quantity.
   - Reset `appState.selectedHistoryDate` on feeder switch so dates re-anchor cleanly.

---

## CR-029 / STORY-031: Sliding Daily Feed Dispensed Bar Chart & Boundary Encapsulation

### 1. Problem Description
User reported that the "Daily Feed Dispensed" bar chart was not aligned or sitting properly inside boundaries:
1. When multiple days of historical records (e.g. 8 to 13 days) were loaded, `#history-chart-container` squeezed all columns using `flex: 1` into a non-scrollable flex row without `min-width` or horizontal slide.
2. Value labels (`15.0`) and weekday/date labels (`Mon 11/09`) collided, overlapped, and caused visual spillage across card boundaries.
3. For single-day devices (e.g. Feeder 04), the single bar stretched unnaturally across the entire card width.
4. The user requested: "daily feed dispensed is is not aligned or sit inside boundaries keep it inside the boundaries and make it slide that would be clean".

### 2. Engineering Solution
1. **Container Encapsulation (`index.html` & `styles.css`):**
   - Wrap the chart container in `.barchart-slider-wrapper` with strict `max-width: 100%`, `overflow: hidden`, and relative positioning.
   - Enforce exact card boundary alignment inside `.card.chart-card`.
2. **Sliding Track Architecture (`styles.css` & `app.js`):**
   - Make `#history-chart-container` a horizontal sliding track (`overflow-x: auto`, `scroll-behavior: smooth`, `scrollbar-width: none`).
   - Fix each column to a comfortable `min-width: 60px; max-width: 68px; flex: 0 0 62px;` so text labels (`15.0 kg` and `Mon 11/09`) have generous breathing room and never collide.
   - Add Left (`◀`) and Right (`▶`) circular navigation buttons (`scrollBarChart(delta)`).
   - Add mouse-wheel horizontal scroll translation (`e.deltaY` to `scrollLeft`).
   - Add auto-scroll centering on the selected day's bar column.
   - When only 1 or 2 days are present, center them cleanly without stretching.


---

## CR-030 / STORY-032: Daily Feed Master Chart with Interactive Day Inspection Modal (Graph & Timeline Views)

### 1. Problem Description
User review identified that the Date Explorer ribbon was confusing, prone to calendar navigation failures, and suffered from date label/timezone inconsistencies. Furthermore, stacking four sequential cards (Header Stats, Date Explorer Ribbon, 15-Day Barchart, Hourly Distribution Chart, and 150-row Completed Events Log) on a single endless scrolling page produced severe cognitive overload and an unpolished user experience.
The user requested:
> *"and date explorer doesnt work. cant change date and rthe name is not correct. just have a history and show a graph of dates with total feed onm top when user clicks on any date open it up showing the timeline and feed graph for that day he can change the view to list or graph or how ever it is good and a small close button should close this pop up and go back. think like a ui designer and do not patch design and implement"*

### 2. Engineering Solution
1. **Master-Detail Architecture (`index.html`):**
   - Main History Screen is streamlined to an elegant high-level overview:
     - Feeder Trends & Analytics Header Card (4 summary stats).
     - Daily Feed Dispensed Bar Chart Card with total feed dispensed (e.g. `15.0 kg`) displayed directly on top of each bar.
     - Redundant inline Date Explorer ribbon, inline Hourly Chart, and inline 150-event log are removed from the main page scroll.
2. **Day Inspection Modal (`index.html`, `styles.css`, `app.js`):**
   - Clicking any bar on the Daily Feed Dispensed chart opens `#day-inspector-modal`.
   - **Header:** Full formatted date (`Monday, Nov 9, 2026` via timezone-safe date constructor), feeder name, pond, target kg, and a top-right close button (`✕`).
   - **KPI Strip:** Total Dispensed, Events Completed, Schedule Adherence, and Active Operating Window.
   - **Segmented Control:** Seamless toggle between:
     - **📊 Hourly Graph:** Hourly feeding bars (06:00 to 18:00) with peak hour insights.
     - **📋 Event Timeline:** Complete sequential pulse log (1 to 150) with timestamps and cumulative grams.
   - **Footer:** Date stepping (`← Previous Day` / `Next Day →`) and a `Done` close button.
   - Modal closes cleanly via close button, backdrop tap, or `Escape` key.
