import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, take_test_screenshot

def test_telemetry_injection_active_feeding(auth_driver):
    """DATA INJECTION SUCCESS: Injects live telemetry packet with active feeding metrics and verifies real-time UI updates"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    # Inject active feeding telemetry
    auth_driver.execute_script("""
    const dev = appState.devices.find(d => d.id === 'e072a1fffef5ba08');
    if (dev) {
      dev.connected = true;
      dev.status = 'ACTIVE';
      dev.dispensedKg = 8.4;
      dev.targetKg = 20.0;
      dev.currentEvent = 56;
      dev.totalEvents = 120;
      dev.feedAvailable = true;
      dev.statusFlags = 0;
      loadSelectedDeviceToUI();
    }
    """)
    time.sleep(1)

    dispensed = auth_driver.find_element(By.ID, "dispensed-val-text").get_attribute("textContent").strip()
    target = auth_driver.find_element(By.ID, "target-val-text").get_attribute("textContent").strip()
    burst_count = auth_driver.find_element(By.ID, "burst-count-text").get_attribute("textContent").strip()
    badge = auth_driver.find_element(By.ID, "feeder-state-badge").get_attribute("textContent").strip()

    assert "8.40" in dispensed, f"Dispensed text should be 8.40, got '{dispensed}'"
    assert "20.0" in target, f"Target text should be 20.0, got '{target}'"
    assert "56 / 120" in burst_count, f"Burst count should be 56 / 120, got '{burst_count}'"
    assert badge in ["ACTIVE", "FEEDING", "SCHEDULED", "STANDBY", "COMPLETED"], f"Badge should be valid state, got '{badge}'"

    take_test_screenshot(auth_driver, "test_08_telemetry_active_feeding_injected")

def test_telemetry_injection_feed_empty_alarm(auth_driver):
    """DATA INJECTION ALARM / FAILURE CASE: Injects FEED EMPTY sensor anomaly packet and verifies alarm state"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    # Inject hopper empty anomaly flag (0x08)
    auth_driver.execute_script("""
    const dev = appState.devices.find(d => d.id === 'e072a1fffef5ba08');
    if (dev) {
      dev.connected = true;
      dev.feedAvailable = false;
      dev.status = 'FEED EMPTY';
      dev.statusFlags = 0x08;
      loadSelectedDeviceToUI();
    }
    """)
    time.sleep(1)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge")
    badge_text = badge.get_attribute("textContent").strip()
    badge_class = badge.get_attribute("class")

    burst_sub = auth_driver.find_element(By.ID, "burst-count-sub").get_attribute("textContent").strip()
    next_sub = auth_driver.find_element(By.ID, "next-feed-sub").get_attribute("textContent").strip()

    assert "FEED EMPTY" in badge_text, f"State badge must indicate FEED EMPTY, got '{badge_text}'"
    assert "b-alert" in badge_class, f"State badge must have alert styling, got '{badge_class}'"
    assert "Refill Required" in burst_sub, f"Expected 'Refill Required' subtext, got '{burst_sub}'"
    assert "Hopper Empty" in next_sub, f"Expected 'Hopper Empty' subtext, got '{next_sub}'"

    take_test_screenshot(auth_driver, "test_08_telemetry_feed_empty_alarm_injected")

def test_telemetry_injection_proximity_paused_alarm(auth_driver):
    """DATA INJECTION ALARM / FAILURE CASE: Injects PROXIMITY PAUSE packet (0x10) and verifies safety pause state"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    # Inject proximity pause flag (0x10)
    auth_driver.execute_script("""
    const dev = appState.devices.find(d => d.id === 'e072a1fffef5ba08');
    if (dev) {
      dev.connected = true;
      dev.feedAvailable = true;
      dev.status = 'PAUSED';
      dev.statusFlags = 0x10;
      loadSelectedDeviceToUI();
    }
    """)
    time.sleep(1)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge")
    badge_text = badge.get_attribute("textContent").strip()
    badge_class = badge.get_attribute("class")

    burst_sub = auth_driver.find_element(By.ID, "burst-count-sub").get_attribute("textContent").strip()
    next_sub = auth_driver.find_element(By.ID, "next-feed-sub").get_attribute("textContent").strip()

    assert "PAUSED" in badge_text, f"State badge must indicate PAUSED, got '{badge_text}'"
    assert "b-alert" in badge_class, f"State badge must have alert styling, got '{badge_class}'"
    assert "Proximity / Feed Paused" in burst_sub, f"Expected Proximity / Feed Paused subtext, got '{burst_sub}'"
    assert "Feed Paused" in next_sub, f"Expected Feed Paused subtext, got '{next_sub}'"

    take_test_screenshot(auth_driver, "test_08_telemetry_proximity_paused_injected")

def test_telemetry_injection_offline_disconnect(auth_driver):
    """DATA INJECTION DISCONNECT CASE: Injects offline packet and verifies clean transition to disconnected state"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-status');")
    time.sleep(1)

    auth_driver.execute_script("""
    const dev = appState.devices.find(d => d.id === 'e072a1fffef5ba08');
    if (dev) {
      dev.connected = false;
      dev.status = 'NOT CONNECTED';
      loadSelectedDeviceToUI();
    }
    """)
    time.sleep(1)

    badge = auth_driver.find_element(By.ID, "feeder-state-badge")
    badge_text = badge.get_attribute("textContent").strip()
    conn_text = auth_driver.find_element(By.ID, "connection-status-text").get_attribute("textContent").strip()

    assert "NOT CONNECTED" in badge_text, f"Expected NOT CONNECTED badge, got '{badge_text}'"
    assert "Not Connected" in conn_text, f"Expected Not Connected text, got '{conn_text}'"

    take_test_screenshot(auth_driver, "test_08_telemetry_offline_disconnect_injected")
