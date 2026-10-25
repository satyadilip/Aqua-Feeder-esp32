import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, take_test_screenshot

def test_status_dashboard_key_metrics_presence(auth_driver):
    """Verifies that all primary operational and status elements exist on Tab 1"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}');")
    time.sleep(1.5)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge")
    gauge_num = auth_driver.find_element(By.ID, "gauge-hero-num")
    gauge_pct = auth_driver.find_element(By.ID, "gauge-pct-badge")
    dispensed = auth_driver.find_element(By.ID, "dispensed-val-text")
    target = auth_driver.find_element(By.ID, "target-val-text")
    conn_val = auth_driver.find_element(By.ID, "connection-status-text")
    feed_dot = auth_driver.find_element(By.ID, "feed-status-dot")

    assert badge.is_displayed(), "State badge must be visible"
    assert len(dispensed.get_attribute("textContent").strip()) > 0, "Dispensed kg must have value"
    assert len(target.get_attribute("textContent").strip()) > 0, "Target kg must have value"
    assert conn_val.is_displayed(), "Connection status text must be visible"
    take_test_screenshot(auth_driver, "test_03_status_dashboard_metrics")

def test_offline_detection_for_feeder_01(auth_driver):
    """Verifies Feeder 01 shows NOT CONNECTED badge and offline state"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(1.5)

    badge_text = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()
    conn_text = auth_driver.find_element(By.ID, "connection-status-text").get_attribute("textContent").strip()

    assert badge_text == "NOT CONNECTED", f"Feeder 01 should show NOT CONNECTED, got '{badge_text}'"
    assert "Not Connected" in conn_text, f"Feeder 01 signal should show Not Connected, got '{conn_text}'"
    take_test_screenshot(auth_driver, "test_03_feeder01_offline_detected")

def test_tray_inspections_shortcut_card_on_status(auth_driver):
    """Verifies the Tray Inspections shortcut card exists on Status and can navigate to tab-traycheck"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    shortcut_desc = auth_driver.find_element(By.ID, "status-last-tray-check")
    assert shortcut_desc.is_displayed(), "Tray Inspections shortcut must be displayed"

    # Click the shortcut button to navigate to Tray Checks tab
    auth_driver.execute_script("navigateToTab('tab-traycheck');")
    time.sleep(1.5)

    active_tab = auth_driver.execute_script("return window.appState.activeTab;")
    assert active_tab == "tab-traycheck", f"Expected activeTab to be 'tab-traycheck', got '{active_tab}'"
    take_test_screenshot(auth_driver, "test_03_tray_inspections_shortcut_navigated")
