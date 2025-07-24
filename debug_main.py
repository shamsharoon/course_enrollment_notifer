"""
Debug version of main.py with pauses and visual inspection
"""

import sys
import time
from config import validate_config, LOG_LEVEL, LOG_FILE, BASE_URL, SITE_USERNAME, SITE_PASSWORD
from utils import setup_logging
from scraper import CourseScraper
import logging

def debug_single_course_check():
    """Run a single course check with debugging pauses"""
    
    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)
    
    # Validate configuration
    if not validate_config():
        logging.error("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    print("🚀 DEBUG MODE: Course Availability Checker")
    print("=" * 50)
    print(f"📍 Will navigate to: {BASE_URL}")
    print(f"👤 Will login as: {SITE_USERNAME}")
    print(f"📋 Will check courses: CSCI4020U (first course only)")
    print()
    
    input("Press Enter to start Chrome and navigate to the page...")
    
    try:
        # Initialize scraper
        print("🌐 Initializing Chrome WebDriver...")
        scraper = CourseScraper()
        
        print("✅ Chrome opened! You should see a browser window.")
        input("Press Enter to continue...")
        
        print("📍 Navigating to Ontario Tech registration page...")
        scraper.driver.get(BASE_URL)
        
        print("⏳ Page loaded. Current URL:", scraper.driver.current_url)
        print("📄 Page title:", scraper.driver.title)
        
        input("🔍 Look at the browser window. Press Enter when ready to continue...")
        
        # Try to login if needed
        print("🔐 Checking if login is needed...")
        scraper.login_if_needed()
        
        print("⏳ After login attempt. Current URL:", scraper.driver.current_url)
        print("📄 Current title:", scraper.driver.title)
        
        input("🔍 Check the browser - are you at the registration page? Press Enter to continue...")
        
        # Now try to find the course search field
        print("🔍 Looking for course search field...")
        print("Available input fields:")
        
        # Get all visible input fields
        all_inputs = scraper.driver.find_elements("tag name", "input")
        for i, input_elem in enumerate(all_inputs):
            try:
                if input_elem.is_displayed():
                    input_type = input_elem.get_attribute("type") or "text"
                    input_name = input_elem.get_attribute("name") or "N/A"
                    input_id = input_elem.get_attribute("id") or "N/A"
                    input_placeholder = input_elem.get_attribute("placeholder") or "N/A"
                    
                    print(f"  Input {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
            except:
                pass
        
        print("\n🎯 Look at the browser window and find the 'Subject and Course Number' field")
        print("Note down its attributes (id, name, class, placeholder)")
        
        field_selector = input("\n✏️  Enter the CSS selector for the course field (e.g., #course-field or input[name='courseName']): ").strip()
        
        if field_selector:
            try:
                print(f"🔍 Trying to find field with selector: {field_selector}")
                search_field = scraper.driver.find_element("css selector", field_selector)
                
                if search_field.is_displayed():
                    print("✅ Found the field!")
                    
                    # Test entering a course code
                    test_course = "CSCI4020U"
                    print(f"📝 Entering test course: {test_course}")
                    
                    search_field.clear()
                    search_field.send_keys(test_course)
                    
                    print("✅ Successfully entered course code!")
                    input("🔍 Check the browser - did the course code appear? Press Enter...")
                    
                    # Look for autocomplete or search button
                    print("🔍 Looking for search button or autocomplete...")
                    time.sleep(3)  # Wait for autocomplete
                    
                    input("🎯 Manually complete the search process in the browser, then press Enter...")
                    
                else:
                    print("❌ Field found but not visible")
                    
            except Exception as e:
                print(f"❌ Could not find field with selector '{field_selector}': {e}")
        
        input("🏁 Press Enter to close the browser and finish...")
        
        # Close browser
        scraper.close()
        
        print("✅ Debug session complete!")
        
        if field_selector:
            print(f"\n📋 Use this selector in the main script: {field_selector}")
        
    except Exception as e:
        logging.error(f"Debug error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_single_course_check() 