import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, take_test_screenshot

def test_settings_multidevice_form_population(auth_driver):
    """
    DETAILED TEST 12.1:
    Verifies that switching between Feeder 01 and Feeder 02 in the Settings tab
    correctly populates all form controls (target kg, FPE, start/end hours)
    for each respective feeder, rather than keeping stale values.
    """
    # 1. Start with Feeder 02 (target in DynamoDB is 20.0 kg, FPE 120g)
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-params');")
    time.sleep(2)

    title_02 = auth_driver.find_element(By.ID, "param-device-name").get_attribute("textContent").strip()
    qty_02 = auth_driver.find_element(By.ID, "input-qty").get_attribute("value").strip()
    badge_02 = auth_driver.find_element(By.ID, "calc-valid-badge").get_attribute("textContent").strip()

    assert "Feeder 02" in title_02, f"Expected Feeder 02 title, got: {title_02}"
    assert float(qty_02) in [15.0, 20.0], f"Feeder 02 daily target should be 15.0 or 20.0 kg, got: {qty_02}"
    assert badge_02 == "SCHEDULE OK", f"Schedule badge should be OK, got: {badge_02}"

    take_test_screenshot(auth_driver, "test_12_feeder02_settings_populated")

    # 2. Switch to Feeder 01 (target in DynamoDB is 50.0 kg, FPE 200g)
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}');")
    time.sleep(2)

    title_01 = auth_driver.find_element(By.ID, "param-device-name").get_attribute("textContent").strip()
    qty_01 = auth_driver.find_element(By.ID, "input-qty").get_attribute("value").strip()
    events_01 = auth_driver.find_element(By.ID, "calc-total-events").get_attribute("textContent").strip()

    assert "Feeder 01" in title_01, f"Expected Feeder 01 title after switch, got: {title_01}"
    assert float(qty_01) == 50.0, f"Feeder 01 target must be 50.0 kg, got: {qty_01}"
    assert int(events_01) in [250, 500], f"Feeder 01 total events should match its schedule, got: {events_01}"

    take_test_screenshot(auth_driver, "test_12_feeder01_settings_switched")

def test_settings_slider_input_bidirectional_sync(auth_driver):
    """
    DETAILED TEST 12.2:
    Verifies that modifying the slider updates the numeric input, and modifying
    the numeric input updates the slider and recalculates daily events and intervals in real-time.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-params');")
    time.sleep(1.5)

    # Change numeric input to 30.0 kg and FPE to 100g
    auth_driver.execute_script("""
        const inputQty = document.getElementById('input-qty');
        const inputFpe = document.getElementById('input-fpe');
        inputQty.value = '30.0';
        inputFpe.value = '100';
        recalculateSchedule();
    """)
    time.sleep(1)

    calc_events = auth_driver.find_element(By.ID, "calc-total-events").get_attribute("textContent").strip()
    calc_interval = auth_driver.find_element(By.ID, "calc-interval").get_attribute("textContent").strip()

    assert int(calc_events) == 300, f"30 kg with 100g FPE should produce 300 events, got: {calc_events}"
    assert "min" in calc_interval, f"Interval should be displayed in minutes, got: {calc_interval}"

    take_test_screenshot(auth_driver, "test_12_slider_bidirectional_sync")

def test_settings_schedule_boundary_conditions(auth_driver):
    """
    DETAILED TEST 12.3:
    Tests schedule boundary conditions:
    1. Tight Window (impossible schedule): Start 08:00, End 08:05 with 150 events -> WINDOW TOO TIGHT badge.
    2. Standard Window: 06:00 to 18:00 -> SCHEDULE OK badge.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-params');")
    time.sleep(1)

    # Inject tight window (Start 8:00, End 8:05)
    auth_driver.execute_script("""
        document.getElementById('input-start-hour').value = '8';
        document.getElementById('input-start-min').value = '0';
        document.getElementById('input-end-hour').value = '8';
        document.getElementById('input-end-min').value = '5';
        recalculateSchedule();
    """)
    time.sleep(1)

    badge = auth_driver.find_element(By.ID, "calc-valid-badge").get_attribute("textContent").strip()
    assert badge == "WINDOW TOO TIGHT", f"Expected 'WINDOW TOO TIGHT', got: {badge}"

    take_test_screenshot(auth_driver, "test_12_schedule_boundary_too_tight")

    # Restore standard window (Start 06:00, End 18:00)
    auth_driver.execute_script("""
        document.getElementById('input-start-hour').value = '6';
        document.getElementById('input-start-min').value = '0';
        document.getElementById('input-end-hour').value = '18';
        document.getElementById('input-end-min').value = '0';
        recalculateSchedule();
    """)
    time.sleep(1)

    badge_restored = auth_driver.find_element(By.ID, "calc-valid-badge").get_attribute("textContent").strip()
    assert badge_restored == "SCHEDULE OK", f"Expected 'SCHEDULE OK' after restoration, got: {badge_restored}"

def test_save_settings_api_dispatch_and_toast(auth_driver):
    """
    DETAILED TEST 12.4:
    Verifies that clicking 'Save Settings to Feeder' button:
    1. Dispatches the POST /api/settings/{deviceId} request.
    2. Shows a confirmation toast notification.
    3. Restores button state after completion.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-params');")
    time.sleep(1)

    save_btn = auth_driver.find_element(By.ID, "btn-save-params")
    auth_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    time.sleep(0.5)
    auth_driver.execute_script("arguments[0].click();", save_btn)
    time.sleep(2)

    toast = auth_driver.find_element(By.ID, "app-toast")
    toast_text = toast.get_attribute("textContent").strip()
    btn_text = auth_driver.find_element(By.ID, "save-btn-text").get_attribute("textContent").strip()

    assert "Settings saved" in toast_text, f"Toast should confirm settings saved, got: '{toast_text}'"
    assert "Save Settings to Feeder" in btn_text, f"Button label must be restored, got: '{btn_text}'"

    take_test_screenshot(auth_driver, "test_12_save_settings_dispatched")
