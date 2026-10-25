import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, safe_click, take_test_screenshot

def test_remote_start_feed_button_failure_offline(auth_driver):
    """BUTTON PRESS FAILURE CASE: Clicking Start Feed on offline Feeder 01 must be blocked with an alert toast"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}'); navigateToTab('tab-status');")
    time.sleep(1.5)

    btn_start = auth_driver.find_element(By.ID, "btn-remote-start")
    assert btn_start.is_displayed(), "Start Feed button must be visible"

    # Click Start Feed on offline device using safe_click to avoid bottom-nav interception
    safe_click(auth_driver, btn_start)
    time.sleep(1)

    toast = auth_driver.find_element(By.ID, "app-toast")
    toast_text = toast.get_attribute("textContent").strip()
    assert "Cannot start" in toast_text and "not connected" in toast_text, (
        f"Expected offline feed trigger rejection toast, got '{toast_text}'"
    )
    take_test_screenshot(auth_driver, "test_09_remote_start_feed_offline_blocked")

def test_remote_start_feed_button_success_online(auth_driver):
    """BUTTON PRESS SUCCESS CASE: Clicking Start Feed on connected Feeder 02 triggers feed burst and cycle update"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1.5)

    # Automatically accept browser confirmation dialog for automated test
    auth_driver.execute_script("window.confirm = function() { return true; };")

    btn_start = auth_driver.find_element(By.ID, "btn-remote-start")
    safe_click(auth_driver, btn_start)
    time.sleep(1.5)

    toast = auth_driver.find_element(By.ID, "app-toast")
    toast_text = toast.get_attribute("textContent").strip()
    assert "triggered" in toast_text or "Feed event" in toast_text, (
        f"Expected feed burst triggered confirmation toast, got '{toast_text}'"
    )

    burst_count = auth_driver.find_element(By.ID, "burst-count-text").get_attribute("textContent").strip()
    assert int(burst_count.split("/")[0].strip()) > 0, "Feed event count should be positive"

    take_test_screenshot(auth_driver, "test_09_remote_start_feed_online_success")
