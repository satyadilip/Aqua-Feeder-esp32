# aquaCON™ Smart Aquaculture Feeder — Complete Software Requirements Specification (SRS)
## In Compliance with ISO/IEC/IEEE 29148:2018 Standards

**Document Identifier:** AGY-SRS-AQUACON-2026-V2.0  
**Status:** Authoritative Baseline / Engineering Source of Truth  
**Architecture Scope:** Embedded Edge Firmware (ESP32-S3), LoRaWAN Cloud Microservices (AWS Lambda, DynamoDB, API Gateway), Progressive Web Application Dashboard (S3 + Vanilla JS)  
**Total Testable Requirements:** 215 Requirements (`REQ-001` through `REQ-215`)

---

## 1. Document Overview & Architectural Context

### 1.1 Purpose
This document provides the exhaustive, formal Software Requirements Specification (SRS) for the **aquaCON™ Automated Smart Commercial Aquaculture Feeder**. It governs all hardware-software boundaries, real-time control loops, display real estate budgets, state transitions, cloud telemetry models, and UI presentations. It serves as the single immutable verification baseline for firmware developers, cloud architects, and QA engineers.

### 1.2 The Architectural "Back-and-Forth" Root Cause Analysis
Previous feature regressions were caused by architectural mismatches across decoupled system boundaries:
1. **Telemetry Bitmask Conflict:** Firmware designated `Bit 5` (`0x20`) as `SD Card Fault / Missing`. The cloud ingestion Lambda misinterpreted `0x20` as `FEED_ACTIVE`, causing units lacking SD cards to report active dispensing 24 hours a day.
2. **Temporal Window Conflict:** Firmware enforced an operational daylight window (`06:00` to `18:00 IST`), but cloud lambdas lacked this guard, allowing midnight uplinks to calculate dynamic intervals into the middle of the night (`12:53 AM`).
3. **Data Boundary Leakage:** Day rollover at midnight failed to strictly constrain telemetry queries to `Timestamp >= today_start_epoch`, pulling yesterday's event counts and weight into today's gauge.
4. **Display Overrun:** LCD buffers without rigorous 20-character bounds wrapped across lines or corrupted adjacent rows.

This document eliminates ambiguity by providing exact strings, byte layouts, timing bounds, and pass/fail criteria for every feature.

### 1.3 Requirement Nomenclature & Traceability Matrix
Every requirement follows the formal IEEE 29148 format:
- **Identifier:** `REQ-[CATEGORY]-[ID]`
- **Statement:** Prescriptive requirement using **SHALL** (mandatory) or **SHALL NOT** (prohibited).
- **Verification Method:**
  - **[T] Test:** Empirical execution against test stimuli.
  - **[I] Inspection:** Code review, schematic inspection, or visual text audit.
  - **[A] Analysis:** Mathematical calculation or timing analysis.
  - **[D] Demonstration:** Real-time functional verification on hardware.

---

## 2. Hardware Architecture & Physical Constraints

### 2.1 Mechanical & Electrical Interfaces
```
+-----------------------------------------------------------------------------------+
|                                  ESP32-S3 MCU                                     |
|                      (16MB Flash, 8MB PSRAM, 240MHz Xtensa)                       |
+--------+--------+--------+--------+--------+--------+--------+--------+-----------+
         |        |        |        |        |        |        |        |
       GPIO4    GPIO5    GPIO6    GPIO7   GPIO10   GPIO11   GPIO16   GPIO42   I2C (8,9)
         |        |        |        |        |        |        |        |        |
       [UP]    [DOWN]    [SEL]    [BACK]  Relay 1  Relay 2  PC817    Piezo   +---+---+---+
      Button   Button   Button    Button  Spreader Loader    Opto    Hooter  |   |   |
                                          Disc     Auger    Sensor   85dB   DS  INA LCD
                                          Motor    Motor    (Feed)          32  219 20x4
                                          (12V)    (12V)                    31
```

### 2.2 Character Display Budget: 20x4 LCD (JHD629-204A / PCF8574)
- **Grid Layout:** Exactly 20 columns $\times$ 4 rows = 80 characters maximum per screen.
- **Physical Memory Boundary:** Exactly 20 characters per row. Buffer size: `char buf[21];` (20 characters + null terminator `\0`).
- **Custom CGRAM Character Slots (0-7):**
  - Custom Char `0`: 1/5 Sub-pixel Bar `[|    ]` (0x10 fill)
  - Custom Char `1`: 2/5 Sub-pixel Bar `[||   ]` (0x18 fill)
  - Custom Char `2`: 3/5 Sub-pixel Bar `[|||  ]` (0x1C fill)
  - Custom Char `3`: 4/5 Sub-pixel Bar `[|||| ]` (0x1E fill)
  - Custom Char `4`: 5/5 Solid Block `[|||||]` (0x1F fill)

---

## 3. Detailed Requirements Specification (215 Requirements)

