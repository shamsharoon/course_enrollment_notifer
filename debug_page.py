"""
Debug script to inspect the Ontario Tech registration page
and find the correct selectors for the course search field
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

# Your config
BASE_URL = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/registration/registerPostSignIn?mode=registration&mepCode=UOIT"
USERNAME = "100911720"
PASSWORD = "$hamS1245"

def debug_registration_page():
    print("🔍 Debugging Ontario Tech Registration Page")
    print("=" * 50)
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--headless=new")  # Comment out to see the page
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"📍 Navigating to: {BASE_URL}")
        driver.get(BASE_URL)
        
        # Wait for page to load
        time.sleep(5)
        
        print(f"🌐 Current URL: {driver.current_url}")
        print(f"📄 Page Title: {driver.title}")
        
        # Check if login is needed
        if "login" in driver.current_url.lower():
            print("🔐 Login page detected, attempting login...")
            
            # Try to find and fill login form
            try:
                username_field = driver.find_element(By.NAME, "username")
                password_field = driver.find_element(By.NAME, "password") 
                
                username_field.send_keys(USERNAME)
                password_field.send_keys(PASSWORD)
                
                login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                login_button.click()
                
                print("✅ Login submitted, waiting...")
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Login failed: {e}")
        
        print(f"🌐 Final URL: {driver.current_url}")
        print(f"📄 Final Title: {driver.title}")
        
        # Wait for registration page elements
        time.sleep(5)
        
        # Get all input fields
        print("\n🔍 FINDING ALL INPUT FIELDS:")
        print("-" * 30)
        
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, input_elem in enumerate(all_inputs):
            try:
                input_type = input_elem.get_attribute("type") or "text"
                input_name = input_elem.get_attribute("name") or "N/A"
                input_id = input_elem.get_attribute("id") or "N/A" 
                input_placeholder = input_elem.get_attribute("placeholder") or "N/A"
                input_class = input_elem.get_attribute("class") or "N/A"
                is_visible = input_elem.is_displayed()
                
                print(f"Input {i+1}: type='{input_type}' name='{input_name}' id='{input_id}' placeholder='{input_placeholder}' class='{input_class}' visible={is_visible}")
                
            except Exception as e:
                print(f"Input {i+1}: Error getting attributes - {e}")
        
        # Get all text areas
        print("\n🔍 FINDING ALL TEXTAREA FIELDS:")
        print("-" * 30)
        
        all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for i, textarea in enumerate(all_textareas):
            try:
                textarea_name = textarea.get_attribute("name") or "N/A"
                textarea_id = textarea.get_attribute("id") or "N/A"
                textarea_placeholder = textarea.get_attribute("placeholder") or "N/A"
                textarea_class = textarea.get_attribute("class") or "N/A"
                is_visible = textarea.is_displayed()
                
                print(f"Textarea {i+1}: name='{textarea_name}' id='{textarea_id}' placeholder='{textarea_placeholder}' class='{textarea_class}' visible={is_visible}")
                
            except Exception as e:
                print(f"Textarea {i+1}: Error getting attributes - {e}")
        
        # Look for elements containing "course" or "subject"
        print("\n🔍 SEARCHING FOR 'COURSE' OR 'SUBJECT' RELATED ELEMENTS:")
        print("-" * 50)
        
        # Get page source for text search
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find elements with course/subject in text
        course_elements = soup.find_all(text=lambda text: text and ('course' in text.lower() or 'subject' in text.lower()))
        for i, text in enumerate(course_elements[:10]):  # Limit to first 10
            print(f"Text {i+1}: '{text.strip()}'")
        
        # Find elements with course/subject in attributes
        for tag in soup.find_all(attrs={"class": lambda x: x and ('course' in str(x).lower() or 'subject' in str(x).lower())}):
            print(f"Element with course/subject class: {tag.name} class='{tag.get('class')}'")
        
        for tag in soup.find_all(attrs={"id": lambda x: x and ('course' in str(x).lower() or 'subject' in str(x).lower())}):
            print(f"Element with course/subject id: {tag.name} id='{tag.get('id')}'")
        
        print("\n🎯 Keep this window open and manually inspect the page!")
        print("Look for the 'Subject and Course Number' field and note its:")
        print("- HTML tag (input/select/etc)")
        print("- id attribute")
        print("- name attribute") 
        print("- class attribute")
        print("- placeholder text")
        
        input("Press Enter when you're done inspecting...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_registration_page() 