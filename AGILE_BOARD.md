# AquaFeeder Agile Kanban & Traceability Board

**Project:** AquaFeeder Autonomous Aquaculture Feeding System  
**Hardware Platform:** ESP32-S3 (SX1262 LoRaWAN, DS3231 Precision RTC, INA219 Power Monitor, Dual 30A Relays)  
**Cloud Infrastructure:** AWS IoT Core Wireless, AWS Lambda, Amazon DynamoDB, Amazon S3  
**Target Device:** Feeder 03 (`e072a1fffef64134`) / Node 1–5  
**Board Status:** Active Sprint — Traceability & Quality Hardening  

---

## 1. Visual Kanban Board

| 📋 Backlog | 🚧 In Progress | 🧪 Verification / Review | ✅ Done (Closed with Commit) |
| :--- | :--- | :--- | :--- |
| *(All Sprint Items Completed)* | | | **STORY-001** (6 AM–6 PM Window) `f88e19f` |
| | | | **STORY-002** (Dynamic Mid-Day Recalc) `7868864` |
| | | | **STORY-003** (Daily Recurrence & Heartbeat Decouple) `ddfcaf1` |
| | | | **STORY-004** (Real Telemetry Timestamps in History) `2db9958` |
| | | | **STORY-005** (Bi-Directional Settings Sync) `bd0522e` |
| | | | **STORY-006** (Timezone Invariance & Cache-Bust) `bd0522e` |
| | | | **STORY-007** (Immutable History Grams) `1243591` |
| | | | **STORY-008** (15-Day Retention & Rollup) `1243591` |
| | | | **STORY-009** (Completed State vs Settings) `1243591` |
| | | | **STORY-010** (Midnight Rollover Projection) `1243591` |

---

## 2. Epics & User Stories Breakdown

---

### STORY-001: Strict Daylight Operational Window (06:00 to 18:00 IST)
- **Status:** `CLOSED`
- **Closed Commit:** [`f88e19f`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/f88e19f)
- **As a:** Commercial Shrimp Farmer
- **I want:** The feeder and cloud schedule to strictly operate between 06:00 AM and 06:00 PM IST
- **So that:** Feed is never dispensed in the dark when shrimp are inactive, dissolved oxygen drops, and water quality risks spike.
- **Acceptance Criteria:**
  1. Setting `startHour < 6` or `endHour > 18` or `endHour == 18 && endMinute > 0` returns validation error on both LCD and Cloud.
  2. Starting feed outside 06:00–18:00 arms the device into `ARMED` standby to auto-trigger at 06:00 AM.
  3. Schedule validator rejects `endTime <= startTime` and `totalCyclesDuration >= windowDuration`.

---

### STORY-002: Dynamic Mid-Day Feed Interval Recalculation
- **Status:** `CLOSED`
- **Closed Commit:** [`7868864`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/7868864)
- **As a:** Farm Supervisor
- **I want:** Mid-day manual start or parameter changes to dynamically recalculate remaining gap intervals
- **So that:** The remaining feed quantity is evenly distributed across the remaining daylight window until 18:00 IST.
- **Formula:**
  $$\text{gap\_sec} = \frac{(\text{end\_sec} - \text{now\_sec}) - (\text{remaining\_events} \times \text{event\_duration\_sec})}{\text{remaining\_events}}$$
- **Acceptance Criteria:**
  1. Starting feed at 13:03 recalculates pulses and interval evenly to 18:00.
  2. Cloud Lambda mirrors firmware schedule engine to the second.
  3. Telemetry reports live interval and next feed time synchronously.

---

### STORY-003: Autonomous Daily Recurring Feeding Schedule
- **Status:** `CLOSED`
- **Closed Commit:** [`ddfcaf1`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/ddfcaf1)
- **As a:** Farm Operator
- **I want:** Feeding to recur automatically every single morning without manual intervention
- **So that:** The farm runs autonomously every day without requiring daily cloud commands.
- **Acceptance Criteria:**
  1. Once configured, firmware automatically triggers at 06:00 AM daily.
  2. Heartbeats do not reset feed completion anchors.
  3. Historic logs for past days are not falsely displayed on subsequent idle days.

---

### STORY-004: Real Historical Telemetry Timestamps in History Tab
- **Status:** `CLOSED`
- **Closed Commit:** [`2db9958`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/2db9958)
- **As a:** Pond Supervisor
- **I want:** The History tab to display genuine timestamps logged in DynamoDB from hardware uplinks
- **So that:** I can audit the exact minute and second of every feed burst rather than synthetic 5-minute approximations.
- **Acceptance Criteria:**
  1. `/api/telemetry/{deviceId}` queries real records from `AquaFeeder_Telemetry`.
  2. History UI renders exact event timestamps (`03:06 PM`, `03:03 PM`, `03:00 PM`, etc.).
  3. Synthetic step calculations only serve as an offline fallback when no network telemetry is available.