### Category 1: Power-On, Bootup & Hardware Bring-Up (REQ-001 to REQ-018)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-001** | Power-On Relay Isolation | The firmware SHALL initialize GPIO 10 (Spreader Relay) and GPIO 11 (Loader Relay) to LOW (de-energized) within $\le 50\text{ ms}$ of ROM boot to prevent inadvertent motor spin. | [T] |
| **REQ-002** | Power-On Hooter Isolation | The firmware SHALL initialize GPIO 42 (Piezo Alarm) to LOW within $\le 50\text{ ms}$ of ROM boot. | [T] |
| **REQ-003** | Boot Visual Indicator | The system SHALL illuminate the onboard RGB LED to solid WHITE (`RGB: 64, 64, 64`) and turn ON the STAT1 Red LED upon boot. | [D] |
| **REQ-004** | I2C Bus Bring-up | The firmware SHALL initialize the I2C bus on GPIO 8 (SDA) and GPIO 9 (SCL) at 100 kHz with a 50 ms bus timeout. | [T] |
| **REQ-005** | LCD Detection & Fallback | The firmware SHALL poll I2C address `0x27` (primary) and `0x3F` (alternate). If neither acknowledges, system SHALL log `[LCD] Not Found` and proceed in Headless Web/LoRa mode without freezing. | [T] |
| **REQ-006** | Custom CGRAM Registration | Upon successful LCD initialization, the firmware SHALL write the 5 sub-pixel progress bar bit patterns into CGRAM indices `0` through `4`. | [T] |
| **REQ-007** | Splash Screen Line 0 | The LCD SHALL display `====================` (exactly 20 `=` characters) on Row 0 during bootup. | [I] |
| **REQ-008** | Splash Screen Line 1 | The LCD SHALL display `    aquaCON(TM)     ` (exactly 4 leading spaces, `aquaCON(TM)`, 5 trailing spaces) on Row 1 during bootup. | [I] |
| **REQ-009** | Splash Screen Line 2 | The LCD SHALL display ` Smart Aqua Feeder  ` (exactly 1 leading space, `Smart Aqua Feeder`, 2 trailing spaces) on Row 2 during bootup. | [I] |
| **REQ-010** | Splash Screen Line 3 | The LCD SHALL display `  Firmware v1.0.0   ` (exactly 2 leading spaces, `Firmware v1.0.0`, 3 trailing spaces) on Row 3 during bootup. | [I] |
| **REQ-011** | Splash Screen Duration | The splash screen SHALL be displayed for a deterministic duration of $2200\text{ ms} \pm 100\text{ ms}$. | [T] |
| **REQ-012** | Keypad Locking on Splash | The system SHALL ignore all pushbutton events (UP, DOWN, SELECT, BACK) while the splash screen is displayed. | [T] |
| **REQ-013** | Hardware RTC Initialization | The system SHALL query the DS3231 RTC. If valid time is returned, `sysStatus.rtcOK` SHALL be set to `true`. | [T] |
| **REQ-014** | Software RTC Fallback | If the DS3231 fails to respond, the system SHALL initialize Software RTC seeded from compilation timestamp (`__DATE__`, `__TIME__`) and set `sysStatus.rtcOK = false`. | [T] |
| **REQ-015** | INA219 Bring-up | The system SHALL initialize the INA219 power monitor on I2C address `0x40`. If missing, system SHALL log error and record `0.0V / 0mA` without aborting boot. | [T] |
| **REQ-016** | NVS Configuration Load | The firmware SHALL load persistent settings (`feedQuantity`, `feedPerEvent`, `startHour`, `startMinute`, `endHour`, `endMinute`, `dischargeRate`) from NVS partition `aquacon`. | [T] |
| **REQ-017** | First Boot Provisioning | If NVS contains no configuration (`isFirstBoot == true`), the system SHALL generate a unique Device ID `AF_[MAC_HIGH][MAC_LOW]`, apply factory defaults, and commit to NVS. | [T] |
| **REQ-018** | Autonomous Home Screen Entry | At $T = 2200\text{ ms}$ post-boot, the system SHALL clear the LCD and autonomously transition to `MenuState::MAIN_STATUS` (Home Screen). | [D] |

---

### Category 2: 20x4 LCD Physical Screen Layouts & Text Bounds (REQ-019 to REQ-040)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-019** | Strict 20-Character Line Budget | No LCD rendering routine SHALL output more than 20 characters to any single row. All string buffers SHALL be allocated as `char buf[21]`. | [I] |
| **REQ-020** | Home Row 0 Clock Format | Row 0 of the Home Screen SHALL display `AquaFeeder  HH:MM:SS` (10 chars title, 2 spaces, 8 chars formatted time) when RTC is valid. | [I] |
| **REQ-021** | Home Row 0 No-Clock Fallback | Row 0 of the Home Screen SHALL display `AquaFeeder  NO-CLOCK` (10 chars title, 2 spaces, 8 chars warning) when RTC is invalid. | [I] |
| **REQ-022** | Home Row 1 State Prefix | Row 1 of the Home Screen SHALL strictly begin with the 7-character prefix `State: `. | [I] |
| **REQ-023** | Home Row 1 Standby Text | When machine is in standby, Row 1 SHALL display `State: STANDBY     ` (7 chars prefix + 13 chars padded text). | [I] |
| **REQ-024** | Home Row 1 Scheduled Text | When machine is armed for today's schedule, Row 1 SHALL display `State: SCHEDULED   `. | [I] |
| **REQ-025** | Home Row 1 Dispensing Text | During motor feed dispense, Row 1 SHALL display `State: DISPENSING  `. | [I] |
| **REQ-026** | Home Row 1 Warmup Text | During motor pre-spin warmup, Row 1 SHALL display `State: WARM-UP     `. | [I] |
| **REQ-027** | Home Row 1 Post-Clear Text | During chute clear spin, Row 1 SHALL display `State: POST-CLEAR  `. | [I] |
| **REQ-028** | Home Row 1 Gap Delay Text | During wait interval between pulses, Row 1 SHALL display `State: GAP DELAY   `. | [I] |
| **REQ-029** | Home Row 1 Feed Paused Text | When feed is paused, Row 1 SHALL display `State: FEED PAUSED `. | [I] |
| **REQ-030** | Home Row 1 Completed Text | When today's target is 100% completed, Row 1 SHALL display `State: COMPLETED   `. | [I] |
| **REQ-031** | Home Row 1 Motor Trip Text | When INA219 trips overcurrent, Row 1 SHALL display `State: MOTOR TRIP  `. | [I] |
| **REQ-032** | Home Row 2 Idle Prompt | When machine is in standby or scheduled, Row 2 SHALL display `Press [SEL] for Menu` (exactly 20 characters). | [I] |
| **REQ-033** | Home Row 2 Gap Countdown | During `FC_WAIT`, Row 2 SHALL display `E:XXX/YYY W:ZZZZs   ` where XXX is current event, YYY is total events, and ZZZZ is remaining wait seconds. | [I] |
| **REQ-034** | Home Row 2 Running Text | During active motor spinning, Row 2 SHALL display `E:XXX/YYY RUN       `. | [I] |
| **REQ-035** | Home Row 3 Connectivity | Row 3 of the Home Screen SHALL display `LR:ss WF:ss GM:ss 12V` where `ss` represents 2-character connection codes (`OK`, `CN`, `DC`, `--`, `ER`). | [I] |
| **REQ-036** | Progress Bar Enclosure | The LCD progress bar SHALL render an opening bracket `[` at Column 0 and a closing bracket `]` at Column 19 on Row 2, containing exactly 18 bar slots. | [I] |
| **REQ-037** | Sub-Pixel Progress Math | The progress bar SHALL scale 0.0% to 100.0% linearly across 90 discrete sub-pixel levels ($18 \text{ slots} \times 5 \text{ sub-pixels}$). | [A] |
| **REQ-038** | Paused Screen Line 0 | The LCD Paused screen SHALL display `=== FEED PAUSED === ` (exactly 20 characters) on Row 0. | [I] |
| **REQ-039** | Paused Screen Line 2 | The LCD Paused screen SHALL display `[SEL]: Resume       ` (exactly 20 characters) on Row 2. | [I] |
| **REQ-040** | Paused Screen Line 3 | The LCD Paused screen SHALL display `[BACK]: Cancel      ` (exactly 20 characters) on Row 3. | [I] |

