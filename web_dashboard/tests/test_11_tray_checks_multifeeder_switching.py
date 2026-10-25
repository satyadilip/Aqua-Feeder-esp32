import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, APP_URL, take_test_screenshot

def test_tray_checks_multifeeder_live_switching(auth_driver):
    """
    Verifies that:
    1. Switching between Feeder 01 and Feeder 02 live in the UI re-fetches and renders the correct
       tray checks dynamically (Feeder 01 has 2 checks, Feeder 02 has 1 check).
    2. Refreshing the browser while on Feeder 01 retains Feeder 01 and correctly displays its checks
       (never unexpectedly dropping to 0).
    3. Switching back to Feeder 02 live accurately updates the view to Feeder 02's check.
    """
    # 1. Switch to Feeder 02 and open Tray Check tab
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-traycheck');")
    time.sleep(3)

    title_02 = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    badge_02 = auth_driver.find_element(By.ID, "traycheck-count-badge").get_attribute("textContent").strip()
    count_02 = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()

    assert "Feeder 02" in title_02, f"Expected Feeder 02 in title, got: {title_02}"
    assert count_02 == "1", f"Feeder 02 should have 1 tray check, got: {count_02}"
    assert "1 CHECKS" in badge_02, f"Badge should be '1 CHECKS', got: {badge_02}"

    take_test_screenshot(auth_driver, "test_11_feeder02_tray_checks_live")

    # 2. Live switch to Feeder 01 without page reload
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(3)

    title_01 = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    badge_01 = auth_driver.find_element(By.ID, "traycheck-count-badge").get_attribute("textContent").strip()
    count_01 = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()

    assert "Feeder 01" in title_01, f"Expected Feeder 01 in title after live switch, got: {title_01}"
    assert count_01 == "2", f"Feeder 01 should have 2 tray checks, got: {count_01}"
    assert "2 CHECKS" in badge_01, f"Badge should be '2 CHECKS', got: {badge_01}"

    container_01 = auth_driver.find_element(By.ID, "tray-checks-log-container").get_attribute("textContent").strip()
    assert "VERIFIED" in container_01, "Feeder 01 container must show verified check items"

    take_test_screenshot(auth_driver, "test_11_feeder01_tray_checks_live_switch")

    # 3. Refresh page and verify Feeder 01 tray checks persist and do NOT drop to 0
    auth_driver.refresh()
    time.sleep(4)

    # Re-navigate to tray check tab after page reload
    auth_driver.execute_script("navigateToTab('tab-traycheck');")
    time.sleep(3)

    title_01_after_refresh = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    count_01_after_refresh = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()

    assert "Feeder 01" in title_01_after_refresh, f"Feeder 01 should persist after refresh, got: {title_01_after_refresh}"
    assert count_01_after_refresh == "2", f"Feeder 01 must show 2 checks after refresh (not 0), got: {count_01_after_refresh}"

    take_test_screenshot(auth_driver, "test_11_feeder01_tray_checks_persisted_after_refresh")

    # 4. Live switch back to Feeder 02
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}');")
    time.sleep(3)

    title_02_return = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    count_02_return = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()

    assert "Feeder 02" in title_02_return, f"Expected Feeder 02 on return, got: {title_02_return}"
    assert count_02_return == "1", f"Feeder 02 should return to 1 check, got: {count_02_return}"

    take_test_screenshot(auth_driver, "test_11_feeder02_tray_checks_switch_back")
