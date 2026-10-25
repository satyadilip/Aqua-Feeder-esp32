import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, take_test_screenshot

def test_feeder_1_selection_and_persistence_on_refresh(auth_driver):
    """
    CRITICAL REGRESSION TEST:
    Verifies that when Feeder 1 is selected, refreshing the page MUST KEEP Feeder 1 selected
    and MUST NOT default back to Feeder 2.
    """
    # 1. Explicitly select Feeder 1
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(1.5)

    # Verify Feeder 1 is active in appState and UI
    selected_id_before = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_id_before == FEEDER_01_ID, f"Expected selectedDeviceId to be {FEEDER_01_ID}, got {selected_id_before}"

    device_name_before = auth_driver.find_element(By.ID, "current-device-name").get_attribute("textContent").strip()
    assert "Feeder 01" in device_name_before, f"Expected 'Feeder 01' in device title, got '{device_name_before}'"

    # Verify localStorage saved the selection
    saved_ls = auth_driver.execute_script("return localStorage.getItem('aquacon_selected_device');")
    assert saved_ls == FEEDER_01_ID, f"localStorage 'aquacon_selected_device' should be {FEEDER_01_ID}, got {saved_ls}"
    take_test_screenshot(auth_driver, "test_02_feeder1_selected_before_refresh")

    # 2. Perform page refresh
    auth_driver.refresh()
    time.sleep(3)

    # 3. Assert Feeder 1 remains selected after refresh
    selected_id_after = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_id_after == FEEDER_01_ID, (
        f"REGRESSION DETECTED: Page refresh reset selectedDeviceId to {selected_id_after}! "
        f"It must remain {FEEDER_01_ID}."
    )

    device_name_after = auth_driver.find_element(By.ID, "current-device-name").get_attribute("textContent").strip()
    assert "Feeder 01" in device_name_after, (
        f"REGRESSION DETECTED: Device header showed '{device_name_after}' after reload, expected Feeder 01!"
    )
    take_test_screenshot(auth_driver, "test_02_feeder1_persisted_after_refresh")

def test_feeder_2_selection_and_persistence_on_refresh(auth_driver):
    """
    Verifies that switching to Feeder 2 also persists cleanly across refreshes.
    """
    # 1. Switch to Feeder 2
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}');")
    time.sleep(1.5)

    selected_id = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_id == FEEDER_02_ID, f"Expected {FEEDER_02_ID}, got {selected_id}"

    device_name = auth_driver.find_element(By.ID, "current-device-name").get_attribute("textContent").strip()
    assert "Feeder 02" in device_name, f"Expected 'Feeder 02', got '{device_name}'"

    # 2. Refresh
    auth_driver.refresh()
    time.sleep(3)

    # 3. Assert Feeder 2 remains selected
    selected_after = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_after == FEEDER_02_ID, f"Expected {FEEDER_02_ID} to persist after reload, got {selected_after}"

    name_after = auth_driver.find_element(By.ID, "current-device-name").get_attribute("textContent").strip()
    assert "Feeder 02" in name_after, f"Expected 'Feeder 02' in title, got '{name_after}'"
    take_test_screenshot(auth_driver, "test_02_feeder2_persisted_after_refresh")

def test_device_pill_click_and_active_indicator(auth_driver):
    """
    Verifies clicking the device pill buttons in the pond context row switches device and updates active styling
    """
    pills = auth_driver.find_elements(By.CSS_SELECTOR, "#pond-devices-pills .story-item")
    assert len(pills) >= 2, f"There should be at least 2 device pills in Pond P-01, found {len(pills)}"

    # Click first pill (Feeder 01)
    pills[0].click()
    time.sleep(1)

    active_pill = auth_driver.find_element(By.CSS_SELECTOR, "#pond-devices-pills .story-item.active-story")
    assert active_pill is not None, "One device pill must have 'active-story' class"

    selected_dev = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_dev == FEEDER_01_ID, f"Clicking first pill should select {FEEDER_01_ID}"

    # Click second pill (Feeder 02)
    pills = auth_driver.find_elements(By.CSS_SELECTOR, "#pond-devices-pills .story-item")
    pills[1].click()
    time.sleep(1)

    selected_dev2 = auth_driver.execute_script("return window.appState.selectedDeviceId;")
    assert selected_dev2 == FEEDER_02_ID, f"Clicking second pill should select {FEEDER_02_ID}"
    take_test_screenshot(auth_driver, "test_02_device_pills_interactive")