---

### Category 3: Keypad Input, Debouncing & Navigation (REQ-041 to REQ-058)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-041** | Keypad Hardware Sampling | The firmware SHALL scan GPIO 4, 5, 6, and 7 every $20\text{ ms} \pm 2\text{ ms}$ via a non-blocking ticker task. | [T] |
| **REQ-042** | Keypad Noise Debounce | A button state change SHALL only be registered after maintaining a stable physical state for $\ge 20\text{ ms}$. | [T] |
| **REQ-043** | Rising Edge Event Generation | The firmware SHALL assert a single-cycle `risingEdge` flag when a button transitions from unpressed (HIGH) to pressed (LOW). | [T] |
| **REQ-044** | Long-Press Repeat Delay | When a navigation or edit button (UP or DOWN) is held continuously, repeat events SHALL trigger after an initial hold delay of $500\text{ ms}$. | [T] |
| **REQ-045** | Long-Press Repeat Rate | Subsequent repeated button events during continuous hold SHALL fire at a deterministic rate of $100\text{ ms}$ ($10\text{ Hz}$). | [T] |
| **REQ-046** | Home to Menu Navigation | Pressing `[SELECT]` (SW3) from the Home Screen SHALL instantly transition `currentMenu` to `MenuState::MENU_LIST` with `menuCursorIdx = 0`. | [D] |
| **REQ-047** | Menu Cursor Down | Pressing `[DOWN]` (SW2) in `MENU_LIST` SHALL increment `menuCursorIdx` by 1, wrapping from 10 to 0. | [D] |
| **REQ-048** | Menu Cursor Up | Pressing `[UP]` (SW1) in `MENU_LIST` SHALL decrement `menuCursorIdx` by 1, wrapping from 0 to 10. | [D] |
| **REQ-049** | Menu Item Selection | Pressing `[SELECT]` (SW3) in `MENU_LIST` SHALL open the corresponding submenu or execute the associated command. | [D] |
| **REQ-050** | Menu Escape to Home | Pressing `[BACK]` (SW4) in `MENU_LIST` SHALL immediately return `currentMenu` to `MenuState::MAIN_STATUS` without altering settings. | [D] |
| **REQ-051** | Menu Inactivity Timeout | If no button is pressed for $30.0\text{ seconds}$ while inside `MENU_LIST` or any edit screen, the system SHALL automatically return to `MAIN_STATUS`. | [T] |
| **REQ-052** | Edit Value Increment | In edit screens, pressing `[UP]` SHALL increment the edited parameter by its designated step size up to its maximum ceiling. | [D] |
| **REQ-053** | Edit Value Decrement | In edit screens, pressing `[DOWN]` SHALL decrement the edited parameter by its designated step size down to its minimum floor. | [D] |
| **REQ-054** | Edit Value Commit | In edit screens, pressing `[SELECT]` on the final field SHALL persist the parameter to NVS, recompute schedule math, and return to `MENU_LIST`. | [T] |
| **REQ-055** | Edit Cancel Discard | In edit screens, pressing `[BACK]` SHALL discard all modified temporary values and return to `MENU_LIST` with original NVS values intact. | [T] |
| **REQ-056** | Running Screen Keypad Interlock | While motors are physically energized (`FC_PRE`, `FC_DISP`, `FC_POST`), pressing `[SELECT]` SHALL immediately open `MENU_LIST` highlighting `Stop Feeding`. | [D] |
| **REQ-057** | Paused Resume Keypad Action | On the `FEED_PAUSED` screen, pressing `[SELECT]` SHALL invoke `feedEng.resumeFeed()` if proximity sensor reports cleared. | [D] |
| **REQ-058** | Paused Cancel Keypad Action | On the `FEED_PAUSED` screen, pressing `[BACK]` SHALL invoke `cbOnFeedStop()`, terminate feeding for the day, and return to `MAIN_STATUS`. | [D] |

---

### Category 4: Menu System Pagination & Submenus (REQ-059 to REQ-075)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-059** | 4-Row Windowed Pagination | The `drawMenuList()` function SHALL calculate `startIdx = (menuCursor / 4) * 4` and display items `startIdx` to `startIdx + 3` across Rows 0-3. | [I] |
| **REQ-060** | Active Item Cursor Tag | The active menu item designated by `menuCursorIdx` SHALL be prefixed with `> ` (Column 0: `>`, Column 1: space). | [I] |
| **REQ-061** | Inactive Item Cursor Tag | All non-active menu items SHALL be prefixed with `  ` (two spaces at Column 0 and 1). | [I] |
| **REQ-062** | Menu Item 0 Text | Item 0 in the menu registry SHALL display `Check Tray` (Manual 1-pulse feed burst). | [I] |
| **REQ-063** | Menu Item 1 Dynamic Text | Item 1 SHALL dynamically render as `Stop Feeding ` when `feedActive == true`, and `Start Feeding` when `feedActive == false`. | [D] |
| **REQ-064** | Menu Item 2 Text | Item 2 in the menu registry SHALL display `Feed Quantity`. | [I] |
| **REQ-065** | Menu Item 3 Text | Item 3 in the menu registry SHALL display `Feed Per Event`. | [I] |
| **REQ-066** | Menu Item 4 Text | Item 4 in the menu registry SHALL display `Start Time`. | [I] |
| **REQ-067** | Menu Item 5 Text | Item 5 in the menu registry SHALL display `End Time`. | [I] |
| **REQ-068** | Menu Item 6 Text | Item 6 in the menu registry SHALL display `Discharge Rate`. | [I] |
| **REQ-069** | Menu Item 7 Text | Item 7 in the menu registry SHALL display `Diagnostics`. | [I] |
| **REQ-070** | Menu Item 8 Text | Item 8 in the menu registry SHALL display `Set Real Clock`. | [I] |
| **REQ-071** | Menu Item 9 Text | Item 9 in the menu registry SHALL display `Network Info`. | [I] |
| **REQ-072** | Menu Item 10 Text | Item 10 in the menu registry SHALL display `Power Monitor`. | [I] |
| **REQ-073** | Empty Slot Blanking | When viewing the final page of menu items, unused LCD rows SHALL be overwritten with 20 space characters to clear stale artifacts. | [I] |
| **REQ-074** | Diagnostics Submenu Items | Selecting `Diagnostics` SHALL open a submenu containing: `Test Feed (30-120s)`, `Test Spreader (2s)`, `Test Loader (2s)`, `Test Hooter (1s)`, `Ping Gateway`, and `< Back`. | [D] |
| **REQ-075** | Diagnostics Manual Test Safety | Any manual motor diagnostic test SHALL automatically timeout and de-energize relays after a hard limit of $\le 5.0\text{ seconds}$. | [T] |

