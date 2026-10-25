import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, safe_click, take_test_screenshot

def test_feeder1_sunday_history_and_monday_unstarted(auth_driver):
    """
    CRITICAL TEST:
    1. Verifies that Feeder 1 history correctly displays Sunday 10/25 feed (23.5 Kg, 235 cycles).
    2. Verifies that Monday 10/26 (today, before 6 AM feeding window) shows 0.0 Kg and is NOT prematurely marked as completed.
    3. Verifies that Feeder 2 on Tab 1 is in STANDBY state with 0.00 Kg dispensed before 6:00 AM.
    """
    # 1. Switch to Feeder 1
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(2)

    # 2. Navigate to History tab
    history_tab = auth_driver.find_element(By.ID, "tab-btn-history")
    safe_click(auth_driver, history_tab)
    time.sleep(3)

    # 3. Verify Feeder 1 header in history
    feeder_title = auth_driver.find_element(By.ID, "history-feeder-title").get_attribute("textContent").strip()
    assert "Feeder 01" in feeder_title, f"Expected Feeder 01 in history title, got '{feeder_title}'"

    # 4. Check 7-day bars
    bars = auth_driver.execute_script("""
      return Array.from(document.querySelectorAll('#history-chart-container .bar-column')).map(el => ({
        val: el.querySelector('.bar-val-lbl').textContent.trim(),
        day: el.querySelector('.bar-day-lbl').textContent.trim(),
        height: el.querySelector('.bar-pillar').style.height
      }));
    """)
    print("Bars rendered:", bars)
    assert len(bars) == 7, f"Expected 7 day bars, got {len(bars)}"

    # Check Sunday bar specifically
    sunday_bar = next((b for b in bars if "Sun" in b["day"]), None)
    assert sunday_bar is not None, f"Sunday bar should be in the 7-day chart! Bars: {bars}"
    print(f"Sunday Bar: {sunday_bar}")
    assert float(sunday_bar["val"]) == 23.5, f"Sunday bar should have exactly 23.5 Kg feed! Got {sunday_bar['val']}"

    # Check Monday bar (today - feeding has not started yet!)
    monday_bar = next((b for b in bars if "Mon" in b["day"]), None)
    assert monday_bar is not None, f"Monday bar should be in chart! Bars: {bars}"
    print(f"Monday Bar: {monday_bar}")
    assert float(monday_bar["val"]) == 0.0, (
        f"CRITICAL ERROR: Monday feed must be 0.0 Kg because schedule has not started! Got {monday_bar['val']}"
    )

    # Check events log
    log_label = auth_driver.find_element(By.ID, "log-date-label").get_attribute("textContent").strip()
    print(f"Events Log Label: {log_label}")
    event_items = auth_driver.find_elements(By.CSS_SELECTOR, "#events-log-container .event-log-item")
    print(f"Event items count: {len(event_items)}")
    assert len(event_items) > 0, "There should be event log items visible for Feeder 01!"

    take_test_screenshot(auth_driver, "test_feeder1_sunday_history_monday_zero")

def test_feeder2_status_standby_before_schedule(auth_driver):
    """
    Verifies that Feeder 2 (online node) shows STANDBY and 0.00 Kg dispensed before 6:00 AM.
    """
    # 1. Switch to Feeder 2
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(2)

    badge_text = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()
    dispensed_text = auth_driver.find_element(By.ID, "dispensed-val-text").get_attribute("textContent").strip()
    gauge_num = auth_driver.find_element(By.ID, "gauge-hero-num").get_attribute("textContent").strip()
    next_sub = auth_driver.find_element(By.ID, "next-feed-sub").get_attribute("textContent").strip()

    print(f"Feeder 2 Status: Badge='{badge_text}', Dispensed='{dispensed_text}', Gauge='{gauge_num}', Sub='{next_sub}'")

    assert badge_text == "STANDBY", f"Feeder 2 should be in STANDBY before schedule, got '{badge_text}'"
    assert dispensed_text == "0.00", f"Feeder 2 dispensed today should be 0.00 before schedule, got '{dispensed_text}'"
    assert gauge_num == "0", f"Feeder 2 gauge today should be 0 before schedule, got '{gauge_num}'"
    assert "Starts today" in next_sub or "06:00" in next_sub, f"Next feed sub should indicate today's start, got '{next_sub}'"

    take_test_screenshot(auth_driver, "test_feeder2_standby_before_schedule")