---

### STORY-005: Bi-Directional Settings Synchronization
- **Status:** `CLOSED`
- **Closed Commit:** [`bd0522e`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/bd0522e)
- **As a:** Farmer and Cloud Operator
- **I want:** Settings changed on the board LCD to update the cloud, and settings changed on the cloud to update the board
- **So that:** Both endpoints remain in 100% lockstep regardless of where configuration takes place.
- **Acceptance Criteria:**
  1. Changing Qty, FPE, or Timings on LCD immediately transmits `SETTINGS_REPORT` (`0x22`, 13B).
  2. Saving settings in Dashboard queues LoRaWAN binary downlink `CMD_SET_SETTINGS` (`0xA0`) on Port 2.
  3. Firmware applies downlink settings, writes to NVS, and confirms via `SETTINGS_REPORT`.
  4. Web dashboard fetches `/api/settings/{deviceId}` on tab open and device switch to display active settings.

---

### STORY-006: Timezone Consistency & Client Browser Cache-Busting
- **Status:** `CLOSED`
- **Closed Commit:** [`bd0522e`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/bd0522e)
- **As a:** Remote Farm Auditor
- **I want:** All colleagues across any device or location to see identical, accurate IST times
- **So that:** Team members in different timezones or with cached browsers do not see 7:00 PM anomalies.
- **Acceptance Criteria:**
  1. HTML files load scripts and stylesheets with cache-busting queries (`?v=2.4`, `?v=6.1`).
  2. S3 deployment sets `Cache-Control: max-age=0, no-cache, no-store, must-revalidate`.
  3. Removed double 5.5-hour offset bug from fallback logic.
  4. All timestamps explicitly format with `{ timeZone: 'Asia/Kolkata' }`.

---

### STORY-007: Immutable Event Log Telemetry (Per-Event Frozen Grams & Settings)
- **Status:** `CLOSED`
- **Closed Commit:** [`1243591`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/1243591)
- **Assigned To:** Full Stack Team (Firmware, Cloud, UI)
- **As a:** Quality Assurance Auditor
- **I want:** The History tab to freeze and display the exact grams and target settings that were active when each specific event ran
- **So that:** Changing Feed Per Event (FPE) or Daily Target later in the day does NOT retroactively alter historical event records.
- **Detailed Requirements:**
  1. `AquaFeeder_Telemetry` must store `EventGrams` (grams dispensed in this specific burst) and `Target_kg` at the time of uplink.
  2. When `/api/telemetry/{deviceId}` responds, each telemetry record includes `EventGrams`, `FeedPerEvent_g`, and `Time`.
  3. The History UI in `web_dashboard` and `web_dashboard_v2` must render `ev.grams = item.EventGrams || item.FeedPerEvent_g`, completely independent of current device settings.
  4. Historical events remain permanent facts of what occurred at that timestamp.

---

### STORY-008: 15-Day Granular Telemetry Retention & Permanent Daily Consolidation
- **Status:** `CLOSED`
- **Closed Commit:** [`1243591`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/1243591)
- **Assigned To:** Cloud & Data Engineer
- **As a:** Cloud Operations Manager
- **I want:** Granular event-by-event telemetry older than 15 days to be automatically cleared while consolidating daily totals into permanent records
- **So that:** Storage costs remain optimal while preserving long-term feeding metrics and daily trend charts.
- **Detailed Requirements:**
  1. Enable DynamoDB Time-To-Live (TTL) on `AquaFeeder_Telemetry` with attribute `TimeToLive`.
  2. Telemetry processor Lambda populates `TimeToLive = Timestamp + (15 * 86400)`.
  3. `AquaFeeder_DailyMetrics` stores consolidated summary per `(DeviceId, Date)`: `TotalEventsCompleted`, `DailyFeed_kg`, `Target_kg`, `Status`.
  4. `AquaFeeder_DailyMetrics` records have no TTL and remain permanent for 7-day, 30-day, and yearly analytics.

---

