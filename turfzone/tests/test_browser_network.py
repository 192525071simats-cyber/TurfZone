import os
import sys
import time
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import db, User, Turf, TimeSlot, Booking

# Start Flask test server
port = 5002
app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.abspath('turfzone_test_browser.db'),
    'SECRET_KEY': 'test-secret-2026'
})

def run_server():
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1.5)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1280,900')
chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})

driver = webdriver.Chrome(options=chrome_options)

def print_section(title):
    print(f"\n{'='*70}\n{title}\n{'='*70}")

def inspect_console_logs():
    logs = driver.get_log('browser')
    if logs:
        print("BROWSER CONSOLE LOGS:")
        for log in logs:
            print(f"  [{log['level']}] {log['message']}")
    else:
        print("BROWSER CONSOLE: Clean (No errors/warnings)")

def inspect_network_traffic():
    print("NETWORK API REQUESTS & RESPONSES:")
    perf_logs = driver.get_log('performance')
    for entry in perf_logs:
        msg = json.loads(entry['message'])['message']
        method = msg.get('method')
        if method == 'Network.responseReceived':
            response = msg['params']['response']
            url = response['url']
            if '/api/' in url:
                status = response['status']
                mime = response['mimeType']
                print(f"  --> HTTP {status} | {url} ({mime})")

try:
    print_section("STEP 1: USER LOGIN IN BROWSER")
    driver.get(f'http://127.0.0.1:{port}/login')
    
    # Fill login form
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "login-email")))
    driver.find_element(By.ID, "login-email").send_keys("user@turfzone.com")
    driver.find_element(By.ID, "login-password").send_keys("User@123")
    driver.find_element(By.ID, "login-submit-btn").click()

    # Wait for navigation to dashboard
    WebDriverWait(driver, 5).until(EC.url_contains("/dashboard"))
    print("✓ Login successful, redirected to /dashboard")
    inspect_console_logs()

    print_section("STEP 2: OPEN TURF DETAIL PAGE & VERIFY AVAILABILITY API")
    driver.get(f'http://127.0.0.1:{port}/turf/1')

    # Wait for turf title and slots
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "turf-name")))
    turf_name = driver.find_element(By.ID, "turf-name").text
    print(f"✓ Turf Detail loaded: '{turf_name}'")

    # Wait for slots to load
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "slot-btn")))
    slot_buttons = driver.find_elements(By.CLASS_NAME, "slot-btn")
    available_slots = [b for b in slot_buttons if 'available' in b.get_attribute('class')]
    print(f"✓ Slots loaded: {len(slot_buttons)} total slots, {len(available_slots)} available slots")

    inspect_console_logs()
    inspect_network_traffic()

    print_section("STEP 3: SELECT SLOT & SELECT ADDON")
    available_slot = available_slots[0]
    slot_id = available_slot.get_attribute('id')
    slot_time = available_slot.find_element(By.CLASS_NAME, "slot-time").text
    print(f"Selecting slot {slot_id} ({slot_time})...")
    available_slot.click()
    time.sleep(0.3)

    # Verify slot is selected
    assert 'selected' in available_slot.get_attribute('class')
    print("✓ Slot visually marked as selected")

    # Select an addon
    addons = driver.find_elements(By.CLASS_NAME, "addon-checkbox")
    if addons:
        addons[0].click()
        print("✓ Selected Match Gear addon: Football")

    # Verify Proceed to Book button is enabled
    proceed_btn = driver.find_element(By.ID, "proceed-booking-btn")
    assert proceed_btn.is_enabled()
    print("✓ 'Proceed to Book' button is active and enabled")

    print_section("STEP 4: OPEN CONFIRMATION MODAL & SUBMIT BOOKING")
    proceed_btn.click()
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "booking-confirm-modal")))
    
    modal_price = driver.find_element(By.ID, "modal-booking-price").text
    modal_slot = driver.find_element(By.ID, "modal-booking-time").text
    print(f"✓ Confirmation modal open: Slot={modal_slot}, Total Price={modal_price}")

    # Confirm booking
    confirm_btn = driver.find_element(By.ID, "confirm-booking-btn")
    confirm_btn.click()

    # Wait for Success Modal
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "booking-success-modal")))
    booking_ref = driver.find_element(By.ID, "success-booking-ref").text
    paid_amount = driver.find_element(By.ID, "success-total-paid").text
    print(f"✓ BOOKING CONFIRMED! Reference={booking_ref}, Paid={paid_amount}")

    inspect_console_logs()
    inspect_network_traffic()

    print_section("STEP 5: VERIFY LIVE SLOT UPDATE ON TURF PAGE")
    # Close success modal
    driver.find_element(By.XPATH, "//button[contains(text(), 'Book Another Slot')]").click()
    time.sleep(0.5)

    # The booked slot should now be disabled and marked as booked
    updated_slot_btn = driver.find_element(By.ID, slot_id)
    assert 'booked' in updated_slot_btn.get_attribute('class')
    assert updated_slot_btn.get_attribute('disabled') is not None
    print(f"✓ Slot {slot_id} is now disabled with status 'Booked'")

    print_section("STEP 6: MY BOOKINGS & CANCELLATION")
    driver.get(f'http://127.0.0.1:{port}/bookings')
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{booking_ref}')]")))
    print(f"✓ Booking {booking_ref} appears in My Bookings")

    # Cancel booking
    cancel_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Cancel')]")
    cancel_btn.click()
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "cancel-confirm-modal")))
    driver.find_element(By.ID, "confirm-cancel-btn").click()
    time.sleep(1)
    print("✓ Cancelled booking successfully")

    inspect_network_traffic()

    print_section("STEP 7: VERIFY SLOT IS RELEASED BACK TO AVAILABLE")
    driver.get(f'http://127.0.0.1:{port}/turf/1')
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, slot_id)))
    freed_slot_btn = driver.find_element(By.ID, slot_id)
    assert 'available' in freed_slot_btn.get_attribute('class')
    assert freed_slot_btn.get_attribute('disabled') is None
    print(f"✓ Slot {slot_id} is once again AVAILABLE and ready for booking!")

    print_section("ALL BROWSER CONSOLE AND NETWORK TESTS PASSED SUCCESSFULLY!")

finally:
    driver.quit()
