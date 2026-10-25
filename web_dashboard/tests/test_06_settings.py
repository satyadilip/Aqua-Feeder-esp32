import time
from selenium.webdriver.common.by import By
from conftest import take_test_screenshot

def test_feed_settings_controls_and_calculation_twin(auth_driver):
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