---

### Category 5: Settings, Limits & NVS Persistence (REQ-076 to REQ-095)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-076** | Feed Quantity Range | The Daily Feed Quantity setting SHALL be bounded between a minimum of $0.5\text{ kg}$ and a maximum of $120.0\text{ kg}$. | [T] |
| **REQ-077** | Feed Quantity Step Size | The Feed Quantity adjustment step size SHALL be exactly $0.5\text{ kg}$ per button event. | [T] |
| **REQ-078** | Feed Per Event Range | The Feed Per Event setting SHALL be bounded between a minimum of $50\text{ g}$ and a maximum of $1000\text{ g}$. | [T] |
| **REQ-079** | Feed Per Event Step Size | The Feed Per Event adjustment step size SHALL be exactly $50\text{ g}$ per button event. | [T] |
| **REQ-080** | Start Hour Range | The Schedule Start Hour setting SHALL be bounded between $06\text{ (6 AM)}$ and $17\text{ (5 PM)}$. | [T] |
| **REQ-081** | Start Minute Range | The Schedule Start Minute setting SHALL be bounded between $00$ and $59$ in increments of $1\text{ minute}$. | [T] |
| **REQ-082** | End Hour Range | The Schedule End Hour setting SHALL be bounded between $07\text{ (7 AM)}$ and $18\text{ (6 PM)}$. | [T] |
| **REQ-083** | End Minute Range | The Schedule End Minute setting SHALL be bounded between $00$ and $59$ in increments of $1\text{ minute}$. | [T] |
| **REQ-084** | Operational Daylight Enclosure | The firmware SHALL enforce that `startHour >= 6` and `(endHour < 18 or (endHour == 18 and endMinute == 0))`. | [T] |
| **REQ-085** | Chronological Ordering Rule | The firmware SHALL reject any configuration where $(\text{EndHour} \times 60 + \text{EndMin}) \le (\text{StartHour} \times 60 + \text{StartMin})$. | [T] |
| **REQ-086** | Discharge Rate Range | The Auger Discharge Rate calibration parameter SHALL be bounded between $20\text{ g/s}$ and $500\text{ g/s}$. Default: $100\text{ g/s}$. | [T] |
| **REQ-087** | Discharge Rate Step Size | The Discharge Rate adjustment step size SHALL be exactly $10\text{ g/s}$ per button event. | [T] |
| **REQ-088** | NVS Flash Wear Reduction | Configuration SHALL only be written to NVS when values have actually changed (`memcmp != 0`). | [T] |
| **REQ-089** | Atomic NVS Transaction | Configuration saves SHALL utilize Preferences API `putBytes()` with verification read-back to guarantee atomicity. | [T] |
| **REQ-090** | Total Events Deduction | The total events count SHALL be calculated as $\text{TotalEvents} = \lceil (\text{FeedQuantity} \times 1000) / \text{FeedPerEvent} \rceil$. | [A] |
| **REQ-091** | Overfill Window Prevention | If $\text{TotalEvents} \times t_{\text{event}} \ge (\text{EndMin} - \text{StartMin}) \times 60$, the system SHALL flag `Schedule Error: Exceeds Window` on LCD. | [T] |
| **REQ-092** | Settings Uplink Notification | Whenever local settings are saved via LCD, the system SHALL queue a `LoRaSettingsPayload` (MsgType `0x22`) uplink within $\le 2\text{ seconds}$. | [D] |
| **REQ-093** | Clock Setting Field 0 | In `EDIT_CLOCK`, Field 0 SHALL adjust Hours (`00` to `23`). Pressing SELECT moves active cursor to Field 1. | [D] |
| **REQ-094** | Clock Setting Field 1 | In `EDIT_CLOCK`, Field 1 SHALL adjust Minutes (`00` to `59`). Pressing SELECT commits time to DS3231 RTC. | [D] |
| **REQ-095** | Factory Reset Key Combo | Holding `[BACK]` and `[SELECT]` simultaneously for $> 10\text{ seconds}$ at boot SHALL erase NVS and restore factory defaults. | [T] |

---

