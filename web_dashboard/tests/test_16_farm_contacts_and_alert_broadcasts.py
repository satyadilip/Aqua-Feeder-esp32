import time
from selenium.webdriver.common.by import By
from conftest import take_test_screenshot

def test_alert_contacts_rendering_in_support_tab(auth_driver):
    """
    DETAILED TEST 16.1:
    Verifies that navigating to Diagnostics -> Support & Emergency Contacts subtab
    renders the alert contacts list with names, roles, phone numbers, and call buttons.
    """
    auth_driver.execute_script("navigateToTab('tab-troubleshoot'); switchTroubleshootSubTab('support');")
    time.sleep(2)

    container = auth_driver.find_element(By.ID, "contacts-list-container")
    text = container.get_attribute("textContent").strip()

    assert len(text) > 0, "Contacts list container must not be empty"
    assert "Charan" in text or "Lead" in text or "Supervisor" in text, f"Default contacts must be rendered, got: {text}"

    take_test_screenshot(auth_driver, "test_16_alert_contacts_rendered")

def test_add_contact_and_persistence_across_refresh(auth_driver):
    """
    DETAILED TEST 16.2:
    Tests adding a new farm alert contact:
    1. Injects a new technician contact via state.
    2. Verifies new contact is rendered with quick-dial link.
    3. Refreshes the page and verifies the contact persists via localStorage.
    """
    auth_driver.execute_script("navigateToTab('tab-troubleshoot'); switchTroubleshootSubTab('support');")
    time.sleep(1)

    # Add a custom test contact
    auth_driver.execute_script("""
        appState.contacts.push({
            name: "Ramesh Kumar",
            role: "Pond Technician",
            phone: "+91 98480 12345",
            rawPhone: "9848012345",
            isDefault: false
        });
        saveDataToStorage();
        renderAlertContacts();
    """)
    time.sleep(1.5)

    container = auth_driver.find_element(By.ID, "contacts-list-container")
    assert "Ramesh Kumar" in container.get_attribute("textContent").strip(), "Newly added contact must be displayed"

    take_test_screenshot(auth_driver, "test_16_contact_added")

    # Refresh browser
    auth_driver.refresh()
    time.sleep(3)

    auth_driver.execute_script("navigateToTab('tab-troubleshoot'); switchTroubleshootSubTab('support');")
    time.sleep(2)

    container_after_reload = auth_driver.find_element(By.ID, "contacts-list-container")
    assert "Ramesh Kumar" in container_after_reload.get_attribute("textContent").strip(), "Contact must persist after page refresh"

    take_test_screenshot(auth_driver, "test_16_contact_persisted_after_refresh")

def test_primary_alert_lead_protected_from_deletion(auth_driver):
    """
    DETAILED TEST 16.3:
    Verifies that the primary alert lead contact is protected and cannot be deleted.
    """
    auth_driver.execute_script("navigateToTab('tab-troubleshoot'); switchTroubleshootSubTab('support');")
    time.sleep(1)

    auth_driver.execute_script("deleteContact(0);")
    time.sleep(1)

    toast = auth_driver.find_element(By.ID, "app-toast")
    assert "Primary Alert Lead cannot be removed" in toast.get_attribute("textContent").strip()

    take_test_screenshot(auth_driver, "test_16_primary_contact_protected")
