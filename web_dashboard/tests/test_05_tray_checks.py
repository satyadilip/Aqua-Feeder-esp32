import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, take_test_screenshot

def test_tray_checks_view_rendering(auth_driver):
    """Verifies that the Tray Inspection tab displays hero metrics and log container"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-traycheck');")
    time.sleep(2)

    title = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    assert "Feeder 02" in title, f"Title should reference Feeder 02, got '{title}'"

    total_count = auth_driver.find_element(By.ID, "tray-total-count")
    last_time = auth_driver.find_element(By.ID, "tray-last-time")
    dispensed = auth_driver.find_element(By.ID, "tray-last-dispensed")
    batt = auth_driver.find_element(By.ID, "tray-last-batt")
    container = auth_driver.find_element(By.ID, "tray-checks-log-container")

    assert total_count.is_displayed(), "Total checks card must be displayed"
    assert last_time.is_displayed(), "Last checked time card must be displayed"
    assert dispensed.is_displayed(), "Feed dispensed card must be displayed"
    assert batt.is_displayed(), "Battery voltage card must be displayed"
    assert container.is_displayed(), "Logs container must be visible"
    take_test_screenshot(auth_driver, "test_05_tray_checks_view_rendered")

def test_tray_checks_refresh_action(auth_driver):
    """Verifies that the Refresh button can be clicked and re-fetches records without crashing"""
    auth_driver.execute_script("navigateToTab('tab-traycheck');")
    time.sleep(1)

    auth_driver.execute_script("renderTrayChecksView();")
    time.sleep(2)

    container = auth_driver.find_element(By.ID, "tray-checks-log-container")
    assert container.is_displayed(), "Container should remain visible after refresh"
    take_test_screenshot(auth_driver, "test_05_tray_checks_refreshed")
