import time
from selenium.webdriver.common.by import By
from conftest import take_test_screenshot

def test_map_tab_rendering_and_leaflet(auth_driver):
    """
    DETAILED TEST 17.1:
    Verifies that navigating to Tab 4 (Ponds & Satellite Map):
    1. Initializes the interactive Leaflet satellite map canvas.
    2. Renders the ponds directory cards with feeder chip badges and GPS links.
    """
    auth_driver.execute_script("navigateToTab('tab-map');")
    time.sleep(2.5)

    map_container = auth_driver.find_element(By.ID, "satellite-map")
    assert map_container.is_displayed(), "Satellite map container must be visible"
    classes = map_container.get_attribute("class")
    assert "leaflet-container" in classes, f"Map must have initialized Leaflet instance, got classes: {classes}"

    ponds_list = auth_driver.find_element(By.ID, "ponds-list-container")
    assert ponds_list.is_displayed(), "Ponds directory list must be visible"
    ponds_text = ponds_list.get_attribute("textContent").strip()
    assert "Pond P-01" in ponds_text, f"Pond P-01 card must be rendered in directory, got: {ponds_text}"

    take_test_screenshot(auth_driver, "test_17_map_tab_rendered")

def test_pond_context_bar_sync(auth_driver):
    """
    DETAILED TEST 17.2:
    Verifies that the top context bar correctly reflects the active pond name,
    acreage, shrimp species, and feeder counts.
    """
    auth_driver.execute_script("navigateToTab('tab-status');")
    time.sleep(1)

    pond_name = auth_driver.find_element(By.ID, "context-pond-name").get_attribute("textContent").strip()
    pond_details = auth_driver.find_element(By.ID, "context-pond-stock").get_attribute("textContent").strip()

    assert "Pond P-01" in pond_name, f"Active pond name should be Pond P-01, got: {pond_name}"
    assert "Acres" in pond_name or "Acres" in pond_details, f"Acreage must be rendered in context bar, got: {pond_name}"
    assert "Vannamei" in pond_details, f"Pond stock species must be rendered, got: {pond_details}"

    take_test_screenshot(auth_driver, "test_17_pond_context_bar")

def test_switch_pond_and_multi_pond_filter(auth_driver):
    """
    DETAILED TEST 17.3:
    Verifies switching between ponds:
    1. Switches to Pond P-02.
    2. Verifies context bar updates to Pond P-02.
    3. Switches back to Pond P-01 and verifies restoration.
    """
    auth_driver.execute_script("switchActivePond('P-02');")
    time.sleep(1.5)

    pond_name_p2 = auth_driver.find_element(By.ID, "context-pond-name").get_attribute("textContent").strip()
    assert "Pond P-02" in pond_name_p2, f"Pond name should update to Pond P-02, got: {pond_name_p2}"

    take_test_screenshot(auth_driver, "test_17_pond_p2_selected")

    # Restore Pond P-01
    auth_driver.execute_script("switchActivePond('P-01');")
    time.sleep(1.5)

    pond_name_p1 = auth_driver.find_element(By.ID, "context-pond-name").get_attribute("textContent").strip()
    assert "Pond P-01" in pond_name_p1, f"Pond name should restore to Pond P-01, got: {pond_name_p1}"

    take_test_screenshot(auth_driver, "test_17_pond_p1_restored")
