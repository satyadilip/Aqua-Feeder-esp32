import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

APP_URL = "http://lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f.s3-website-us-east-1.amazonaws.com"
SCREENSHOT_DIR = r"C:\Users\nsaty\.gemini\antigravity\brain\a76f981b-14fe-40c3-8b78-5503281f7539\test_screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

FEEDER_01_ID = "e072a1fffef6249c"
FEEDER_02_ID = "e072a1fffef5ba08"

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=430,932")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(4)
    return driver

@pytest.fixture(scope="function")
def driver():
    """Unauthenticated browser fixture"""
    d = create_driver()
    yield d
    try:
        d.quit()
    except Exception:
        pass

@pytest.fixture(scope="function")
def auth_driver():
    """Authenticated browser fixture pre-loaded with valid session"""
    d = create_driver()
    d.get(APP_URL)
    time.sleep(1)
    d.execute_script("""
        localStorage.setItem('aquacon_session_user', JSON.stringify({
            name: 'Ramesh Varma',
            phone: '9848012345',
            farm: 'Godavari Delta Shrimp Farm'
        }));
        location.reload();
    """)
    time.sleep(2)
    yield d
    try:
        d.quit()
    except Exception:
        pass

def take_test_screenshot(driver, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    return filepath
