import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, take_test_screenshot

def test_rtc_clock_sync_button_and_dispatch(auth_driver):
    """Verifies that Sync Feeder Clock (RTC) control is present and dispatches time sync"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-troubleshoot');")
    time.sleep(1.5)

    btn_rtc = auth_driver.find_element(By.ID, "btn-sync-rtc")
    assert btn_rtc.is_displayed(), "Sync RTC button must be visible in Component Field Tests"

    # Dispatch RTC sync
    auth_driver.execute_script("syncFeederRTC();")
    time.sleep(2)

    status_desc = auth_driver.find_element(By.ID, "rtc-sync-status-desc").get_attribute("textContent").strip()
    assert "Sync Queued" in status_desc or "Epoch" in status_desc, (
        f"Expected 'Sync Queued' status after dispatching RTC sync, got '{status_desc}'"
    )
    take_test_screenshot(auth_driver, "test_07_rtc_sync_dispatched")

def test_motor_test_confirmation_banner(auth_driver):
    """Verifies that triggering a motor test displays the live waiting/confirmation banner"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-troubleshoot');")
    time.sleep(1)

    # Trigger Loader test
    auth_driver.execute_script("runHardwareTestAction('TEST_LOADER');")
    time.sleep(2)

    banner = auth_driver.find_element(By.ID, "test-confirmation-banner")
    title = auth_driver.find_element(By.ID, "test-confirm-title").get_attribute("textContent").strip()
    detail = auth_driver.find_element(By.ID, "test-confirm-detail").get_attribute("textContent").strip()

    assert banner.is_displayed(), "Test confirmation banner must become visible when test is run"
    assert "Waiting for Feeder" in title or "Confirmed" in title, (
        f"Banner title should show waiting/confirmation state, got '{title}'"
    )
    assert len(detail) > 0, "Banner detail must explain real LoRaWAN downlink execution"
    take_test_screenshot(auth_driver, "test_07_motor_test_confirmation_banner")