### Category 6: Schedule Engine, Timing & Operational Window Constraints (REQ-096 to REQ-115)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-096** | Strict Night Window Motor Lockdown | From `18:00:00` to `06:00:00 IST`, the FeedEngine SHALL enforce `state = IDLE` and lock Relays 1 and 2 de-energized. | [T] |
| **REQ-097** | Unarmed First Boot Invariant | On initial power-on or new flash, the feeder SHALL NOT start automated feeding until explicitly started by operator (`hasBeenRun == false`). | [T] |
| **REQ-098** | Night Arming Behavior | If `START FEEDING` is commanded between `18:00` and `06:00`, the engine SHALL set `hasBeenRun = true`, arm for `06:00 AM`, and remain in `STANDBY`. | [T] |
| **REQ-099** | Single Event Duration Formula | The duration of one pulse SHALL be calculated as $t_{\text{event}} = 3.0\text{s (Pre)} + (\text{FeedPerEvent} / \text{DischargeRate}) + 3.0\text{s (Post)}$. | [A] |
| **REQ-100** | Full Window Duration Formula | Total daylight window seconds SHALL be calculated as $t_{\text{window}} = (\text{EndHour} \times 3600 + \text{EndMin} \times 60) - (\text{StartHour} \times 3600 + \text{StartMin} \times 60)$. | [A] |
| **REQ-101** | Base Gap Calculation | The nominal wait gap SHALL be calculated as $t_{\text{base\_gap}} = \max(5, \lfloor (t_{\text{window}} - (\text{TotalEvents} \times t_{\text{event}})) / \text{TotalEvents} \rfloor)$. | [A] |
| **REQ-102** | Remaining Events Deduction | In active runs, remaining events SHALL be calculated dynamically as $N_{\text{rem}} = \max(0, \text{TotalEvents} - \text{CurrentEvent})$. | [A] |
| **REQ-103** | Dynamic Gap Recalculation | When recalculated mid-day, the gap SHALL be $t_{\text{dyn\_gap}} = \max(5, \lfloor (t_{\text{rem\_window}} - (N_{\text{rem}} \times t_{\text{event}})) / N_{\text{rem}} \rfloor)$. | [A] |
| **REQ-104** | Dynamic Gap Ceiling | If remaining time exceeds schedule requirements, $t_{\text{dyn\_gap}}$ SHALL be capped such that no feed occurs past `EndHour:EndMinute`. | [T] |
| **REQ-105** | Minimum Inter-Pulse Gap | The system SHALL enforce an absolute minimum wait gap of $\ge 5\text{ seconds}$ between feed events to prevent motor thermal overload. | [T] |
| **REQ-106** | Day Rollover Autonomous Trigger | When $T_{\text{epoch}} / 86400 > \text{lastFedDay}$, the engine SHALL reset `currentEvent = 0`, `dispensedQuantity_g = 0.0`, and clear NVS run state. | [T] |
| **REQ-107** | Target Dispensed Weight Completion | When `dispensedQuantity_g >= FeedQuantity * 1000`, the engine SHALL set `state = FEED_FINISHED` and cease pulsing for the day. | [T] |
| **REQ-108** | Target Event Count Completion | When `currentEvent >= TotalEvents`, the engine SHALL set `state = FEED_FINISHED` and cease pulsing for the day. | [T] |
| **REQ-109** | End of Operational Hours Concession | When local time reaches `EndHour:EndMinute`, the engine SHALL transition to `FEED_FINISHED` regardless of uncompleted events. | [T] |
| **REQ-110** | Immediate First Pulse on Manual Start | When `START FEEDING` is triggered inside daylight hours (`06:00` to `18:00`), Event 1 SHALL fire within $\le 1.0\text{ second}$. | [D] |
| **REQ-111** | Next Feed Epoch Projection | During `FC_WAIT`, `nextFeedEpoch` SHALL equal $T_{\text{pulse\_end}} + t_{\text{gap}}$. | [A] |
| **REQ-112** | Telemetry Heartbeat in Gap Delay | During `FC_WAIT`, the system SHALL suppress rapid telemetry bursts and transmit periodic heartbeats at $60\text{s}$ intervals. | [T] |
| **REQ-113** | Time Drift Realignment | If the RTC time is adjusted mid-cycle by $> 60\text{ seconds}$, the engine SHALL immediately recalculate dynamic schedule math. | [T] |
| **REQ-114** | Completion Lockout on Same Day | Once `FEED_FINISHED` is reached on calendar day $D$, auto-start SHALL remain locked until calendar day $D+1$. | [T] |
| **REQ-115** | Check Tray Schedule Independence | Executing a manual `Check Tray` burst SHALL NOT increment `currentEvent` or alter the scheduled `nextFeedEpoch`. | [T] |

---

### Category 7: 3-Phase Dispensing Engine & Actuator Control (REQ-116 to REQ-130)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-116** | Phase 1 Spreader Pre-Warmup | Upon pulse trigger, the system SHALL assert GPIO 10 (Spreader Relay) HIGH for exactly $3.0\text{ seconds} \pm 50\text{ ms}$ while Loader remains LOW. | [T] |
| **REQ-117** | Phase 2 Loader Metering Engagement | At $T = 3.0\text{ seconds}$, the system SHALL assert GPIO 11 (Loader Auger Relay) HIGH while maintaining GPIO 10 HIGH. | [T] |
| **REQ-118** | Dispense Metering Duration Math | Loader Relay SHALL remain energized for exactly $t_{\text{meter}} = (\text{FeedPerEvent} / \text{DischargeRate})\text{ seconds} \pm 50\text{ ms}$. | [T] |
| **REQ-119** | Phase 3 Loader Cutoff | At $T = 3.0 + t_{\text{meter}}$, the system SHALL de-energize GPIO 11 (Loader Relay LOW). | [T] |
| **REQ-120** | Phase 3 Spreader Post-Clear Duration | GPIO 10 (Spreader Relay) SHALL remain energized for exactly $3.0\text{ seconds} \pm 50\text{ ms}$ following Loader cutoff. | [T] |
| **REQ-121** | Total Actuation Relay De-energize | At $T = 3.0 + t_{\text{meter}} + 3.0$, the system SHALL de-energize GPIO 10 (Spreader Relay LOW), completing the pulse. | [T] |
| **REQ-122** | Cumulative Dispense Math Tracking | Upon completion of Phase 3, the engine SHALL increment `dispensedQuantity_g += FeedPerEvent` and `currentEvent += 1`. | [A] |
| **REQ-123** | NVS Run State Checkpoint | The system SHALL persist `currentEvent`, `dispensedQuantity_g`, and `lastFedDay` to NVS at the end of each pulse. | [T] |
| **REQ-124** | Dispense Telemetry Event Generation | Upon completion of Phase 3, the system SHALL immediately queue a `LoRaUplinkPayload` with MsgType `0x21` (Event Report). | [D] |
| **REQ-125** | Relay Non-Overlap Failsafe | The firmware SHALL guarantee that the Loader Relay (GPIO 11) is NEVER energized while the Spreader Relay (GPIO 10) is de-energized. | [T] |
| **REQ-126** | Relay Command Inversion Guard | If GPIO 10 fails to assert within 50ms, GPIO 11 SHALL NOT be asserted, and `MOTOR FAULT` SHALL be raised. | [T] |
| **REQ-127** | Spreader Motor Current Sampling | During Phase 1, Phase 2, and Phase 3, motor current SHALL be measured via INA219 every $50\text{ ms}$. | [T] |
| **REQ-128** | Active Pulse LED Indication | The STAT2 Green LED SHALL flash at $5\text{ Hz}$ during Phase 1, Phase 2, and Phase 3. | [D] |
| **REQ-129** | Emergency Motor Abort Latency | An emergency stop signal from software, overcurrent, or proximity SHALL de-energize both relays within $\le 10\text{ ms}$. | [T] |
| **REQ-130** | Watchdog Refresh in Dispense Loop | The FreeRTOS feed task SHALL pet the hardware watchdog timer every $\le 100\text{ ms}$ throughout the dispensing sequence. | [T] |

---

