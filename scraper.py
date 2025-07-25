from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import logging
import time
from config import HEADLESS, SITE_USERNAME, SITE_PASSWORD, BASE_URL
from utils import sanitize_course_code, find_element_with_selectors

class CourseScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self) -> None:
        """Initialize Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            
            # Windows-specific fixes for Chrome crashes
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            if HEADLESS:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
            
            # Try to initialize driver
            try:
                # First try without profile (since profile causes crashes on this system)
                self.driver = webdriver.Chrome(options=chrome_options)
                logging.info("Chrome initialized successfully without profile")
            except Exception as chrome_error:
                logging.warning(f"Chrome initialization failed: {chrome_error}")
                logging.info("Trying with webdriver-manager...")
                
                # Try with webdriver-manager for automatic ChromeDriver management
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logging.info("Successfully initialized with webdriver-manager")
                except Exception as wdm_error:
                    logging.warning(f"Webdriver-manager failed: {wdm_error}")
                    logging.info("Trying simplified options...")
                    
                    # Last fallback - minimal options
                    chrome_options_fallback = Options()
                    chrome_options_fallback.add_argument("--no-sandbox")
                    chrome_options_fallback.add_argument("--disable-dev-shm-usage")
                    chrome_options_fallback.add_argument("--disable-gpu")
                    chrome_options_fallback.add_argument("--window-size=1920,1080")
                    
                    if HEADLESS:
                        chrome_options_fallback.add_argument("--headless=new")
                    
                    try:
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options_fallback)
                    except:
                        self.driver = webdriver.Chrome(options=chrome_options_fallback)
            
            self.driver.implicitly_wait(10)
            
            logging.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {e}")
            logging.error("Please ensure Chrome and ChromeDriver are installed and compatible")
            raise
    
    def login_if_needed(self) -> bool:
        """Attempt to login if credentials are provided and not already logged in."""
        if not SITE_USERNAME or not SITE_PASSWORD:
            logging.info("No login credentials provided, assuming already logged in via profile")
            return True
        
        try:
            # Check if we're on a login page (SAML, login, or sign-in in URL)
            current_url = self.driver.current_url.lower()
            login_indicators = ["login", "saml", "sign", "auth", "sts.dc-uoit.ca", "adfs", "shibboleth"]
            is_login_page = any(keyword in current_url for keyword in login_indicators)
            
            logging.info(f"Current URL: {current_url}")
            logging.info(f"Login page detected: {is_login_page}")
            
            if is_login_page:
                logging.info("Login page detected, attempting to log in...")
                
                # Wait for login form to load
                time.sleep(1)
                
                # Try multiple selectors for username field
                username_field = find_element_with_selectors(self.driver, ["input[placeholder*='Email']", "input[placeholder*='Banner']", "input[placeholder*='Student']", "input[placeholder*='ID']", "input[type='text']:first-of-type", "input[type='email']", "input[name*='user']", "input[name*='email']", "input[id*='user']", "input[id*='email']"])
                if username_field:
                    logging.info(f"Found username field")
                    username_field.clear()
                    username_field.send_keys(SITE_USERNAME)
                    logging.info("Entered username")
                else:
                    logging.error("Could not find username field")
                    return False
                
                # Try multiple selectors for password field
                password_field = find_element_with_selectors(self.driver, ["input[placeholder*='Password']", "input[placeholder*='Network']", "input[type='password']", "input[name*='pass']", "input[id*='pass']"])
                if password_field:
                    logging.info(f"Found password field")
                    password_field.clear()
                    password_field.send_keys(SITE_PASSWORD)
                    logging.info("Entered password")
                else:
                    logging.error("Could not find password field")
                    return False
                
                if username_field and password_field:
                    # Clear and enter credentials
                    
                    # Try ENTER key first (fastest method)
                    try:
                        password_field.send_keys(Keys.RETURN)
                        logging.info("FAST: Pressed ENTER key to submit login (fastest method)")
                        time.sleep(2)  # Brief wait to check if it worked
                        
                        # Check if login worked with Enter key
                        new_url = self.driver.current_url.lower()
                        if not any(keyword in new_url for keyword in login_indicators):
                            logging.info("SUCCESS: Login successful with ENTER key!")
                            return True
                        else:
                            logging.info("ENTER key didn't work, trying sign in button...")
                    except NoSuchElementException as e:
                        logging.error(f"ENTER key method failed: {e}")
                    
                    # IMMEDIATELY find and click sign in button (no delays)
                    logging.info("Immediately clicking sign in button...")
                    signin_button = find_element_with_selectors(self.driver, ["input[value*='Sign in']", "input[value*='Sign In']", "input[value*='LOGIN']", "input[value*='Login']", "input[value='Sign in']", "button[type='submit']", "input[type='submit']", "button:contains('Sign')", ".btn-primary", "#submitButton", "[role='button']"])
                    if signin_button:
                        signin_button.click()
                        logging.info("SUCCESS: IMMEDIATELY clicked sign in button")
                        time.sleep(2)
                        
                        # Check if we're redirected away from login page
                        new_url = self.driver.current_url.lower()
                        if not any(keyword in new_url for keyword in login_indicators):
                            logging.info("Login appears successful - redirected to new page")
                            return True
                        else:
                            logging.warning("Still on login page after submission")
                            return False
                    else:
                        logging.error("Could not find or click sign in button")
                        return False
                else:
                    logging.error("Could not find username or password fields")
                    return False
            
            else:
                logging.info("Not on login page, assuming already logged in")
                return True
            
        except Exception as e:
            logging.error(f"Login process failed: {e}")
            return False
    
    def check_course(self, course_code: str) -> int:
        """
        Check availability for a specific course code on Ontario Tech University system.
        Returns number of available lecture seats, or 0 if none/error.
        
        # Note: This function has high cognitive complexity due to multiple conditional paths and loops.
        # It handles navigation, login, term selection, course search, and result parsing.
        """
        try:
            # Clean course code
            clean_code = sanitize_course_code(course_code)
            logging.info(f"Checking course {clean_code}")
            
            # Navigate to base URL
            self.driver.get(BASE_URL)
            
            # Step 1: IMMEDIATELY handle login since it always appears first
            logging.info("Checking for login page immediately after navigation...")
            time.sleep(2)  # Wait for page to load
            
            # Handle login first (this always happens)
            if not self.login_if_needed():
                logging.error("Login failed, cannot proceed")
                return 0
            
            # Step 2: Check if we need to select term or if we're already at registration page
            try:
                # Wait a moment for page to load after login
                time.sleep(3)
                
                logging.info(f"After login - Current URL: {self.driver.current_url}")
                logging.info(f"After login - Page title: {self.driver.title}")
                
                # Check if we're at term selection page
                page_text = self.driver.page_source.lower()
                term_indicators = [
                    "terms open for registration"
                ]
                
                is_term_page = any(indicator in page_text for indicator in term_indicators)
                has_select_dropdown = len(self.driver.find_elements(By.CSS_SELECTOR, "select")) > 0
                
                logging.info(f"Term page indicators found: {is_term_page}")
                logging.info(f"Select dropdown found: {has_select_dropdown}")
                
                if is_term_page or has_select_dropdown:
                    logging.info("Found term selection page")
                    
                    # Handle Select2 dropdown (detected from HTML)
                    select2_selectors = [
                        "#s2id_txt_term .select2-choice",  # Specific Select2 term dropdown
                        ".select2-container .select2-choice",  # Generic Select2 dropdown
                        ".term-combo2 .select2-choice",  # Term-specific Select2
                        ".select2-choice"  # Any Select2 dropdown
                    ]
                    
                    dropdown_trigger = find_element_with_selectors(self.driver, select2_selectors)
                    if dropdown_trigger:
                        logging.info("Found Select2 dropdown")
                        dropdown_trigger.click()
                        logging.info("SUCCESS: Clicked Select2 dropdown to open it")
                        time.sleep(1)
                        
                        # NEW STRATEGY: Type "winter" and press Enter to select
                        logging.info("NEW STRATEGY: Typing 'winter' and pressing Enter...")
                        
                        search_input = find_element_with_selectors(self.driver, [".select2-search input", ".select2-input", "#s2id_autogen1", ".select2-focusser", "input[class*='select2']", ".select2-container input"])
                        if search_input:
                            search_input.clear()
                            search_input.send_keys("winter")
                            logging.info("SUCCESS: Typed 'winter' in search field")
                            time.sleep(1)
                            search_input.send_keys(Keys.RETURN)
                            logging.info("SUCCESS: Pressed ENTER to select filtered option")
                        else:
                            logging.info("No search input found, trying alternative method...")
                        
                        time.sleep(2)
                        
                        continue_button = find_element_with_selectors(self.driver, ["#term-go", "button[id='term-go']", "button.form-button", "button[data-endpoint*='term/search']", "input[value='Continue']", "input[value='CONTINUE']", "button[type='submit']", "input[type='submit']", "button:contains('Continue')", ".btn:contains('Continue')"])
                        if continue_button:
                            continue_button.click()
                            logging.info("Clicked Continue button")
                        else:
                            logging.error("Could not find or click Continue button")
                            return 0
                    else:
                        logging.error("Could not find or click Select2 term dropdown")
                        return 0
                else:
                    logging.info("Already at registration page, skipping term selection")
                
            except Exception as e:
                logging.info(f"Term selection not needed or already completed: {e}")
            
            # Step 2: Wait for Register for Classes page and search for course
            try:
                # Wait for the course search interface to load
                logging.info("Waiting for course search page to load...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input, select, .search"))
                )
                logging.info("Course search page loaded successfully")
                
                # Try multiple selectors for the course search field
                search_field = find_element_with_selectors(self.driver, ["input[placeholder*='course']", "input[name*='course']", "input[id*='course']", "input[placeholder*='subject']", "input[name*='subject']", "input[id*='subject']", "input[type='text']"])
                if search_field:
                    search_field.clear()
                    search_field.send_keys(clean_code)
                    logging.info(f"SUCCESS: Typed course code: {clean_code}")
                    time.sleep(1)
                    search_field.send_keys(Keys.RETURN)
                    logging.info("SUCCESS: Pressed ENTER to submit course search")
                    time.sleep(2)
                else:
                    logging.error("Could not find course search field")
                    return 0
                
            except Exception as e:
                logging.error(f"Failed to search for course: {e}")
                return 0
            
            # Step 3: Parse results table
            try:
                # Wait for results table
                logging.info("Waiting for search results to load...")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table, .search-results"))
                )
                logging.info("Search results loaded, parsing course data...")
                
                # Get page source and parse
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find the results table
                tables = soup.find_all('table')
                logging.info(f"Found {len(tables)} tables on the page")
                
                # To optimize the nested loop, process rows directly from all tables at once to reduce complexity
                all_rows = [row for table in tables for row in table.find_all('tr')]  # Flattened list for single loop
                max_available_seats = 0
                found_matching_sections = 0
                
                for row_idx, row in enumerate(all_rows):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 5:  # Skip header or incomplete rows
                        continue
                    
                    subject_cell = row.find('td', {'data-property': 'subject'})
                    course_number_cell = row.find('td', {'data-property': 'courseNumber'})
                    schedule_type_cell = row.find('td', {'data-property': 'scheduleType'})
                    status_cell = row.find('td', {'data-property': 'status'})
                    
                    if subject_cell and course_number_cell and schedule_type_cell and status_cell:
                        subject = subject_cell.get_text(strip=True)
                        course_number = course_number_cell.get_text(strip=True)
                        schedule_type = schedule_type_cell.get_text(strip=True)
                        status_text = status_cell.get('title', '').strip() or status_cell.get_text(strip=True)
                        
                        if course_number == clean_code and subject == 'CSCI' and schedule_type == 'Lecture':
                            found_matching_sections += 1
                            seats_remaining_match = re.search(r'(\d+)\s*of\s*\d+\s*seats?\s*rem(?:ain)?', status_text, re.IGNORECASE)
                            if seats_remaining_match:
                                section_seats = int(seats_remaining_match.group(1))
                            elif re.search(r'(\d+)\s*of\s*(\d+)', status_text):
                                flexible_match = re.search(r'(\d+)\s*of\s*(\d+)', status_text)
                                section_seats = int(flexible_match.group(1))
                            elif 'FULL:' in status_text and '0 of' in status_text:
                                section_seats = 0
                            elif 'OPEN' in status_text.upper():
                                open_match = re.search(r'(\d+)', status_text)
                                section_seats = int(open_match.group(1)) if open_match else 1
                            else:
                                section_seats = 0  # Default if no match
                            
                            if section_seats > max_available_seats:
                                max_available_seats = section_seats
                
                if found_matching_sections == 0:
                    logging.info(f"Course {clean_code}: No CSCI lecture sections found")
                    return 0
                elif max_available_seats > 0:
                    logging.info(f"SUCCESS: Course {clean_code}: {max_available_seats} seats available (checked {found_matching_sections} CSCI lecture sections)")
                    return max_available_seats
                else:
                    logging.info(f"Course {clean_code}: Found {found_matching_sections} CSCI lecture sections, but all are full")
                    return 0
                
            except Exception as e:
                logging.error(f"Failed to parse results: {e}")
                return 0
            
        except TimeoutException:
            logging.error(f"Timeout while checking course {course_code}")
            return 0
        except Exception as e:
            logging.error(f"Error checking course {course_code}: {e}")
            return 0
    
    def close(self) -> None:
        """Clean up WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed successfully")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")