import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_02_ID, take_test_screenshot

def test_tray_checks_view_rendering(auth_driver):
    """Verifies that the Tray Inspection tab displays hero metrics and log container"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-traycheck');")
    time.sleep(2)

    title = auth_driver.find_element(By.ID, "traycheck-feeder-title").get_attribute("textContent").strip()
    assert "Feeder 02" in title, f"Title should reference Feeder 02, got '{title}'"

    total_count = auth_driver.find_element(By.ID, "tray-total-count")
    last_time = auth_driver.find_element(By.ID, "tray-last-time")
    dispensed = auth_driver.find_element(By.ID, "tray-last-dispensed")
    batt = auth_driver.find_element(By.ID, "tray-last-batt")
    container = auth_driver.find_element(By.ID, "tray-checks-log-container")

    assert total_count.is_displayed(), "Total checks card must be displayed"
    assert last_time.is_displayed(), "Last checked time card must be displayed"
    assert dispensed.is_displayed(), "Feed dispensed card must be displayed"
    assert batt.is_displayed(), "Battery voltage card must be displayed"
    assert container.is_displayed(), "Logs container must be visible"
    take_test_screenshot(auth_driver, "test_05_tray_checks_view_rendered")

def test_tray_checks_refresh_action(auth_driver):
    """Verifies that the Refresh button re-fetches records without error"""
    auth_driver.execute_script("navigateToTab('tab-traycheck');")
    time.sleep(1)

    auth_driver.execute_script("renderTrayChecksView();")
    time.sleep(2)

    container = auth_driver.find_element(By.ID, "tray-checks-log-container")
    assert container.is_displayed(), "Container should remain visible after refresh"
    take_test_screenshot(auth_driver, "test_05_tray_checks_refreshed")

def test_tray_checks_data_injection_success(auth_driver):
    """DATA INJECTION SUCCESS: Injects simulated physical tray check records and verifies UI cards & log items"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-traycheck');")
    time.sleep(1)

    # Inject mock data into renderTrayChecksView by mocking fetch for /api/tray-checks
    injection_script = """
    const mockChecks = [
      {
        Timestamp: Math.floor(Date.now() / 1000) - 300,
        FeedDispensed_g: 3850,
        CurrentEvent: 26,
        Battery_V: 4.15
      },
      {
        Timestamp: Math.floor(Date.now() / 1000) - 7200,
        FeedDispensed_g: 1900,
        CurrentEvent: 13,
        Battery_V: 4.18
      }
    ];

    const origFetch = window.fetch;
    window._origFetch = origFetch;
    window.fetch = async function(url, opts) {
      if (typeof url === 'string' && url.includes('/api/tray-checks')) {
        return {
          ok: true,
          json: async () => ({ status: 'success', trayChecks: mockChecks })
        };
      }
      return origFetch(url, opts);
    };

    renderTrayChecksView();
    """
    auth_driver.execute_script(injection_script)
    time.sleep(1.5)

    total_count = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()
    dispensed = auth_driver.find_element(By.ID, "tray-last-dispensed").get_attribute("textContent").strip()
    batt = auth_driver.find_element(By.ID, "tray-last-batt").get_attribute("textContent").strip()
    container = auth_driver.find_element(By.ID, "tray-checks-log-container")
    container_text = container.get_attribute("textContent").strip()

    assert total_count == "2", f"Total checks should be 2 after injection, got '{total_count}'"
    assert "3.85" in dispensed, f"Latest dispensed feed should show 3.85 kg, got '{dispensed}'"
    assert "4.15" in batt, f"Latest battery should show 4.15 V, got '{batt}'"
    assert "VERIFIED" in container_text, "Event log must contain VERIFIED status badges"
    assert "3.85 kg" in container_text, "Event log entry must render dispensed weight"

    take_test_screenshot(auth_driver, "test_05_tray_checks_data_injected_success")

def test_tray_checks_empty_state_handling(auth_driver):
    """DATA INJECTION EMPTY/FAILURE STATE: Injects zero tray checks and verifies clean empty-state placeholder"""
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-traycheck');")
    time.sleep(1)

    injection_script = """
    window.fetch = async function(url, opts) {
      if (typeof url === 'string' && url.includes('/api/tray-checks')) {
        return {
          ok: true,
          json: async () => ({ status: 'success', trayChecks: [] })
        };
      }
      if (window._origFetch) return window._origFetch(url, opts);
      return window.fetch(url, opts);
    };

    renderTrayChecksView();
    """
    auth_driver.execute_script(injection_script)
    time.sleep(1.5)

    total_count = auth_driver.find_element(By.ID, "tray-total-count").get_attribute("textContent").strip()
    last_sub = auth_driver.find_element(By.ID, "tray-last-sub").get_attribute("textContent").strip()
    container_text = auth_driver.find_element(By.ID, "tray-checks-log-container").get_attribute("textContent").strip()

    assert total_count == "0", f"Total checks should be 0, got '{total_count}'"
    assert "No checks logged" in last_sub, f"Last check sub should show 'No checks logged', got '{last_sub}'"
    assert "No Tray Inspections Recorded Yet" in container_text, "Container must render friendly empty placeholder"

    take_test_screenshot(auth_driver, "test_05_tray_checks_empty_state")
