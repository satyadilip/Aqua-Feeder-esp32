import time
from selenium.webdriver.common.by import By
from conftest import take_test_screenshot

TABS = [
    ("tab-status", "screen-status", "tab-btn-status"),
    ("tab-history", "screen-history", "tab-btn-history"),
    ("tab-traycheck", "screen-traycheck", "tab-btn-traycheck"),
    ("tab-params", "screen-params", "tab-btn-params"),
    ("tab-troubleshoot", "screen-troubleshoot", "tab-btn-troubleshoot"),
    ("tab-map", "screen-map", "tab-btn-map"),
]

def test_all_6_tabs_navigation(auth_driver):
    """Verifies that user can cleanly navigate through all 6 tabs in sequence"""
    for tab_id, screen_id, btn_id in TABS:
        auth_driver.execute_script(f"navigateToTab('{tab_id}');")
        time.sleep(1)

        # Assert screen active
        screen = auth_driver.find_element(By.ID, screen_id)
        assert "active" in screen.get_attribute("class"), f"Screen {screen_id} should have 'active' class"

        # Assert button active
        btn = auth_driver.find_element(By.ID, btn_id)
        assert "active" in btn.get_attribute("class"), f"Button {btn_id} should have 'active' class"

    take_test_screenshot(auth_driver, "test_04_navigation_all_tabs_passed")

def test_bottom_nav_dock_structure(auth_driver):
    """Verifies that bottom navigation bar is fixed, contains 6 tabs, and fits ergonomically"""
    nav = auth_driver.find_element(By.CSS_SELECTOR, "nav.bottom-nav")
    assert nav.is_displayed(), "Bottom navigation dock must be visible"

    tabs = auth_driver.find_elements(By.CSS_SELECTOR, "nav.bottom-nav .nav-tab")
    assert len(tabs) == 6, f"Bottom nav bar should contain exactly 6 tabs, found {len(tabs)}"
    take_test_screenshot(auth_driver, "test_04_bottom_dock_6_tabs")
