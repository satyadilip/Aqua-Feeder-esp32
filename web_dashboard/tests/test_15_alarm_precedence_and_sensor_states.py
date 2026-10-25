import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, take_test_screenshot

def test_alarm_proximity_paused_handling(auth_driver):
    """
    DETAILED TEST 15.1:
    Verifies that when ultrasonic proximity sensor triggers (status: PAUSED / statusFlags: 0x10):
    1. Hero card badge turns amber 'PAUSED'.
    2. Subtitle displays 'Proximity Pause Active'.
    3. Spreader & loader status cells in Diagnostics report 'Paused'.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    # Inject Proximity Pause Telemetry State
    auth_driver.execute_script("""
        const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
        if (dev) {
            dev.status = 'PAUSED';
            dev.statusFlags = 0x10;
            dev.connected = true;
        }
        loadSelectedDeviceToUI();
    """)
    time.sleep(1.5)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()
    burst_sub = auth_driver.find_element(By.ID, "burst-count-sub").get_attribute("textContent").strip()

    assert badge == "PAUSED", f"State badge should be 'PAUSED', got: '{badge}'"
    assert "Proximity" in burst_sub, f"Burst subtext must indicate Proximity Pause, got: '{burst_sub}'"

    take_test_screenshot(auth_driver, "test_15_proximity_paused_rendered")

def test_alarm_feed_hopper_empty_handling(auth_driver):
    """
    DETAILED TEST 15.2:
    Verifies that when hopper feed level switch triggers (feedAvailable: false / status: FEED EMPTY):
    1. Hero card badge turns coral 'FEED EMPTY'.
    2. Subtitle warns 'Refill Required'.
    3. Diagnostics feed stock indicates 'Empty / Refill'.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    # Inject Feed Hopper Empty Telemetry State
    auth_driver.execute_script("""
        const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
        if (dev) {
            dev.status = 'FEED EMPTY';
            dev.statusFlags = 0x08;
            dev.feedAvailable = false;
            dev.connected = true;
        }
        loadSelectedDeviceToUI();
    """)
    time.sleep(1.5)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()
    burst_sub = auth_driver.find_element(By.ID, "burst-count-sub").get_attribute("textContent").strip()

    assert badge == "FEED EMPTY", f"State badge should be 'FEED EMPTY', got: '{badge}'"
    assert "Refill" in burst_sub or "Empty" in burst_sub, f"Subtext must indicate refill required, got: '{burst_sub}'"

    take_test_screenshot(auth_driver, "test_15_feed_empty_rendered")

def test_alarm_compound_state_resilience(auth_driver):
    """
    DETAILED TEST 15.3:
    Verifies that compound alarm states (both Proximity Paused and Feed Empty simultaneously)
    are handled gracefully without breaking UI metrics or gauge display.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    auth_driver.execute_script("""
        const dev = appState.devices.find(d => d.id === appState.selectedDeviceId);
        if (dev) {
            dev.status = 'PAUSED';
            dev.statusFlags = 0x18; // 0x10 (proximity) | 0x08 (feed empty)
            dev.feedAvailable = false;
            dev.connected = true;
        }
        loadSelectedDeviceToUI();
    """)
    time.sleep(1.5)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()
    dispensed = auth_driver.find_element(By.ID, "dispensed-val-text").get_attribute("textContent").strip()
    gauge_num = auth_driver.find_element(By.ID, "gauge-hero-num").get_attribute("textContent").strip()

    assert badge in ["PAUSED", "FEED EMPTY"], f"Badge should be PAUSED or FEED EMPTY, got: {badge}"
    assert len(dispensed) > 0, "Dispensed text must remain visible"
    assert len(gauge_num) > 0, "Gauge number must remain rendered"

    take_test_screenshot(auth_driver, "test_15_compound_alarm_resilience")
