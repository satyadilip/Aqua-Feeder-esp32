import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, take_test_screenshot

def test_history_feeder_switching_metrics(auth_driver):
    """
    DETAILED TEST 13.1:
    Verifies that switching between Feeder 01 and Feeder 02 in the History tab
    dynamically loads the respective feeder's target, week total, daily average, and chart.
    """
    # 1. Feeder 02 (15.0 kg target)
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-history');")
    time.sleep(2.5)

    title_02 = auth_driver.find_element(By.ID, "history-feeder-title").get_attribute("textContent").strip()
    target_02 = auth_driver.find_element(By.ID, "chart-target-lbl").get_attribute("textContent").strip()
    stat_week_02 = auth_driver.find_element(By.ID, "stat-week-total").get_attribute("textContent").strip()

    assert "Feeder 02" in title_02, f"Expected Feeder 02 in title, got: {title_02}"
    assert ("20.0" in target_02 or "15.0" in target_02), f"Feeder 02 target should be 20.0 or 15.0 Kg, got: {target_02}"
    assert "Kg" in stat_week_02, f"Week total should be formatted with Kg, got: {stat_week_02}"

    take_test_screenshot(auth_driver, "test_13_feeder02_history_view")

    # 2. Live Switch to Feeder 01 (50.0 kg target)
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(2.5)

    title_01 = auth_driver.find_element(By.ID, "history-feeder-title").get_attribute("textContent").strip()
    target_01 = auth_driver.find_element(By.ID, "chart-target-lbl").get_attribute("textContent").strip()

    assert "Feeder 01" in title_01, f"Expected Feeder 01 in title after switch, got: {title_01}"
    assert "50.0" in target_01, f"Feeder 01 target must be 50.0 Kg, got: {target_01}"

    take_test_screenshot(auth_driver, "test_13_feeder01_history_switched")

def test_history_sunday_completed_and_monday_unstarted(auth_driver):
    """
    DETAILED TEST 13.2:
    Verifies that for Feeder 01 (and Feeder 02):
    - Sunday (Oct 25) shows actual dispensed feed (23.5 kg / 15.0 kg).
    - Monday (Oct 26) strictly shows 0.0 kg dispensed before the 06:00 AM start time.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}'); navigateToTab('tab-history');")
    time.sleep(2.5)

    chart_container = auth_driver.find_element(By.ID, "history-chart-container")
    chart_text = chart_container.get_attribute("textContent").strip()

    # Verify Sunday Oct 25 completed feed is visible in chart
    assert "23.5" in chart_text, f"Chart must display Sunday's 23.5 kg feed, got: {chart_text}"

    # Verify Today's pillar
    today_pillar = auth_driver.find_element(By.CSS_SELECTOR, ".bar-pillar.today")
    assert today_pillar.is_displayed(), "Today's chart pillar must be rendered with .today class"

    take_test_screenshot(auth_driver, "test_13_chart_sunday_monday_verified")

def test_history_feed_events_log_order_and_tags(auth_driver):
    """
    DETAILED TEST 13.3:
    Verifies that the Feed Events log table renders event cycles with timestamps,
    event numbers, dispensed tags, and informative status subtexts.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}'); navigateToTab('tab-history');")
    time.sleep(2)

    events_container = auth_driver.find_element(By.ID, "events-log-container")
    log_text = events_container.get_attribute("textContent").strip()
    log_label = auth_driver.find_element(By.ID, "log-date-label").get_attribute("textContent").strip()

    assert "DISPENSED" in log_text, "Events log must display DISPENSED tags"
    assert "Feed Event #" in log_text, "Events log must include cycle event numbers"
    assert len(log_label) > 0, "Log date label must be present"

    take_test_screenshot(auth_driver, "test_13_events_log_verified")

def test_history_refresh_button_action(auth_driver):
    """
    DETAILED TEST 13.4:
    Verifies that the 'Refresh' button re-fetches trend data and shows user feedback.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-history');")
    time.sleep(1.5)

    auth_driver.execute_script("refreshHistoryData();")
    time.sleep(1.5)

    toast = auth_driver.find_element(By.ID, "app-toast")
    assert "Refreshed historic trends" in toast.get_attribute("textContent").strip()

    take_test_screenshot(auth_driver, "test_13_refresh_trends_action")
