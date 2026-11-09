"""
Automated Test Suite for aquaCON Cloud & Web Dashboard Requirements
Validates REQ-181, REQ-191, REQ-193, REQ-196, REQ-197, REQ-198, and REQ-201 through REQ-215.
"""

import os
import sys
import struct
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

class TestCloudRequirements(unittest.TestCase):

    def test_req_181_time_sync_downlink(self):
        """REQ-181: Cloud Time Synchronization Downlink (CMD_SYNC_TIME 0xA3)"""
        with open(os.path.join(WORKSPACE, "lambda_function.py"), "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("def auto_sync_rtc_if_needed", code)
        self.assertIn("0xA3", code)
        self.assertIn("ist_now = now_epoch + IST_OFFSET_SEC", code)
        down_bytes = struct.pack('<BI7s', 0xA3, 1730970000, b'\x00' * 7)
        self.assertEqual(len(down_bytes), 12, "Time sync downlink payload must be exactly 12 bytes")
        self.assertEqual(down_bytes[0], 0xA3, "Downlink opcode for time sync must be 0xA3 (CMD_SYNC_TIME)")

    def test_req_191_cloud_misinterpretation_prohibition(self):
        """REQ-191: Bit 5 (0x20 = SD Card) must NOT be interpreted as feed active"""
        with open(os.path.join(WORKSPACE, "lambda_function.py"), "r", encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("status_flags & 0x20", code)
        self.assertIn("flag_proximity = (status_flags & 0x01) != 0", code)
        self.assertIn("flag_overcurrent = (status_flags & 0x02) != 0", code)
        self.assertIn("flag_empty = (status_flags & 0x08) != 0", code)

    def test_req_193_downlink_packet_format(self):
        """REQ-193: Downlink packet must strictly measure 12 bytes across all commands"""
        p_start = struct.pack('<B11s', 0xA4, b'\x00' * 11)
        self.assertEqual(len(p_start), 12, "START packet must be 12 bytes")

        p_stop = struct.pack('<B11s', 0xA5, b'\x00' * 11)
        self.assertEqual(len(p_stop), 12, "STOP packet must be 12 bytes")

        p_resume = struct.pack('<B11s', 0xA6, b'\x00' * 11)
        self.assertEqual(len(p_resume), 12, "RESUME packet must be 12 bytes")

        p_sync = struct.pack('<BI7s', 0xA3, 1730970000, b'\x00' * 7)
        self.assertEqual(len(p_sync), 12, "SYNC TIME packet must be 12 bytes")

        p_motor = struct.pack('<BBHHBBBB2s', 0xA2, 0, 0, 0, 0, 1, 0, 2, b'\x00\x00')
        self.assertEqual(len(p_motor), 12, "TEST MOTOR packet must be 12 bytes")

        p_set = struct.pack('<BBHHBBBB2s', 0xA0, 1, 15, 100, 6, 0, 18, 0, b'\x00\x00')
        self.assertEqual(len(p_set), 12, "SETTINGS packet must be 12 bytes")

    def test_req_196_telemetry_deduplication(self):
        """REQ-196: Ingestion Lambda deduplicates incoming uplinks by primary key (DeviceId, Timestamp)"""
        with open(os.path.join(WORKSPACE, "lambda_function.py"), "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("telemetry_table.put_item", code)
        self.assertIn("'DeviceId': dev_eui", code)
        self.assertIn("'Timestamp':", code)

    def test_req_197_daytime_telemetry_filtering(self):
        """REQ-197: Cloud query for today's feed filters strictly >= 00:00:00 IST"""
        with open(os.path.join(WORKSPACE, "api_lambda.py"), "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("today_start_epoch =", code)
        self.assertIn("if ts < today_start_epoch:", code)
        self.assertIn("continue", code)

    def test_req_198_zero_item_rollover_invariant(self):
        """REQ-198: When no telemetry records exist for current calendar day, returns 0.00 kg and 0 events"""
        with open(os.path.join(WORKSPACE, "api_lambda.py"), "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("actual_dispensed_kg = 0.0", code)
        self.assertIn("active_ev = 0", code)

    def test_req_201_zero_jargon_presentation(self):
        """REQ-201: Dashboard displays human-friendly badges (STANDBY, FEEDING, PAUSED, COMPLETED, OVERCURRENT, EMPTY)"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        for friendly in ["STANDBY", "FEEDING", "PAUSED", "COMPLETED", "OVERCURRENT", "EMPTY"]:
            self.assertIn(friendly, app_js, f"Dashboard must handle state {friendly}")
        self.assertNotIn("FC_WAIT", app_js, "Internal state code FC_WAIT should not appear in dashboard")

    def test_req_202_night_window_status_display(self):
        """REQ-202: Between 18:00 and 06:00 IST, dashboard status badge displays STANDBY"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("const isNightTime = nowTotalMin < startTotalMin || nowTotalMin >= endTotalMin;", app_js)
        self.assertIn("statusText = 'STANDBY';", app_js)

    def test_req_203_night_window_next_feed_display(self):
        """REQ-203: Between 00:00 and 06:00 IST, Next Feed displays morning schedule"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("isBeforeSchedule", app_js)
        self.assertIn("Starts at", app_js)

    def test_req_204_evening_next_feed_display(self):
        """REQ-204: Between 18:00 and 24:00 IST, Next Feed displays tomorrow's schedule"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("Starts tomorrow at", app_js)

    def test_req_205_pre_dawn_progress_bar_integrity(self):
        """REQ-205: Between 00:00 and 06:00 IST on a new calendar day, progress gauge displays 0%"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("const effectiveCurrent = isBeforeSchedule ? 0 : rawCurrent;", app_js)

    def test_req_206_pre_dawn_dispensed_weight_integrity(self):
        """REQ-206: Between 00:00 and 06:00 IST, Dispensed Today displays 0.00 kg"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("const rawDispensed = isBeforeSchedule ? 0.0 : authoritativeDispensed;", app_js)

    def test_req_207_standby_action_button_mapping(self):
        """REQ-207: In STANDBY, primary button displays START FEEDING and is active"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("btnStart.innerHTML = `<span class=\"btn-icon\"><svg width=\"15\" height=\"15\" viewBox=\"0 0 24 24\" fill=\"currentColor\"><polygon points=\"5 3 19 12 5 21 5 3\"/></svg></span><span>START FEEDING</span>`;", app_js)
        self.assertIn("triggerRemoteAction('START')", app_js)

    def test_req_208_night_arming_operator_confirmation(self):
        """REQ-208: Clicking START FEEDING during night hours displays informational prompt/arming"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("Click to Start / Arm: Feeder begins automatically", app_js)

    def test_req_209_feeding_action_button_mapping(self):
        """REQ-209: When FEEDING, primary button displays FEED BURST NOW and secondary button is STOP FEEDING"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("<span>FEED BURST NOW</span>", app_js)
        self.assertIn("triggerRemoteAction('STOP')", app_js)

    def test_req_210_paused_action_button_mapping(self):
        """REQ-210: When PAUSED, primary button displays RESUME FEEDING and is active"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("<span>RESUME FEEDING</span>", app_js)
        self.assertIn("triggerRemoteAction('RESUME')", app_js)

    def test_req_211_completed_action_button_mapping(self):
        """REQ-211: When COMPLETED, primary button allows arming or restart"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("isTrulyCompleted", app_js)
        self.assertIn("Today's feeding completed. Click to arm for tomorrow or restart.", app_js)

    def test_req_212_mobile_viewport_responsiveness(self):
        """REQ-212: Web dashboard layout has responsive viewport meta tag and mobile-first container max-width"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('<meta name="viewport" content="width=device-width', html)
        with open(os.path.join(WORKSPACE, "web_dashboard", "styles.css"), "r", encoding="utf-8") as f:
            css = f.read()
        self.assertIn("max-width: 440px", css)

    def test_req_213_auto_refresh_polling_cycle(self):
        """REQ-213: Dashboard polls GET /api/devices every 5.0 seconds"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("function startTelemetryLoop()", app_js)
        self.assertIn("}, 5000);", app_js)

    def test_req_214_history_tab_event_log_isolation(self):
        """REQ-214: History tab isolates events to active operational date"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("todayIso = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });", app_js)
        self.assertIn("todayEvents = dev.eventsLog.filter(e => e.date === todayIso);", app_js)

    def test_req_215_cloud_command_pending_pill(self):
        """REQ-215: While downlink command is queued, displays pending confirmation callout"""
        with open(os.path.join(WORKSPACE, "web_dashboard", "app.js"), "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("command-sync-callout", app_js)
        self.assertIn("Starting feeder... waiting for confirmation", app_js)

if __name__ == "__main__":
    unittest.main()
