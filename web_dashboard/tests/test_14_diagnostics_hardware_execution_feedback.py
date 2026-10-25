import time
from selenium.webdriver.common.by import By
from conftest import FEEDER_01_ID, FEEDER_02_ID, take_test_screenshot

def test_diagnostics_offline_feeder_guard(auth_driver):
    """
    DETAILED TEST 14.1:
    Verifies that for an OFFLINE feeder (Feeder 01):
    1. Diagnostics metrics reflect 'Not Connected' / 'No Signal' / 'Feeder Offline'.
    2. Attempting to run a motor test or RTC sync is safely blocked with an informative offline warning.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_01_ID}'); navigateToTab('tab-troubleshoot');")
    time.sleep(2)

    dev_title = auth_driver.find_element(By.ID, "troubleshoot-dev-name").get_attribute("textContent").strip()
    spreader_val = auth_driver.find_element(By.ID, "diag-spreader-val").get_attribute("textContent").strip()
    loader_val = auth_driver.find_element(By.ID, "diag-loader-val").get_attribute("textContent").strip()
    feed_val = auth_driver.find_element(By.ID, "diag-feed-val").get_attribute("textContent").strip()
    wireless_val = auth_driver.find_element(By.ID, "diag-wireless-val").get_attribute("textContent").strip()

    assert "Feeder 01" in dev_title, f"Expected Feeder 01, got: {dev_title}"
    assert spreader_val == "Not Connected", f"Spreader should show 'Not Connected', got: {spreader_val}"
    assert loader_val == "Not Connected", f"Loader should show 'Not Connected', got: {loader_val}"
    assert feed_val == "Not Connected", f"Feed stock should show 'Not Connected', got: {feed_val}"
    assert wireless_val == "Not Connected", f"Wireless should show 'Not Connected', got: {wireless_val}"

    # Attempt to trigger test on offline feeder
    auth_driver.execute_script("runHardwareTestAction('TEST_DISPENSER');")
    time.sleep(1)

    toast = auth_driver.find_element(By.ID, "app-toast")
    assert "offline" in toast.get_attribute("textContent").strip().lower(), "Toast must report device is offline"

    # Attempt to trigger RTC clock sync on offline feeder
    auth_driver.execute_script("syncFeederRTC();")
    time.sleep(1)

    toast2 = auth_driver.find_element(By.ID, "app-toast")
    assert "offline" in toast2.get_attribute("textContent").strip().lower(), "Toast must report device is offline for RTC sync"

    take_test_screenshot(auth_driver, "test_14_offline_diagnostics_guard")

def test_diagnostics_online_rtc_clock_sync(auth_driver):
    """
    DETAILED TEST 14.2:
    Verifies that for an ONLINE feeder (Feeder 02):
    Clicking 'Sync Time' dispatches the RTC epoch packet to the cloud backend and shows confirmation.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-troubleshoot');")
    time.sleep(2)

    auth_driver.execute_script("syncFeederRTC();")
    time.sleep(2)

    desc_el = auth_driver.find_element(By.ID, "rtc-sync-status-desc")
    btn_lbl = auth_driver.find_element(By.ID, "btn-sync-rtc-label")

    assert "Sync Queued" in desc_el.get_attribute("textContent").strip(), "RTC sync description should confirm queued status"
    assert "Queued" in btn_lbl.get_attribute("textContent").strip(), "Button label should update to Queued"

    take_test_screenshot(auth_driver, "test_14_online_rtc_clock_sync")

def test_diagnostics_motor_hardware_feedback_lifecycle(auth_driver):
    """
    DETAILED TEST 14.3:
    Simulates the full motor diagnostic lifecycle:
    1. Technician clicks 'Test Spreader Motor'.
    2. UI displays 'Waiting for Feeder to Execute...'.
    3. Simulated LoRaWAN sensor uplink arrives with physical current reading (380 mA).
    4. UI transitions to '✔ Confirmed PASSED!' displaying actual sensor telemetry.
    """
    auth_driver.execute_script(f"switchActiveDevice('{FEEDER_02_ID}'); navigateToTab('tab-troubleshoot');")
    time.sleep(1.5)

    # Trigger test and intercept status polling to simulate device confirmation
    simulation_script = """
    // Mock the command dispatch and status endpoint
    const origFetch = window.fetch;
    window._origFetch = origFetch;
    let pollCount = 0;

    window.fetch = async function(url, opts) {
        if (typeof url === 'string' && url.includes('/api/command/')) {
            return {
                ok: true,
                json: async () => ({ status: 'QUEUED', commandId: 'CMD-TEST-SPRD-99' })
            };
        }
        if (typeof url === 'string' && url.includes('/api/command-status/')) {
            pollCount++;
            if (pollCount >= 1) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        commands: [{ CommandId: 'CMD-TEST-SPRD-99', Status: 'CONFIRMED' }],
                        lastTestResult: {
                            TestType: 'TEST_DISPENSER',
                            Status: 'CONFIRMED',
                            Duration_s: 2,
                            Current_mA: 385,
                            Timestamp: Math.floor(Date.now() / 1000)
                        }
                    })
                };
            }
        }
        return origFetch(url, opts);
    };

    runHardwareTestAction('TEST_DISPENSER');
    """
    auth_driver.execute_script(simulation_script)
    time.sleep(4)

    banner_title = auth_driver.find_element(By.ID, "test-confirm-title").get_attribute("textContent").strip()
    spreader_val = auth_driver.find_element(By.ID, "diag-spreader-val").get_attribute("textContent").strip()

    assert "Confirmed PASSED" in banner_title, f"Banner must show Confirmed PASSED, got: {banner_title}"
    assert "385 mA" in spreader_val or "Confirmed" in spreader_val, f"Spreader val should show confirmed current, got: {spreader_val}"

    take_test_screenshot(auth_driver, "test_14_motor_feedback_confirmed")
