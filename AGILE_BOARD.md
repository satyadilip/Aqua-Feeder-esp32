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
| | | | **STORY-011** (Official v1.0 Baseline & Version Telemetry) `803a16d` |
| | | | **STORY-012** (Delta-Patch FUOTA Architecture Specification) `CLOSED` |
| | | | **STORY-013** (AquaDelta Engine: 50–85KB Micro-Patch & In-PSRAM Reconstructor) `CLOSED` |
| | | | **STORY-014** (Daylight Solar Class C & Zero-Uplink Sub-Second Downlink RX) `CLOSED` |
| | | | **STORY-015** (Fluid Multi-Field Settings Editing & Runtime Deductive Feed Schedule Math) `CLOSED` |
| | | | **STORY-016** (Zero Stale Data Flash on Page Refresh via Pre-Hydration & Storage Persistence) `CLOSED` |
| | | | **STORY-017** (Cloud Architecture Hardening & Latent Defect Elimination) `CLOSED` |
| | | | **STORY-018** (Eradicate Zero-Interval Re-Trigger & Concluded Day Auto-Start Loop) `CLOSED` |

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
- **Closed Commit:** [`803a16d`](https://github.com/satyadilip/Aqua-Feeder-esp32/commit/803a16d)
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
- **Status:** `CLOSED`
- **Assigned To:** RF Systems & Power Optimization Architect
- **As a:** Firmware & Field Operations Lead
- **I want:** An architectural design to perform firmware updates strictly over LoRaWAN and optimize receiver duty cycling during daylight
- **So that:** Operators can control feeders without 5-minute latency while conserving battery power overnight.
- **Key Architecture Decisions:**
  1. **Pure LoRa FUOTA:** Delta binary patching (`bsdiff` / `tinf`) to shrink 1.2 MB ESP32 binary down to 50–85 KB; TS005 / TS003 Fountain block reconstruction; Dual-partition A/B flash rollback with cryptographic SHA-256 verification.
  2. **Daylight RX / Night Standby:** Continuous Class C listen during 06:00–18:00 IST powered by 12V solar panel (virtually zero battery drain); automatic fall-back to Class A with 15–30 min heartbeat during night hours (18:00–06:00).

---

### STORY-013: AquaDelta Differential Patch Engine & In-PSRAM On-Device Reconstructor
- **Status:** `CLOSED`
- **Assigned To:** Embedded Systems & Compiler Engineer
- **As a:** Farm Network Engineer
- **I want:** To generate and flash 50–85 KB differential `.adelta` patch files instead of full 1.2 MB binaries
- **So that:** Firmware updates can be transmitted in minutes over low-bandwidth LoRaWAN or in seconds over the local AP web server.
- **Detailed Requirements & Implementation:**
  1. **Delta Generator (`tools/delta_generator.py`):**
     - Suffix-sorted differential streaming engine comparing baseline binary (`v4.0.0` / `v1.0`) against target.
     - RFC 1950 zlib compression (level 9) of `ctrl`, `diff`, and `extra` streams with 80-byte `AquaDeltaHeader`.
     - Target SHA-256 and CRC32 cryptographic hash calculation embedded in header.
     - **Verification Result:** Produced 83.06 KB `.adelta` from 1,211,760 B binary (93.0% bandwidth reduction) with 100% bit-for-bit target verification passed.
  2. **Embedded Decompression Engine (`tinf`):**
     - Integrated zero-allocation `tinf_zlib_uncompress()` within firmware without external dependencies.
  3. **On-Device Delta OTA Engine (`AquaFeeder/delta_ota.cpp`):**
     - Utilizes ESP32-S3 8MB Octal PSRAM (`safe_alloc`) to stage decompressor buffers and patch streams without flash wear.
     - Reads baseline active partition (`ota_0`) directly from flash via `esp_partition_read()`.
     - Reconstructs target binary in memory with byte-for-byte delta arithmetic.
     - Validates SHA-256 integrity via ESP32 hardware/mbedTLS engine.
     - Writes target partition via `esp_ota_begin()`, `esp_ota_write()`, and activates next boot partition via `esp_ota_set_boot_partition()`.
  4. **Local SoftAP Flasher (`/api/ota/delta` & `tools/flash_delta_wifi.py`):**
     - High-speed HTTP POST streaming endpoint on feeder AP (`192.168.4.1`) permitting 83 KB patch upload in <2 seconds.

---

### STORY-014: Daylight Solar Class C Continuous Listen & Battery Cadence Enforcement
- **Status:** `CLOSED`
- **Assigned To:** LoRaWAN Protocol & Power Architect
- **As a:** Farm Supervisor
- **I want:** The feeder to operate in LoRaWAN Class C during daylight hours to execute downlinks in under 1 second without waiting for uplinks, and conserve battery at night
- **So that:** I can instantly start, stop, or pause feeding from the cloud without battery exhaustion.
- **Detailed Requirements & Implementation:**
  1. **Dynamic Class C Switching (`lora_manager.cpp`):**
     - FreeRTOS Core 0 scheduler queries DS3231 RTC every 10 seconds.
     - Between 06:00 and 18:00 IST (solar daylight), switches radio to `RADIOLIB_LORAWAN_CLASS_C` (continuous RX).
     - Power consumption (~14 mW) is completely offset by the 12V 20W/50W pond solar panel.
     - At 18:00 IST (sunset), drops to `RADIOLIB_LORAWAN_CLASS_A` allowing radio deep sleep.
  2. **Sub-Second Downlink Polling (`lora_manager.cpp`):**
     - In Class C mode, `LoRaManager::loop()` polls `_node->getDownlinkClassC()` every 100 ms.
     - Downlinks execute immediately without requiring any precursory uplink from the feeder.
  3. **Standby Battery Cadence Enforced (`cloud_manager.cpp`):**
     - Outside feeding events, clamped minimum heartbeat interval to $\ge 300\text{s}$ (5 minutes) to eliminate continuous 5-second uplink battery drain.

---

### STORY-015: Fluid Multi-Field Settings Editing & Runtime Deductive Feed Schedule Math
- **Status:** `CLOSED`
- **Assigned To:** Full Stack Systems Team (Cloud, Web Dashboard, Firmware)
- **As a:** Farm Supervisor
- **I want:** The web dashboard settings page to allow fluid, uninterrupted editing of multiple parameters without inputs jumping back before saving, and for runtime changes to deduct already dispensed feed from the new target
- **So that:** If 8 pulses ran (dispensing 2 kg) and I change daily target from 20 kg to 25 kg, the schedule calculates remaining events for the remaining 23 kg and sets total events to $8 + \text{remaining}$, without clobbering my edits.
- **Detailed Requirements & Implementation:**
  1. **Decoupled Background Polling from Settings Inputs (`web_dashboard/app.js`):**
     - Removed `populateParamEditorUI()` from `loadSelectedDeviceToUI()` so background 5-second telemetry polling never resets input fields.
     - Added `isEditingSettings` state flag and focus guards to prevent asynchronous remote settings fetches from clobbering active user typing.
     - Added `'input'` and `'change'` real-time listeners across all numerical and time inputs (`input-qty`, `input-fpe`, `input-start-hour`, etc.) ensuring sliders and calculations sync fluidly on every keystroke.
     - In `saveSettingsToFeeder()`, read values directly from the DOM elements to guarantee all simultaneous multi-field edits are captured atomically.
  2. **Runtime Deductive Math in Cloud API (`api_lambda.py`):**
     - When `POST /api/settings/{deviceId}` is called mid-day, checks `CurrentEvent` ($E_{done}$) and `DispensedFeed_kg` ($Q_{disp}$).
     - Calculates remaining feed: $Q_{rem} = \max(0, Q_{target} - Q_{disp})$.
     - Calculates remaining events: $E_{rem} = \lceil (Q_{rem} \times 1000) / \text{FPE} \rceil$.
     - Computes updated total events: $E_{total} = E_{done} + E_{rem}$.
     - Recalculates `IntervalMin` for $E_{rem}$ evenly across remaining daylight seconds until `EndHour:EndMinute`.
  3. **Runtime Deductive Math in Firmware (`AquaFeeder/feed_engine.cpp` & `AquaFeeder.ino`):**
     - `FeedEngine::calcSchedule()` checks if `_status->currentEvent > 0 && _status->dispensedQuantity_g > 0` on the active operational day and deducts `dispensedQuantity_g` from the target quantity, computing $E_{rem} = \lceil Q_{rem} / \text{FPE} \rceil$ and $E_{total} = E_{done} + E_{rem}$.
     - Corrected `eventsDuration_ms` in `calcSchedule()` to use $E_{rem} \times \text{singleEvent\_ms}$ against remaining daylight window, eliminating the prior distortion where $E_{total}$ was compared against remaining time.
     - `FeedEngine::recalcDynamic()` enables exact dynamic schedule adjustment when `sysStatus.dispensedQuantity_g > 0` even while paused or between feeding cycles.
  4. **Live Verification & Simulation:**
     - Headless Selenium test verified zero input jump-back after an 8-second wait (exceeding the 5-second polling cycle).
     - Verified Cloud API returns `totalEvents: 123` ($8 \text{ done} + 115 \text{ rem}$) for $25\text{ kg target} - 2\text{ kg dispensed}$ at $200\text{g FPE}$.
     - Native C++ simulation harness (`scratch/test_firmware_math.cpp`) validated all 7 firmware operational scenarios:
       * Initial schedule (80 events, 20 kg @ 250g FPE).
       * User scenario mid-day update (8 events completed, 2 kg dispensed, updated to 25 kg @ 200g FPE -> both `recalcDynamic` and `calcSchedule` produced exactly 123 total events and 240,434 ms gap interval).
       * Runtime reduction below dispensed quantity (clean `FEED_FINISHED` termination without underflow).
       * Runtime reduction above dispensed quantity ($8 + 5 = 13$ events).
       * FPE change only ($8 + 46 = 54$ events).
       * Autonomous midnight rollover (clean reset to 0 events, 0 g, and fresh 50-event schedule).
       * Operational safety boundaries ("Time Too Short" error).
     - Compiled production binaries: `AquaFeeder.bin`, `AquaFeeder_v1.0.bin` (1,212,048 bytes), `AquaFeeder_merged_v1.0.bin`, and regenerated `AquaFeeder_v1.0.adelta` (87,268 bytes, 92.8% bandwidth savings, bit-for-bit verified).


---

### STORY-016: Zero Stale Data Flash on Page Refresh (Instant Pre-Hydration & Storage Persistence)
- **Status:** `CLOSED`
- **Assigned To:** Web Dashboard & Cloud Frontend Engineering
- **As a:** Commercial Shrimp Farmer / Supervisor
- **I want:** The status screen to never briefly flash stale placeholder data (such as dummy Feeder 01, 235 pulses, 23.50 kg) when I refresh or navigate to the page
- **So that:** The dashboard displays my active feeder's true status seamlessly from frame 1 without confusing or jarring UI jumps.
- **Root Cause Analysis:**
  1. `web_dashboard/index.html` contained hardcoded static placeholder numbers (`aquaCON Feeder 01`, `COMPLETED`, `235 / 235`, `23.50 kg`) that rendered immediately upon HTML parsing before JavaScript executed.
  2. `syncDevicesFromCloud()` fetched live telemetry from DynamoDB into memory every 5 seconds but never persisted the updated devices array to `localStorage`. As a result, page reloads fell back to un-updated default storage values before the asynchronous AWS API call returned.
- **Detailed Implementation:**
  1. **Clean Neutral HTML Placeholders (`web_dashboard/index.html`):**
     - Replaced all fake numbers with neutral, non-misleading placeholders (`--`, `/ -- Events Today`, `-- kg`, `STANDBY`).
  2. **Synchronous In-DOM Pre-Hydration (`web_dashboard/index.html`):**
     - Implemented an inline script directly following the hero card that reads `localStorage.getItem('aquacon_devices')` synchronously during DOM tree construction.
     - Pre-seeds the active device's real name, status badge, dispensed kg, daily target, and pulse count on the very first render frame prior to external script loads.
  3. **Cloud Telemetry Storage Persistence (`web_dashboard/app.js` & `web_dashboard_v2/app.js`):**
     - Updated `syncDevicesFromCloud()` and `fetchLiveTelemetry()` to atomically persist live device telemetry to `localStorage` on every poll cycle.
     - Positioned active feeder Feeder 03 (`e072a1fffef64134`) in Pond P-02 as the primary default device.
  4. **Live Verification & Proof:**
     - Automated Selenium headless test on live AWS S3 production site (`verify_live_s3_refresh.py`) verified 100ms post-refresh state: Feeder 03 rendered immediately with 0.00 kg dispensed, 20.0 kg target, 0/94 pulses, and STANDBY badge.
     - Confirmed zero occurrences of dummy numbers `235`, `23.50`, or `Feeder 01` throughout page load lifecycle.

---

### STORY-017: Cloud Architecture Hardening & Latent Defect Elimination
- **Status:** `CLOSED`
- **Closed Commit:** `HEAD`
- **As an:** Aquaculture System Architect & Site Reliability Engineer
- **I want:** All latent multi-feeder, downlink mode, tray check, timezone, and safety trip bugs eradicated from the cloud Lambdas and UI
- **So that:** The cloud platform exhibits 100% operational fidelity across all feeder nodes, global clients, and telemetry pipelines.
- **Architectural Fixes Implemented:**
  1. **Dynamic Multi-Device Expansion:** Removed the hardcoded 3-feeder whitelist (`e072a1fffef6249c`, `e072a1fffef5ba08`, `e072a1fffef64134`) from `api_lambda.py`. All 7 registered devices in DynamoDB (including Feeder 04, Feeder 05, and future nodes) are dynamically discovered and returned with custom names and pond associations.
  2. **Pond Switching Fatal Crash Elimination:** Fixed `ReferenceError: dev is not defined` in `switchActivePond()` (`web_dashboard/app.js` line 591) by calling `populateParamEditorUI()` parameterless, allowing fluid pond transitions with 0 console errors.
  3. **Daylight Solar Class C Sub-Second Downlinks:** In `send_lora_downlink()` (`api_lambda.py`), dynamically set `TransmitMode=1` during operational daylight hours (06:00 to 18:00 IST) to immediately transmit downlinks over gateways without waiting for Class A uplinks.
  4. **Tray Inspection Key Reconciliation & Battery Telemetry:** In `lambda_function.py`, logged real `Voltage_mV`, `Battery_V`, and `FeedDispensed_g` to `AquaFeeder_TrayChecks`. Updated `app.js` to inspect both `DispensedKg` and `FeedDispensed_g`, displaying genuine dispensed weights and battery levels.
  5. **Deterministic History Integrity & Math.ceil:** Eliminated synthetic random offsets (`offsets = [0.2, -0.4, 0.5, ...]`) in `web_dashboard/app.js`. In `recalculateSchedule()`, replaced `Math.floor` with `Math.ceil((qty * 1000.0) / fpe)` matching firmware precision.
  6. **Absolute Timezone Invariance (Asia/Kolkata):** Added `{ timeZone: 'Asia/Kolkata', hour12: true }` across all UI date, time, clock, and event log formatters so international coworkers and remote farm managers see identical farm-local times.
  7. **Motor Overcurrent / Jam Safety Trip Decoding:** Decoded Bit 1 (`statusFlags & 0x02`) across `api_lambda.py`, `lambda_function.py`, and `web_dashboard/app.js` as `MOTOR JAM / OVERCURRENT` with alert badges (`b-alert`).
- **Production Verification:**
  - Full Selenium headless test passed against live production AWS S3 bucket (`lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f.s3-website-us-east-1.amazonaws.com`).
  - 0 console errors during pond switching, tray check hydration, history rendering, and schedule calculation.

---

### STORY-018: Eradicate Zero-Interval Re-Trigger & Concluded Day Auto-Start Loop
- **Status:** `CLOSED`
- **Closed Commit:** `HEAD`
- **As a:** Commercial Shrimp Farmer
- **I want:** The feeder to never re-trigger feeding on the same day after reaching total target events, and under zero circumstances ever execute a 0-second relay loop
- **So that:** Feed is never dumped rapidly due to race conditions between LCD menu transitions, mid-day schedule math, and auto-start timers.
- **Root Cause Analysis (5 Intersecting Faults):**
  1. **LCD Menu Destructive State Overwrite:** At Event 175 (completion), `_fcState` completed and set `sysStatus.state = FEED_FINISHED`. The LCD displayed `MenuState::FINISHED` for a 30s timeout (`finishedDisplayTimer`). When 30s elapsed, `currentMenu` reverted to `MenuState::MAIN_STATUS`. In `AquaFeeder.ino` line 1875, `switch (currentMenu)` had `default: sysStatus.state = SystemState::IDLE; break;`, erasing `FEED_FINISHED` and resetting state to `IDLE`.
  2. **Auto-Start Day-Guard Bypass:** `AquaFeeder.ino` line 2929 called `feedEng.shouldAutoStart(epoch)`. Because `_status->state` was now `IDLE`, the guard `_lastFedDay == currentDay && _status->state == FEED_FINISHED` failed to engage.
  3. **Mid-Day Schedule Math Fall-Through:** Because the time was 17:50 (before the 18:00 window cutoff), `calcSchedule()` evaluated `else if (currentMins >= startMins)`. Because `remainingEvents == 0`, `eventsDuration_ms = 0`, bypassing `eventsDuration_ms >= availableTime_ms` and producing `intervalMs = 0`, with `scheduleValid = true` and `nextFeedEpoch` in the past.
  4. **Unconditional startFeed Counter Wipe:** Line 2937 invoked `startFeed(epoch)`, which unconditionally zeroed `currentEvent = 0` and `dispensedQuantity_g = 0.0f` on the very same day.
  5. **Zero-Delay Machine-Gun Relay Loop:** In `FC_WAIT`, because `intervalMs == 0`, every cycle elapsed with 0 delay, firing Event 1..175 with zero gap.
- **5-Layer Defensive Interlocks Implemented:**
  1. **`calcSchedule()` Concluded Day Guard:** Added `isCompletedToday` guard (`dispensedQuantity_g >= qty_g || currentEvent >= totalEvents || state == FEED_FINISHED`). Once completed, immediately arms for tomorrow at 06:00 AM (`startEpochToday + 86400UL`), pre-calculates tomorrow's full interval, and clamps minimum interval to 5000 ms.
  2. **`shouldAutoStart()` Irrevocable Day Completion Invariant:** In `shouldAutoStart()`, checks `_lastFedDay == currentDay` against target grams and total events regardless of LCD state string. Rejects auto-start if `dispensedQuantity_g >= target_g` or `currentEvent >= totalEvents`. Also requires `intervalMs > 0` and `nextFeedEpoch > nowEpoch`.
  3. **Menu Switch State Preservation (`AquaFeeder.ino`):** Replaced `default: sysStatus.state = IDLE` with `if (sysStatus.state != SystemState::FEED_FINISHED && sysStatus.state != SystemState::FEED_PAUSED) { sysStatus.state = SystemState::IDLE; }`. Persistent operational states are completely immune to LCD menu navigation.
  4. **`startFeed()` Guard Interlock:** `startFeed()` verifies if already completed today; returns `false` and rejects re-arming if `currentEvent >= totalEvents` or `dispensedQuantity_g >= target_g`.
  5. **Zero-Interval Hardware Interlock (`FC_WAIT`):** Clamped `intervalMs` to minimum 5000 ms; `FC_WAIT` strictly enforces `nowMs - _fcTimer >= 5000UL` before any motor relay can re-energize.
- **Verification:**
  - Standalone simulation `scratch/test_crazy_loop_fix.cpp` compiled and executed with 0 errors, validating all 5 defensive layers.
  - Production ESP32-S3 firmware compiled with `arduino-cli`.