### Category 8: Safety Interlocks, Current Monitoring & Motor Trip (REQ-131 to REQ-145)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-131** | Overcurrent Trip Threshold | If INA219 measured current exceeds $3500\text{ mA} (3.5\text{A})$ for $\ge 150\text{ ms}$, the system SHALL trigger an Overcurrent Motor Trip. | [T] |
| **REQ-132** | Immediate Actuator Cutoff on Trip | Upon Overcurrent Trip, GPIO 10 and GPIO 11 SHALL be forced LOW within $\le 5\text{ ms}$. | [T] |
| **REQ-133** | Acoustic Overcurrent Alarm | Upon Overcurrent Trip, the piezo hooter (GPIO 42) SHALL sound continuously for $3.0\text{ seconds}$. | [D] |
| **REQ-134** | Visual Overcurrent Alarm | Upon Overcurrent Trip, the STAT1 Red LED SHALL latch ON and the RGB LED SHALL illuminate solid RED (`255, 0, 0`). | [D] |
| **REQ-135** | System State Latch on Trip | The system state SHALL transition to `SystemState::ERROR_FATAL` with error code `ERR_OVERCURRENT`. | [T] |
| **REQ-136** | Telemetry Bitmask Assertion on Trip | The telemetry engine SHALL assert `Bit 1` (`0x02` Overcurrent Trip) in `statusFlags` on all subsequent uplinks. | [T] |
| **REQ-137** | Cloud Alert Uplink on Trip | The system SHALL immediately transmit an emergency uplink packet with MsgType `0x04` (Feed Paused / Alarm). | [D] |
| **REQ-138** | LCD Motor Jam Notification | The LCD SHALL display `State: MOTOR TRIP  ` on Row 1 and `Overcurrent Check HW` on Row 2. | [I] |
| **REQ-139** | Jam Auto-Clear Prohibition | The system SHALL NOT automatically restart feeding following an Overcurrent Trip. Manual user intervention is mandatory. | [T] |
| **REQ-140** | Manual Jam Clearance Reset | The user SHALL only clear a Motor Trip by pressing `[BACK]` from the Home Screen or power-cycling the device. | [D] |
| **REQ-141** | Brownout Voltage Floor | If battery voltage drops below $10.2\text{V}$ for $> 500\text{ ms}$, the system SHALL inhibit motor actuation and report `LOW BATTERY`. | [T] |
| **REQ-142** | Solar Overvoltage Protection | If voltage exceeds $16.0\text{V}$, the system SHALL log a warning and clamp charging indicators. | [T] |
| **REQ-143** | Thermal Cutoff Protection | If DS3231 internal temperature sensor reports $> 70^\circ\text{C}$, motor dispense operations SHALL be paused until temperature $\le 60^\circ\text{C}$. | [T] |
| **REQ-144** | Relay Weld Detection | If current $> 100\text{ mA}$ is detected when both relays are commanded OFF, system SHALL latch `RELAY HARDWARE FAULT`. | [T] |
| **REQ-145** | Current Sensor Communication Loss | If INA219 fails to acknowledge on I2C during dispense, the system SHALL limit maximum pulse time to $2.0 \times t_{\text{meter}}$ as a failsafe. | [T] |

---

### Category 9: Hopper Level Sensing, Proximity & Hooter Alarm (REQ-146 to REQ-160)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-146** | Proximity Sensor Hardware Input | The hopper level sensor SHALL be monitored via GPIO 16 through a PC817 optocoupler with a 10kΩ pull-up. | [I] |
| **REQ-147** | Hopper Empty Sensor State | When feed level drops below the sensor window, the optocoupler transistor de-energizes, pulling GPIO 16 HIGH (Active HIGH dry). | [T] |
| **REQ-148** | Hopper Empty Debounce Window | GPIO 16 must remain continuously HIGH for $\ge 100\text{ ms}$ before triggering `FEED EMPTY` to eliminate pellet bounce noise. | [T] |
| **REQ-149** | Feed Empty Mid-Pulse Abort | If `FEED EMPTY` triggers during Phase 1, Phase 2, or Phase 3, the Loader Relay SHALL de-energize immediately, followed by a 3s Spreader clear. | [T] |
| **REQ-150** | System State on Empty | The system state SHALL transition to `SystemState::FEED_PAUSED`. | [T] |
| **REQ-151** | Telemetry Bitmask on Empty | The telemetry engine SHALL assert `Bit 3` (`0x08` Feed Hopper Empty) and `Bit 4` (`0x10` Feeder Paused) in `statusFlags`. | [T] |
| **REQ-152** | Hooter Empty Acoustic Pattern | While paused due to empty hopper, the piezo hooter SHALL emit three $200\text{ ms}$ chirps separated by $100\text{ ms}$ pauses, repeating every $15\text{ seconds}$. | [D] |
| **REQ-153** | Visual Empty Indicator | The STAT1 Red LED SHALL flash at $1\text{ Hz}$ while paused due to empty hopper. | [D] |
| **REQ-154** | LCD Empty Screen Display | The LCD SHALL display `Error: FEED EMPTY   ` on Row 1 and `[SEL]: Resume       ` on Row 2 of the Paused Screen. | [I] |
| **REQ-155** | Proximity Active Low Config Option | If `config.proxAlarmHigh == false`, the active level logic SHALL be inverted to support normally-closed proximity switches. | [T] |
| **REQ-156** | Resume Sensor Interlock | Pressing `[SELECT]` on the Paused Screen SHALL verify `hal.isProximityTriggered() == false` before permitting resume. | [T] |
| **REQ-157** | Refusal on Uncleared Sensor | If `[SELECT]` is pressed while sensor is still dry (hopper empty), the hooter SHALL emit a negative double-buzz and remain paused. | [D] |
| **REQ-158** | Hooter Mute Capability | Pressing `[BACK]` while on the Paused Screen SHALL mute the periodic acoustic hooter while retaining visual error flags. | [D] |
| **REQ-159** | Auto-Resume Prohibition | The feeder SHALL NOT automatically resume dispensing when pellets are refilled without operator confirmation (LCD SEL or Cloud Downlink). | [T] |
| **REQ-160** | Pellets Refilled Telemetry | When hopper is refilled and resumed, an uplink with Bit 3 (`0x08`) cleared SHALL be transmitted within $\le 2\text{ seconds}$. | [D] |

---