### STORY-009: Post-Feed Completion State Preservation Until Midnight (Prevent 0/100 Reset on Settings Change)
- **Status:** `CLOSED`
- **Closed Commit:** [`1243591`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/1243591)
- **Assigned To:** Cloud Backend & UI Lead
- **As a:** Farm Supervisor
- **I want:** The dashboard to continue displaying today's completed events and feed dispensed until 12:00 AM midnight IST even if I modify settings
- **So that:** Reviewing or preparing tomorrow's feed schedule does not erase today's completed feeding metrics from the main status screen.
- **Detailed Requirements:**
  1. If feeding has completed today (`CurrentEvent >= TotalEvents` or after `EndHour`), the device status remains `COMPLETED` until 23:59:59 IST.
  2. `AquaFeeder_Devices` tracks `TodayDate`, `TodayEventsCompleted`, and `TodayFeedDispensed_kg`.
  3. Editing settings via `POST /api/settings/{deviceId}` updates the *Next Schedule* (`AquaFeeder_Settings`), but preserves `TodayEventsCompleted` and `TodayFeedDispensed_kg` in `AquaFeeder_Devices`.
  4. Heartbeats received after feed completion do not overwrite today's completed numbers to 0.
  5. The UI Status card shows `COMPLETED` with today's completed pulse ratio (e.g. `135 / 135` or `82 / 82`) and `Tomorrow morning` for next feed.

---

### STORY-010: Midnight Rollover & Pre-Schedule Next Day Projection (00:00 to 06:00 IST)
- **Status:** `CLOSED`
- **Closed Commit:** [`1243591`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/1243591)
- **Assigned To:** Cloud Backend & UI Lead
- **As a:** Morning Operator
- **I want:** The dashboard to transition at midnight IST to show the upcoming day's projected schedule (`0 / TargetEvents`) in `STANDBY`
- **So that:** Before the morning feeding begins, the operator clearly sees the day's upcoming target and start time.
- **Detailed Requirements:**
  1. At 00:00:00 IST (midnight), the operational date flips to Day $T+1$.
  2. From 00:00:00 IST until `StartHour:StartMinute` (06:00 AM), `CurrentEvent` shows `0` and `TotalEvents` shows the new day's planned target events.
  3. Status displays `STANDBY` with `Starts today at 06:00 AM`.
  4. At 06:00:00 AM, the first pulse triggers transition to `FEEDING`.

---

### STORY-011: Official Release v1.0 Baseline & Cloud Firmware Version Telemetry
- **Status:** `CLOSED`
- **Closed Commit:** `PENDING_COMMIT`
- **Assigned To:** Embedded Firmware & Cloud Architect
- **As a:** Farm Hardware Operator & Cloud Manager
- **I want:** The firmware release version to be standardized to `v1.0` (with branding "AquaFeeder Firmware"), and reported dynamically to the cloud over LoRaWAN telemetry
- **So that:** All devices in the field report their active software version without incurring extra airtime overhead, and operators are alerted when new versions are available.
- **Detailed Requirements:**
  1. Standardize firmware name to `"AquaFeeder Firmware"` across LCD, Web AP, and Serial logs.
  2. Bump production shipping version to `v1.0` (`0x10`).
  3. Pack `(Major << 4) | Minor` into byte 14 of the standard 15-byte `LoRaUplinkPayload` (`reserved` field), adding 0 extra bytes to LoRa transmission.
  4. Telemetry processor Lambda parses byte 14 into `FirmwareVersion` (`v1.0`) and `FirmwareName` (`AquaFeeder Firmware`) and stores into `AquaFeeder_Devices`.
  5. Cloud API serves `FirmwareVersion` in `GET /api/devices`.

---

### STORY-012: Pure LoRaWAN FUOTA & Daylight Receiver Power Optimization Architecture
- **Status:** `IN REVIEW / DESIGN SPEC`
- **Assigned To:** RF Systems & Power Optimization Architect
- **As a:** Firmware & Field Operations Lead
- **I want:** An architectural design to perform firmware updates strictly over LoRaWAN and optimize receiver duty cycling during daylight
- **So that:** Operators can control feeders without 5-minute latency while conserving battery power overnight.
- **Key Architecture Decisions:**
  1. **Pure LoRa FUOTA:** Delta binary patching (`bsdiff` / Detools) to shrink 1.15MB ESP32 binary to ~60KB; LoRa Alliance TS005 Multicast distribution; TS003 Fountain / Reed-Solomon forward error correction; Dual-partition A/B flash rollback.
  2. **Daylight RX / Night Standby:** Continuous Class C listen during 06:00–18:00 IST powered by 12V solar panel (virtually zero battery drain); automatic fall-back to Class A with 15–30 min heartbeat during night hours (18:00–06:00).
