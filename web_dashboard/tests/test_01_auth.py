import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from conftest import APP_URL, take_test_screenshot

def test_login_screen_renders(driver):
    """Verifies that unauthenticated user sees the Auth Screen with sign in and register tabs"""
    driver.get(APP_URL)
    time.sleep(1)
    
    # Clear any residual session
    driver.execute_script("localStorage.clear(); location.reload();")
    time.sleep(2)

    auth_screen = driver.find_element(By.ID, "screen-auth")
    assert auth_screen.is_displayed(), "Auth screen should be displayed for new user"

    phone_input = driver.find_element(By.ID, "auth-phone-input")
    pass_input = driver.find_element(By.ID, "auth-pw-input")
    submit_btn = driver.find_element(By.ID, "btn-login-submit")

    assert phone_input.is_displayed(), "Phone input must be visible"
    assert pass_input.is_displayed(), "Password input must be visible"
    assert submit_btn.is_displayed(), "Sign in button must be visible"
    take_test_screenshot(driver, "test_01_auth_screen_rendered")

def test_login_failure_empty_credentials(driver):
    """FAILURE CASE: Clicking Sign In with empty fields must trigger validation error"""
    driver.get(APP_URL)
    driver.execute_script("localStorage.clear();")
    time.sleep(1)

    phone_input = driver.find_element(By.ID, "auth-phone-input")
    pass_input = driver.find_element(By.ID, "auth-pw-input")
    submit_btn = driver.find_element(By.ID, "btn-login-submit")

    # Clear both inputs
    phone_input.clear()
    pass_input.clear()
    
    # Button press with empty fields
    submit_btn.click()
    time.sleep(1)

    alert_box = driver.find_element(By.ID, "auth-alert-box")
    assert alert_box.is_displayed(), "Validation alert box must become visible on empty submission"
    
    alert_text = alert_box.get_attribute("textContent").strip()
    assert "Please enter mobile number and password" in alert_text, (
        f"Expected empty credentials warning, got '{alert_text}'"
    )
    assert "error" in alert_box.get_attribute("class"), "Alert box should have error styling class"
    
    # Verify main shell remains inaccessible
    main_shell = driver.find_element(By.ID, "main-app-shell")
    assert not main_shell.is_displayed(), "Main app shell must stay hidden when credentials are blank"
    take_test_screenshot(driver, "test_01_login_failure_empty_credentials")

def test_login_failure_invalid_credentials(driver):
    """FAILURE CASE: Clicking Sign In with invalid/unregistered credentials must display error and block access"""
    driver.get(APP_URL)
    driver.execute_script("localStorage.clear();")
    time.sleep(1)

    phone_input = driver.find_element(By.ID, "auth-phone-input")
    pass_input = driver.find_element(By.ID, "auth-pw-input")
    submit_btn = driver.find_element(By.ID, "btn-login-submit")

    phone_input.clear()
    phone_input.send_keys("9876543210")
    pass_input.clear()
    pass_input.send_keys("wrong_password_123")
    
    # Button press with invalid credentials
    submit_btn.click()
    time.sleep(2)

    alert_box = driver.find_element(By.ID, "auth-alert-box")
    assert alert_box.is_displayed(), "Alert box must appear on invalid login attempt"
    
    alert_text = alert_box.get_attribute("textContent").strip()
    assert any(term in alert_text for term in ["Invalid", "Unable to connect", "error", "failed"]), (
        f"Expected invalid credentials or connection error message, got '{alert_text}'"
    )

    # Verify main shell remains inaccessible
    main_shell = driver.find_element(By.ID, "main-app-shell")
    assert not main_shell.is_displayed(), "Main app shell must not open on invalid credentials"
    take_test_screenshot(driver, "test_01_login_failure_invalid_credentials")

def test_valid_login_flow(driver):
    """SUCCESS CASE: Entering valid technician credentials unlocks the main farm shell"""
    driver.get(APP_URL)
    driver.execute_script("localStorage.clear();")
    time.sleep(1)

    phone_input = driver.find_element(By.ID, "auth-phone-input")
    pass_input = driver.find_element(By.ID, "auth-pw-input")
    submit_btn = driver.find_element(By.ID, "btn-login-submit")

    phone_input.clear()
    phone_input.send_keys("9000420999")
    pass_input.clear()
    pass_input.send_keys("admin")
    
    # Button press with valid credentials
    submit_btn.click()
    time.sleep(2.5)

    main_shell = driver.find_element(By.ID, "main-app-shell")
    assert main_shell.is_displayed(), "Main shell should be visible after successful login"

    user_name = driver.find_element(By.ID, "sys-farm-name").get_attribute("textContent").strip()
    assert len(user_name) > 0, "Farm header name should be populated"
    take_test_screenshot(driver, "test_01_valid_login_success")

def test_session_persistence_across_reload(auth_driver):
    """SUCCESS CASE: User session token in localStorage keeps session active across page reload"""
    main_shell = auth_driver.find_element(By.ID, "main-app-shell")
    assert main_shell.is_displayed(), "Main shell should be active on initial load"

    auth_driver.refresh()
    time.sleep(2.5)

    main_shell_after = auth_driver.find_element(By.ID, "main-app-shell")
    assert main_shell_after.is_displayed(), "Main shell must remain active after page reload"
    take_test_screenshot(driver=auth_driver, name="test_01_session_persisted")