### Category 10: Pause, Resume Engine & Manual Feed (REQ-161 to REQ-175)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-161** | Same-Window Resume Invariant | If paused and resumed within the SAME wait cycle ($t_{\text{pause}} < t_{\text{gap}}$), the engine SHALL NOT recalculate intervals and retain `nextFeedEpoch`. | [T] |
| **REQ-162** | Same-Window Countdown Continuity | In Scenario A (Same-Window Resume), the countdown on Row 2 SHALL resume from $(T_{\text{nextFeed}} - T_{\text{current}})$. | [A] |
| **REQ-163** | Extended Pause Threshold | If total paused duration exceeds $t_{\text{gap}}$, the system SHALL classify the event as Scenario B (Extended Pause). | [A] |
| **REQ-164** | Extended Pause Dynamic Recalculation | In Scenario B, the engine SHALL invoke `recalcDynamic()`, re-distributing remaining kilograms across remaining daylight minutes until `EndHour:EndMin`. | [A] |
| **REQ-165** | Immediate Pulse on Extended Resume | In Scenario B, the feeder SHALL fire a compensatory feed pulse within $\le 1.0\text{ second}$ of resume confirmation. | [D] |
| **REQ-166** | Feed Session Cancel Action | Pressing `[BACK]` on the Paused Screen SHALL set `state = IDLE`, disable `feedActive`, and cancel all remaining pulses for the day. | [D] |
| **REQ-167** | Manual Check Tray Invocation | Selecting `Check Tray` from `MENU_LIST` SHALL initiate a single 1-pulse feed burst regardless of current gap delay state. | [D] |
| **REQ-168** | Check Tray Night Lockdown | The system SHALL reject `Check Tray` requests received between `18:00` and `06:00 IST` with error `Outside Feed Window`. | [T] |
| **REQ-169** | Check Tray Weight Non-Deduction | Pellets dispensed during `Check Tray` SHALL be tracked under `trayCheckGrams` and SHALL NOT deduct from the scheduled daily target. | [T] |
| **REQ-170** | Check Tray Telemetry Record | Upon `Check Tray` completion, a dedicated uplink packet with MsgType `0x0A` (Tray Checkin) SHALL be transmitted. | [D] |
| **REQ-171** | Remote Cloud Pause Execution | Upon receiving Downlink Command `0xA1` (CMD_STOP_FEED), the feeder SHALL pause within $\le 500\text{ ms}$ and assert `state = FEED_PAUSED`. | [T] |
| **REQ-172** | Remote Cloud Resume Execution | Upon receiving Downlink Command `0xA2` (CMD_RESUME_FEED), the feeder SHALL execute resume logic identical to LCD SELECT. | [T] |
| **REQ-173** | Remote Cloud Start Execution | Upon receiving Downlink Command `0xA0` (CMD_START_FEED), the feeder SHALL start the daily feeding session. | [T] |
| **REQ-174** | Pause Duration Metric Tracking | The firmware SHALL log total cumulative pause duration per day in minutes to evaluate feeder availability metrics. | [A] |
| **REQ-175** | Motor Pre-Pause State Recovery | If paused during Phase 2 (Dispense), the resume cycle SHALL first run a full 3s Pre-warmup before re-engaging the auger. | [T] |

---

### Category 11: Real-Time Clock, UTC/IST & Time Synchronization (REQ-176 to REQ-185)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-176** | Hardware RTC Architecture | The system SHALL maintain local real-time clock via an external DS3231 I2C RTC with integrated temperature-compensated crystal. | [I] |
| **REQ-177** | Local Timezone Representation | All time variables inside the DS3231 (`Hour`, `Minute`, `Second`, `Day`, `Month`, `Year`) SHALL represent **Indian Standard Time (IST, UTC+5:30)**. | [T] |
| **REQ-178** | Firmware Epoch Derivation | The firmware function `rtcMgr.getEpoch()` SHALL compute seconds from `1970-01-01` assuming stored RTC fields are local time components. | [A] |
| **REQ-179** | Calendar Day Index Formula | The calendar day index SHALL be calculated as $\text{CurrentDay} = \lfloor \text{LocalEpoch} / 86400 \rfloor$, guaranteeing midnight rollover at exactly 00:00:00 IST. | [A] |
| **REQ-180** | Software RTC Synchronization | The Software RTC fallback timer SHALL synchronize with DS3231 on every successful read to eliminate millisecond drift. | [T] |
| **REQ-181** | Cloud Time Synchronization Downlink | The cloud Lambda SHALL evaluate device clock on every uplink. If `abs(DeviceEpoch - CloudEpoch) > 120 seconds`, a Downlink `0xA4` SHALL be queued. | [T] |
| **REQ-182** | RTC Adjustment Execution | Upon receiving Downlink `0xA4` (`CMD_SYNC_RTC`), the firmware SHALL write the received 32-bit epoch to DS3231 via `rtc.adjust()`. | [T] |
| **REQ-183** | RTC Fault Telemetry Flag | If the DS3231 oscillator stop flag (OSF) is asserted, the firmware SHALL assert `Bit 2` (`0x04` RTC Fault) in `statusFlags`. | [T] |
| **REQ-184** | Smooth Schedule Realignment | When RTC is updated by cloud downlink, ongoing wait delays SHALL NOT jump erratically; `nextFeedEpoch` SHALL be recomputed smoothly. | [T] |
| **REQ-185** | Daylight Savings Immunity | The firmware SHALL NOT implement daylight savings adjustments, operating on continuous UTC+5:30 year-round. | [I] |

---

