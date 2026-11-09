# aquaCON™ Requirements Traceability & Verification Matrix

**Generated:** 2026-11-07 15:24:18  
**Compliance Standard:** ISO/IEC/IEEE 29148:2018  
**Status:** 1/215 Passed (0.5%) | 0 Failed | 214 Pending

---

| UID | Category | Title | Method | Target | Status | Verified Date | Reference |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---|
| **REQ-001** | Cat 1 | Power-On Relay Isolation | [T] | Feeder 03 (ESP32-S3) | **PASSED** | 2026-11-07 15:24:15 | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-002** | Cat 1 | Power-On Hooter Isolation | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-003** | Cat 1 | Boot Visual Indicator | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-004** | Cat 1 | I2C Bus Bring-up | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-005** | Cat 1 | LCD Detection & Fallback | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-006** | Cat 1 | Custom CGRAM Registration | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-007** | Cat 1 | Splash Screen Line 0 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-008** | Cat 1 | Splash Screen Line 1 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-009** | Cat 1 | Splash Screen Line 2 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-010** | Cat 1 | Splash Screen Line 3 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-011** | Cat 1 | Splash Screen Duration | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-012** | Cat 1 | Keypad Locking on Splash | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-013** | Cat 1 | Hardware RTC Initialization | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-014** | Cat 1 | Software RTC Fallback | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-015** | Cat 1 | INA219 Bring-up | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-016** | Cat 1 | NVS Configuration Load | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-017** | Cat 1 | First Boot Provisioning | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-018** | Cat 1 | Autonomous Home Screen Entry | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-019** | Cat 2 | Strict 20-Character Line Budget | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-020** | Cat 2 | Home Row 0 Clock Format | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-021** | Cat 2 | Home Row 0 No-Clock Fallback | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-022** | Cat 2 | Home Row 1 State Prefix | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-023** | Cat 2 | Home Row 1 Standby Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-024** | Cat 2 | Home Row 1 Scheduled Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-025** | Cat 2 | Home Row 1 Dispensing Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-026** | Cat 2 | Home Row 1 Warmup Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-027** | Cat 2 | Home Row 1 Post-Clear Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-028** | Cat 2 | Home Row 1 Gap Delay Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-029** | Cat 2 | Home Row 1 Feed Paused Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-030** | Cat 2 | Home Row 1 Completed Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-031** | Cat 2 | Home Row 1 Motor Trip Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-032** | Cat 2 | Home Row 2 Idle Prompt | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-033** | Cat 2 | Home Row 2 Gap Countdown | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-034** | Cat 2 | Home Row 2 Running Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-035** | Cat 2 | Home Row 3 Connectivity | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-036** | Cat 2 | Progress Bar Enclosure | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-037** | Cat 2 | Sub-Pixel Progress Math | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-038** | Cat 2 | Paused Screen Line 0 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-039** | Cat 2 | Paused Screen Line 2 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-040** | Cat 2 | Paused Screen Line 3 | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp` |
| **REQ-041** | Cat 3 | Keypad Hardware Sampling | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-042** | Cat 3 | Keypad Noise Debounce | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-043** | Cat 3 | Rising Edge Event Generation | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-044** | Cat 3 | Long-Press Repeat Delay | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-045** | Cat 3 | Long-Press Repeat Rate | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-046** | Cat 3 | Home to Menu Navigation | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-047** | Cat 3 | Menu Cursor Down | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-048** | Cat 3 | Menu Cursor Up | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-049** | Cat 3 | Menu Item Selection | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-050** | Cat 3 | Menu Escape to Home | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-051** | Cat 3 | Menu Inactivity Timeout | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-052** | Cat 3 | Edit Value Increment | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-053** | Cat 3 | Edit Value Decrement | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-054** | Cat 3 | Edit Value Commit | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-055** | Cat 3 | Edit Cancel Discard | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-056** | Cat 3 | Running Screen Keypad Interlock | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-057** | Cat 3 | Paused Resume Keypad Action | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-058** | Cat 3 | Paused Cancel Keypad Action | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-059** | Cat 4 | 4-Row Windowed Pagination | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-060** | Cat 4 | Active Item Cursor Tag | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-061** | Cat 4 | Inactive Item Cursor Tag | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-062** | Cat 4 | Menu Item 0 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-063** | Cat 4 | Menu Item 1 Dynamic Text | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-064** | Cat 4 | Menu Item 2 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-065** | Cat 4 | Menu Item 3 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-066** | Cat 4 | Menu Item 4 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-067** | Cat 4 | Menu Item 5 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-068** | Cat 4 | Menu Item 6 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-069** | Cat 4 | Menu Item 7 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-070** | Cat 4 | Menu Item 8 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-071** | Cat 4 | Menu Item 9 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-072** | Cat 4 | Menu Item 10 Text | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-073** | Cat 4 | Empty Slot Blanking | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-074** | Cat 4 | Diagnostics Submenu Items | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-075** | Cat 4 | Diagnostics Manual Test Safety | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lcd_display.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-076** | Cat 5 | Feed Quantity Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-077** | Cat 5 | Feed Quantity Step Size | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-078** | Cat 5 | Feed Per Event Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-079** | Cat 5 | Feed Per Event Step Size | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-080** | Cat 5 | Start Hour Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-081** | Cat 5 | Start Minute Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-082** | Cat 5 | End Hour Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-083** | Cat 5 | End Minute Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-084** | Cat 5 | Operational Daylight Enclosure | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-085** | Cat 5 | Chronological Ordering Rule | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-086** | Cat 5 | Discharge Rate Range | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-087** | Cat 5 | Discharge Rate Step Size | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-088** | Cat 5 | NVS Flash Wear Reduction | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-089** | Cat 5 | Atomic NVS Transaction | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-090** | Cat 5 | Total Events Deduction | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-091** | Cat 5 | Overfill Window Prevention | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-092** | Cat 5 | Settings Uplink Notification | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-093** | Cat 5 | Clock Setting Field 0 | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-094** | Cat 5 | Clock Setting Field 1 | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-095** | Cat 5 | Factory Reset Key Combo | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/config_manager.cpp;AquaFeeder/config.h` |
| **REQ-096** | Cat 6 | Strict Night Window Motor Lockdown | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-097** | Cat 6 | Unarmed First Boot Invariant | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-098** | Cat 6 | Night Arming Behavior | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-099** | Cat 6 | Single Event Duration Formula | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-100** | Cat 6 | Full Window Duration Formula | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-101** | Cat 6 | Base Gap Calculation | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-102** | Cat 6 | Remaining Events Deduction | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-103** | Cat 6 | Dynamic Gap Recalculation | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-104** | Cat 6 | Dynamic Gap Ceiling | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-105** | Cat 6 | Minimum Inter-Pulse Gap | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-106** | Cat 6 | Day Rollover Autonomous Trigger | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-107** | Cat 6 | Target Dispensed Weight Completion | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-108** | Cat 6 | Target Event Count Completion | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-109** | Cat 6 | End of Operational Hours Concession | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-110** | Cat 6 | Immediate First Pulse on Manual Start | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-111** | Cat 6 | Next Feed Epoch Projection | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-112** | Cat 6 | Telemetry Heartbeat in Gap Delay | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-113** | Cat 6 | Time Drift Realignment | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-114** | Cat 6 | Completion Lockout on Same Day | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-115** | Cat 6 | Check Tray Schedule Independence | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp` |
| **REQ-116** | Cat 7 | Phase 1 Spreader Pre-Warmup | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-117** | Cat 7 | Phase 2 Loader Metering Engagement | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-118** | Cat 7 | Dispense Metering Duration Math | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-119** | Cat 7 | Phase 3 Loader Cutoff | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-120** | Cat 7 | Phase 3 Spreader Post-Clear Duration | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-121** | Cat 7 | Total Actuation Relay De-energize | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-122** | Cat 7 | Cumulative Dispense Math Tracking | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-123** | Cat 7 | NVS Run State Checkpoint | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-124** | Cat 7 | Dispense Telemetry Event Generation | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-125** | Cat 7 | Relay Non-Overlap Failsafe | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-126** | Cat 7 | Relay Command Inversion Guard | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-127** | Cat 7 | Spreader Motor Current Sampling | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-128** | Cat 7 | Active Pulse LED Indication | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-129** | Cat 7 | Emergency Motor Abort Latency | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-130** | Cat 7 | Watchdog Refresh in Dispense Loop | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-131** | Cat 8 | Overcurrent Trip Threshold | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-132** | Cat 8 | Immediate Actuator Cutoff on Trip | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-133** | Cat 8 | Acoustic Overcurrent Alarm | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-134** | Cat 8 | Visual Overcurrent Alarm | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-135** | Cat 8 | System State Latch on Trip | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-136** | Cat 8 | Telemetry Bitmask Assertion on Trip | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-137** | Cat 8 | Cloud Alert Uplink on Trip | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-138** | Cat 8 | LCD Motor Jam Notification | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-139** | Cat 8 | Jam Auto-Clear Prohibition | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-140** | Cat 8 | Manual Jam Clearance Reset | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-141** | Cat 8 | Brownout Voltage Floor | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-142** | Cat 8 | Solar Overvoltage Protection | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-143** | Cat 8 | Thermal Cutoff Protection | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-144** | Cat 8 | Relay Weld Detection | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-145** | Cat 8 | Current Sensor Communication Loss | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/power_monitor.cpp;AquaFeeder/af_hal.cpp` |
| **REQ-146** | Cat 9 | Proximity Sensor Hardware Input | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-147** | Cat 9 | Hopper Empty Sensor State | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-148** | Cat 9 | Hopper Empty Debounce Window | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-149** | Cat 9 | Feed Empty Mid-Pulse Abort | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-150** | Cat 9 | System State on Empty | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-151** | Cat 9 | Telemetry Bitmask on Empty | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-152** | Cat 9 | Hooter Empty Acoustic Pattern | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-153** | Cat 9 | Visual Empty Indicator | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-154** | Cat 9 | LCD Empty Screen Display | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-155** | Cat 9 | Proximity Active Low Config Option | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-156** | Cat 9 | Resume Sensor Interlock | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-157** | Cat 9 | Refusal on Uncleared Sensor | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-158** | Cat 9 | Hooter Mute Capability | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-159** | Cat 9 | Auto-Resume Prohibition | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-160** | Cat 9 | Pellets Refilled Telemetry | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/af_hal.cpp;AquaFeeder/feed_engine.cpp` |
| **REQ-161** | Cat 10 | Same-Window Resume Invariant | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-162** | Cat 10 | Same-Window Countdown Continuity | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-163** | Cat 10 | Extended Pause Threshold | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-164** | Cat 10 | Extended Pause Dynamic Recalculation | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-165** | Cat 10 | Immediate Pulse on Extended Resume | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-166** | Cat 10 | Feed Session Cancel Action | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-167** | Cat 10 | Manual Check Tray Invocation | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-168** | Cat 10 | Check Tray Night Lockdown | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-169** | Cat 10 | Check Tray Weight Non-Deduction | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-170** | Cat 10 | Check Tray Telemetry Record | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-171** | Cat 10 | Remote Cloud Pause Execution | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-172** | Cat 10 | Remote Cloud Resume Execution | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-173** | Cat 10 | Remote Cloud Start Execution | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-174** | Cat 10 | Pause Duration Metric Tracking | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-175** | Cat 10 | Motor Pre-Pause State Recovery | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/feed_engine.cpp;AquaFeeder/AquaFeeder.ino` |
| **REQ-176** | Cat 11 | Hardware RTC Architecture | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-177** | Cat 11 | Local Timezone Representation | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-178** | Cat 11 | Firmware Epoch Derivation | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-179** | Cat 11 | Calendar Day Index Formula | [A] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-180** | Cat 11 | Software RTC Synchronization | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-181** | Cat 11 | Cloud Time Synchronization Downlink | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-182** | Cat 11 | RTC Adjustment Execution | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-183** | Cat 11 | RTC Fault Telemetry Flag | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-184** | Cat 11 | Smooth Schedule Realignment | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-185** | Cat 11 | Daylight Savings Immunity | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/rtc_manager.cpp` |
| **REQ-186** | Cat 12 | Uplink Packet Size | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-187** | Cat 12 | Uplink Port Mapping | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-188** | Cat 12 | Downlink Port Mapping | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-189** | Cat 12 | LoRaWAN Radio Modulation | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-190** | Cat 12 | Bit 5 Diagnostic Isolation | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-191** | Cat 12 | Cloud Misinterpretation Prohibition | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-192** | Cat 12 | Day/Night LoRaWAN Class Switching | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-193** | Cat 12 | Downlink Command Packet Format | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-194** | Cat 12 | Downlink Execution Acknowledgment | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-195** | Cat 12 | Uplink Queue Depth | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-196** | Cat 12 | Telemetry Deduplication | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-197** | Cat 12 | Daytime Telemetry Filtering | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-198** | Cat 12 | Zero Item Rollover Invariant | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-199** | Cat 12 | LoRa SX1262 SPI Transaction Mutex | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-200** | Cat 12 | Link Quality Telemetry | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `AquaFeeder/lora_manager.cpp;AquaFeeder/telemetry.cpp` |
| **REQ-201** | Cat 13 | Zero Jargon Presentation | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-202** | Cat 13 | Night Window Status Display | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-203** | Cat 13 | Night Window Next Feed Display | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-204** | Cat 13 | Evening Next Feed Display | [I] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-205** | Cat 13 | Pre-Dawn Progress Bar Integrity | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-206** | Cat 13 | Pre-Dawn Dispensed Weight Integrity | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-207** | Cat 13 | Standby Action Button Mapping | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-208** | Cat 13 | Night Arming Operator Confirmation | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-209** | Cat 13 | Feeding Action Button Mapping | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-210** | Cat 13 | Paused Action Button Mapping | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-211** | Cat 13 | Completed Action Button Mapping | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-212** | Cat 13 | Mobile Viewport Responsiveness | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-213** | Cat 13 | Auto-Refresh Polling Cycle | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-214** | Cat 13 | History Tab Event Log Isolation | [T] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |
| **REQ-215** | Cat 13 | Cloud Command Pending Pill | [D] | Feeder 03 (ESP32-S3) | *PENDING* |  | `web_dashboard/app.js;Cloud/api_lambda.py` |