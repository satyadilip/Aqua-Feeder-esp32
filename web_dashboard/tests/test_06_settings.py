import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, safe_click, take_test_screenshot

def test_feed_settings_controls_rendered(auth_driver):
    """Verifies that Feed Settings inputs exist and math twin calculates valid schedule"""
    auth_driver.execute_script("navigateToTab('tab-params');")
    time.sleep(1)

    slider_qty = auth_driver.find_element(By.ID, "slider-qty")
    input_qty = auth_driver.find_element(By.ID, "input-qty")
    calc_badge = auth_driver.find_element(By.ID, "calc-valid-badge")
    total_events = auth_driver.find_element(By.ID, "calc-total-events")
    interval = auth_driver.find_element(By.ID, "calc-interval")
    btn_save = auth_driver.find_element(By.ID, "btn-save-params")

    assert slider_qty.is_displayed(), "Quantity slider must be visible"
    assert input_qty.is_displayed(), "Quantity input must be visible"
    assert "SCHEDULE OK" in calc_badge.get_attribute("textContent"), "Calculation badge should indicate SCHEDULE OK"
    assert int(total_events.get_attribute("textContent").strip()) > 0, "Total events must be positive integer"
    assert btn_save.is_displayed(), "Save settings button must be present"
    take_test_screenshot(auth_driver, "test_06_settings_controls_valid")

def test_feed_settings_validation_failure_too_tight(auth_driver):
    """VALIDATION FAILURE CASE: Setting impossible feeding schedule triggers 'WINDOW TOO TIGHT' rejection badge"""
    auth_driver.execute_script("navigateToTab('tab-params');")
    time.sleep(1)

    # Inject tight window: 100kg total with 100g FPE (=1000 events) in a 10-minute window (06:00 to 06:10)
    auth_driver.execute_script("""
    const inputQty = document.getElementById('input-qty');
    const inputFpe = document.getElementById('input-fpe');
    const inputSh = document.getElementById('input-start-hour');
    const inputSm = document.getElementById('input-start-min');
    const inputEh = document.getElementById('input-end-hour');
    const inputEm = document.getElementById('input-end-min');

    if (inputQty) inputQty.value = '100.0';
    if (inputFpe) inputFpe.value = '100';
    if (inputSh) inputSh.value = '6';
    if (inputSm) inputSm.value = '0';
    if (inputEh) inputEh.value = '6';
    if (inputEm) inputEm.value = '10';

    recalculateSchedule();
    """)
    time.sleep(1)

    calc_badge = auth_driver.find_element(By.ID, "calc-valid-badge")
    badge_text = calc_badge.get_attribute("textContent").strip()
    badge_class = calc_badge.get_attribute("class")

    assert "WINDOW TOO TIGHT" in badge_text, f"Expected WINDOW TOO TIGHT, got '{badge_text}'"
    assert "badge-invalid" in badge_class, f"Badge must have badge-invalid styling, got '{badge_class}'"
    take_test_screenshot(auth_driver, "test_06_settings_validation_failure_too_tight")

def test_save_settings_button_press_success(auth_driver):
    """BUTTON PRESS SUCCESS CASE: Submitting valid feed parameters dispatches save and triggers confirmation toast"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-params');")
    time.sleep(1)

    # Set realistic parameters: 20kg from 06:00 to 18:00
    auth_driver.execute_script("""
    const inputQty = document.getElementById('input-qty');
    const inputFpe = document.getElementById('input-fpe');
    const inputSh = document.getElementById('input-start-hour');
    const inputSm = document.getElementById('input-start-min');
    const inputEh = document.getElementById('input-end-hour');
    const inputEm = document.getElementById('input-end-min');

    if (inputQty) inputQty.value = '20.0';
    if (inputFpe) inputFpe.value = '120';
    if (inputSh) inputSh.value = '6';
    if (inputSm) inputSm.value = '0';
    if (inputEh) inputEh.value = '18';
    if (inputEm) inputEm.value = '0';

    recalculateSchedule();
    """)
    time.sleep(1)

    calc_badge = auth_driver.find_element(By.ID, "calc-valid-badge")
    assert "SCHEDULE OK" in calc_badge.get_attribute("textContent").strip()

    btn_save = auth_driver.find_element(By.ID, "btn-save-params")
    safe_click(auth_driver, btn_save)

    # Poll for confirmation toast up to 5 seconds
    toast_found = False
    for _ in range(10):
        time.sleep(0.5)
        toast = auth_driver.find_element(By.ID, "app-toast")
        toast_text = toast.get_attribute("textContent").strip()
        if "Settings saved" in toast_text:
            toast_found = True
            break

    assert toast_found, f"Expected 'Settings saved' toast notification, got '{toast_text}'"
    take_test_screenshot(auth_driver, "test_06_save_settings_button_success")