### Category 12: Wireless Telemetry & LoRaWAN Communications Contract (REQ-186 to REQ-200)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-186** | Uplink Packet Size | The binary LoRaWAN uplink payload SHALL strictly measure **16 bytes** with `__attribute__((packed))` struct alignment. | [T] |
| **REQ-187** | Uplink Port Mapping | All telemetry uplink packets SHALL be transmitted on LoRaWAN **FPort 1**. | [T] |
| **REQ-188** | Downlink Port Mapping | All cloud commands and configuration downlinks SHALL be received on LoRaWAN **FPort 2**. | [T] |
| **REQ-189** | LoRaWAN Radio Modulation | Uplinks SHALL transmit in the IN865 band (865–867 MHz) using Spreading Factor SF7 to SF12, 125 kHz bandwidth. | [T] |
| **REQ-190** | Bit 5 Diagnostic Isolation | In the LoRa binary payload, `Bit 5` (`0x20`) of `statusFlags` SHALL strictly denote **SD Card Fault / Missing Card**. | [I] |
| **REQ-191** | Cloud Misinterpretation Prohibition | Cloud ingestion services SHALL NOT interpret `Bit 5` (`0x20`) as feed active. `FEEDING` state SHALL strictly depend on message type and daylight window. | [I] |
| **REQ-192** | Day/Night LoRaWAN Class Switching | The system SHALL operate in **Class C** (Continuous RX) between 06:00 and 18:00, and switch to **Class A** (Power conservation) between 18:00 and 06:00. | [D] |
| **REQ-193** | Downlink Command Packet Format | The binary downlink packet SHALL strictly measure **12 bytes**, containing `cmdType`, `feedQty_100g`, `fpe_g`, `shour`, `smin`, `ehour`, `emin`, and `rate`. | [T] |
| **REQ-194** | Downlink Execution Acknowledgment | Within $\le 5\text{ seconds}$ of executing a downlink command, the feeder SHALL transmit an uplink reflecting the new status flags. | [D] |
| **REQ-195** | Uplink Queue Depth | The firmware telemetry queue SHALL hold a minimum of 20 unacknowledged events (`TELEMETRY_QUEUE_SIZE >= 20`) in FreeRTOS memory. | [T] |
| **REQ-196** | Telemetry Deduplication | The cloud DynamoDB ingestion Lambda SHALL deduplicate incoming uplinks using primary key `(DeviceId, Timestamp)`. | [T] |
| **REQ-197** | Daytime Telemetry Filtering | Cloud queries for "Today's Dispensed Feed" SHALL strictly filter telemetry records with `Timestamp >= today_start_epoch (00:00:00 IST)`. | [T] |
| **REQ-198** | Zero Item Rollover Invariant | When no telemetry records exist for the current calendar day, the API SHALL return `0.00 kg` and `0` events. | [T] |
| **REQ-199** | LoRa SX1262 SPI Transaction Mutex | All SPI bus interactions with SX1262 SHALL be protected by a FreeRTOS mutex to prevent collision with SD card transactions. | [T] |
| **REQ-200** | Link Quality Telemetry | The feeder SHALL record and uplink RSSI and SNR metrics to enable RF network health analytics on the farm dashboard. | [T] |

---

### Category 13: Web & Mobile Dashboard UI Contract (REQ-201 to REQ-215)

| ID | Title | Requirement Statement | Method |
|---|---|---|---|
| **REQ-201** | Zero Jargon Presentation | The dashboard SHALL display human-friendly state badges (`STANDBY`, `FEEDING`, `PAUSED`, `COMPLETED`, `OFFLINE`). Hex codes SHALL NOT be displayed. | [I] |
| **REQ-202** | Night Window Status Display | When local IST time is between 18:00 and 06:00, the dashboard status badge SHALL display **`STANDBY`** (never `FEEDING`). | [T] |
| **REQ-203** | Night Window Next Feed Display | Between 00:00 and 06:00 IST, the Next Feed card SHALL display **`06:00 AM`** with subtitle `Starts today at 06:00 AM`. | [I] |
| **REQ-204** | Evening Next Feed Display | Between 18:00 and 24:00 IST, the Next Feed card SHALL display **`06:00 AM`** with subtitle `Starts tomorrow at 06:00 AM`. | [I] |
| **REQ-205** | Pre-Dawn Progress Bar Integrity | Between 00:00 and 06:00 IST on a new calendar day, the central circular gauge SHALL display **`0 / 50 EVENTS TODAY (0.0%)`**. | [T] |
| **REQ-206** | Pre-Dawn Dispensed Weight Integrity | Between 00:00 and 06:00 IST, the Dispensed Today metric card SHALL display **`0.00 kg`** (never yesterday's accumulated weight). | [T] |
| **REQ-207** | Standby Action Button Mapping | When feeder is in `STANDBY`, the primary button SHALL display **`START FEEDING`** (enabled) and the secondary button SHALL display `STOP FEEDING` (disabled). | [D] |
| **REQ-208** | Night Arming Operator Confirmation | Clicking `START FEEDING` during night hours SHALL display an informational prompt: *"Feeder armed for 06:00 AM. No feed will dispense tonight."* | [D] |
| **REQ-209** | Feeding Action Button Mapping | When feeder is in `FEEDING`, the primary button SHALL display **`FEED BURST NOW`** and secondary button SHALL display **`STOP FEEDING`** (active red). | [D] |
| **REQ-210** | Paused Action Button Mapping | When feeder is in `PAUSED`, the primary button SHALL display **`RESUME FEEDING`** (active cyan) and secondary button SHALL display **`STOP FEEDING`**. | [D] |
| **REQ-211** | Completed Action Button Mapping | When feeder is in `COMPLETED`, the primary button SHALL display **`START FEEDING`** (armed for tomorrow) and secondary button SHALL be disabled. | [D] |
| **REQ-212** | Mobile Viewport Responsiveness | The web dashboard layout SHALL render responsively on mobile viewports ($375\text{px}$ to $430\text{px}$ width) without horizontal scrolling. | [D] |
| **REQ-213** | Auto-Refresh Polling Cycle | The dashboard SHALL poll `GET /api/devices` every $5.0\text{ seconds}$ to reflect near-real-time farm telemetry. | [T] |
| **REQ-214** | History Tab Event Log Isolation | The History tab SHALL only list feed pulses timestamped on the active operational date. Past sessions SHALL be grouped under "Previous Sessions". | [T] |
| **REQ-215** | Cloud Command Pending Pill | While a downlink command is queued in DynamoDB awaiting delivery, the UI SHALL display a pulsing indicator: `⏳ Command Sync Pending`. | [D] |

---

## 4. Verification & Traceability Cross-Reference

| System Tier | Requirements Covered | Primary Verification Tool |
|---|---|---|
| **Firmware Core & HAL** | REQ-001 to REQ-018, REQ-041 to REQ-058, REQ-116 to REQ-160 | Hardware-in-the-loop (HIL), Oscilloscope, Logic Analyzer |
| **20x4 LCD Display UI** | REQ-019 to REQ-040, REQ-059 to REQ-075 | Visual String Budget Audit, LCD Character Counter Scripts |
| **Feed Engine & Math** | REQ-076 to REQ-115, REQ-161 to REQ-185 | Unit Tests, Mathematical Timing Analysis, Epoch Rollover Sim |
| **LoRaWAN & Cloud Microservices** | REQ-186 to REQ-200 | AWS CloudWatch, Packet Logger, LoRaWAN Gateway Console |
| **Web & Mobile Dashboard** | REQ-201 to REQ-215 | Selenium WebDriver, Mobile Emulation, API Integration Tests |

---
**End of Specification**  
*aquaCON™ Engineering Architecture Group — Confidential & Proprietary*
