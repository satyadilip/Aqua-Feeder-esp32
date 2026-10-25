import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, safe_click, take_test_screenshot

def test_feeder1_sunday_history_rendered(auth_driver):
    """
    Verifies that Feeder 1 history view correctly displays Sunday 10/25 feed data
    even though Feeder 1 is currently offline.
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

    # 4. Verify Week Total is NOT 0.0 Kg
    week_total = auth_driver.find_element(By.ID, "stat-week-total").get_attribute("textContent").strip()
    print(f"Week Total: {week_total}")
    assert week_total != "0.0 Kg", f"Week total should not be 0.0 Kg for Feeder 01! Got '{week_total}'"

    # 5. Check bars
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
    assert float(sunday_bar["val"]) > 0, f"Sunday bar should have > 0 Kg feed! Got {sunday_bar['val']}"

    # 6. Check events log
    log_label = auth_driver.find_element(By.ID, "log-date-label").get_attribute("textContent").strip()
    print(f"Events Log Label: {log_label}")
    event_items = auth_driver.find_elements(By.CSS_SELECTOR, "#events-log-container .event-log-item")
    print(f"Event items count: {len(event_items)}")
    assert len(event_items) > 0, "There should be event log items visible for Feeder 01!"

    take_test_screenshot(auth_driver, "test_feeder1_sunday_history_verified")
    print("TEST PASSED: Feeder 1 Sunday feed history verified successfully!")
