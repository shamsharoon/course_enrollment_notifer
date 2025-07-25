from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import logging
import time
from config import HEADLESS, SITE_USERNAME, SITE_PASSWORD, BASE_URL
from utils import sanitize_course_code

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
                WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                
                # Try multiple selectors for username field
                username_field = None
                username_selectors = [
                    "input[placeholder*='Email']",
                    "input[placeholder*='Banner']", 
                    "input[placeholder*='Student']",
                    "input[placeholder*='ID']",
                    "input[type='text']:first-of-type",
                    "input[type='email']",
                    "input[name*='user']",
                    "input[name*='email']",
                    "input[id*='user']",
                    "input[id*='email']"
                ]
                
                for selector in username_selectors:
                    try:
                        username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if username_field.is_displayed():
                            logging.info(f"Found username field with selector: {selector}")
                            break
                    except TimeoutException:
                        logging.warning(f"TimeoutException for selector {selector}")
                        continue  # Specific handling for TimeoutException
                    except Exception as e:  # Changed to specific exception if possible, but keeping general as per context
                        logging.warning(f"Exception for selector {selector}: {e}")
                        continue
                
                # Try multiple selectors for password field
                password_field = None
                password_selectors = [
                    "input[placeholder*='Password']",
                    "input[placeholder*='Network']",
                    "input[type='password']",
                    "input[name*='pass']",
                    "input[id*='pass']"
                ]
                
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if password_field.is_displayed():
                            logging.info(f"Found password field with selector: {selector}")
                            break
                    except TimeoutException:
                        logging.warning(f"TimeoutException for selector {selector}")
                        continue
                    except Exception as e:
                        logging.warning(f"Exception for selector {selector}: {e}")
                        continue
                
                if username_field and password_field:
                    # Clear and enter credentials
                    username_field.clear()
                    username_field.send_keys(SITE_USERNAME)
                    logging.info("Entered username")
                    
                    password_field.clear()
                    password_field.send_keys(SITE_PASSWORD)
                    logging.info("Entered password")
                    
                    # Try ENTER key first (fastest method)
                    try:
                        from selenium.webdriver.common.keys import Keys
                        password_field.send_keys(Keys.RETURN)
                        logging.info("FAST: Pressed ENTER key to submit login (fastest method)")
                        WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                        
                        # Check if login worked with Enter key
                        new_url = self.driver.current_url.lower()
                        if not any(keyword in new_url for keyword in login_indicators):
                            logging.info("SUCCESS: Login successful with ENTER key!")
                            return True
                        else:
                            logging.info("ENTER key didn't work, trying sign in button...")
                    except Exception as e:
                        logging.warning(f"ENTER key method failed: {e}")
                    
                    # IMMEDIATELY find and click sign in button (no delays)
                    logging.info("Immediately clicking sign in button...")
                    signin_selectors = [
                        "input[value*='Sign in']",
                        "input[value*='Sign In']", 
                        "input[value*='LOGIN']",
                        "input[value*='Login']",
                        "input[value='Sign in']",
                        "button[type='submit']",
                        "input[type='submit']",
                        "button:contains('Sign')",
                        ".btn-primary",
                        "#submitButton",
                        "[role='button']"
                    ]
                    
                    signin_clicked = False
                    for selector in signin_selectors:
                        try:
                            signin_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if signin_button.is_displayed() and signin_button.is_enabled():
                                # Click immediately after finding the button
                                signin_button.click()
                                logging.info(f"SUCCESS: IMMEDIATELY clicked sign in button with selector: {selector}")
                                signin_clicked = True
                                break
                        except TimeoutException:
                            logging.warning(f"TimeoutException for selector {selector}")
                            continue
                        except Exception as e:
                            logging.warning(f"Selector {selector} failed: {e}")
                            continue
                    
                    if not signin_clicked:
                        logging.error("Could not find or click sign in button")
                        return False
                    
                    # Wait for login to process
                    logging.info("Waiting for login to complete...")
                    WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                    
                    # Check if we're redirected away from login page
                    new_url = self.driver.current_url.lower()
                    logging.info(f"After login submission - URL: {new_url}")
                    
                    # Check if we're no longer on login/SAML page
                    if not any(keyword in new_url for keyword in login_indicators):
                        logging.info("Login appears successful - redirected to new page")
                        return True
                    else:
                        logging.warning("Still on login page after submission")
                        return False
                        
                else:
                    logging.error("Could not find username or password fields")
                    return False
            
            else:
                logging.info("Not on login page, assuming already logged in")
                return True
            
        except TimeoutException:
            logging.error("TimeoutException during login process")
            return False
        except Exception as e:
            logging.error(f"Login process failed: {e}")
            return False
    
    def check_course(self, course_code: str) -> int:
        """
        Check availability for a specific course code on Ontario Tech University system.
        Returns the number of available lecture seats, or 0 if none or error.
        """
        try:
            # Clean course code
            clean_course_code = sanitize_course_code(course_code)  # Renamed for clarity in complex logic
            logging.info(f"Checking course {clean_course_code}")
            
            # Navigate to base URL
            self.driver.get(BASE_URL)
            
            # Step 1: Handle login since it always appears first
            logging.info("Checking for login page immediately after navigation...")
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
            
            if not self.login_if_needed():
                logging.error("Login failed, cannot proceed")
                return 0
            
            # Step 2: Check if we need to select term or if we're already at registration page
            try:
                WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                
                logging.info(f"After login - Current URL: {self.driver.current_url}")
                logging.info(f"After login - Page title: {self.driver.title}")
                
                page_text = self.driver.page_source.lower()
                term_indicators = ["terms open for registration"]
                is_term_page = any(indicator in page_text for indicator in term_indicators)
                has_select_dropdown = len(self.driver.find_elements(By.CSS_SELECTOR, "select")) > 0
                
                logging.info(f"Term page indicators found: {is_term_page}")
                logging.info(f"Select dropdown found: {has_select_dropdown}")
                
                if is_term_page or has_select_dropdown:
                    logging.info("Found term selection page")
                    
                    select2_selectors = [
                        "#s2id_txt_term .select2-choice",
                        ".select2-container .select2-choice",
                        ".term-combo2 .select2-choice",
                        ".select2-choice"
                    ]
                    
                    dropdown_clicked = False
                    for selector in select2_selectors:
                        try:
                            dropdown_trigger = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if dropdown_trigger.is_displayed():
                                logging.info(f"Found Select2 dropdown with selector: {selector}")
                                dropdown_trigger.click()
                                logging.info("SUCCESS: Clicked Select2 dropdown to open it")
                                dropdown_clicked = True
                                WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                                break
                        except TimeoutException:
                            logging.warning(f"TimeoutException for selector {selector}")
                            continue
                        except Exception as e:
                            logging.warning(f"Select2 selector {selector} failed: {e}")
                            continue
                    
                    if dropdown_clicked:
                        # Type "winter" and press Enter to select
                        logging.info("Typing 'winter' and pressing Enter...")
                        search_selectors = [
                            ".select2-search input",
                            ".select2-input",
                            "#s2id_autogen1",
                            ".select2-focusser",
                            "input[class*='select2']",
                            ".select2-container input"
                        ]
                        search_input = None
                        for selector in search_selectors:
                            try:
                                search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if search_input.is_displayed():
                                    logging.info(f"Found Select2 search input with selector: {selector}")
                                    search_input.clear()
                                    search_input.send_keys("winter")
                                    logging.info("SUCCESS: Typed 'winter' in search field")
                                    WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                                    search_input.send_keys(Keys.RETURN)
                                    logging.info("SUCCESS: Pressed ENTER to select filtered option")
                                    break
                            except TimeoutException:
                                logging.warning(f"TimeoutException for selector {selector}")
                                continue
                            except Exception as e:
                                logging.warning(f"Search selector {selector} failed: {e}")
                                continue
                        
                        WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                        
                        continue_selectors = [
                            "#term-go",
                            "button[id='term-go']",
                            "button.form-button",
                            "button[data-endpoint*='term/search']",
                            "input[value='Continue']",
                            "input[value='CONTINUE']",
                            "button[type='submit']",
                            "input[type='submit']",
                            "button:contains('Continue')",
                            ".btn:contains('Continue')"
                        ]
                        continue_clicked = False
                        for selector in continue_selectors:
                            try:
                                continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if continue_button.is_displayed() and continue_button.is_enabled():
                                    continue_button.click()
                                    logging.info(f"Clicked Continue button with selector: {selector}")
                                    continue_clicked = True
                                    break
                            except TimeoutException:
                                logging.warning(f"TimeoutException for selector {selector}")
                                continue
                            except Exception as e:
                                logging.warning(f"Continue selector {selector} failed: {e}")
                                continue
                        if not continue_clicked:
                            logging.error("Could not find or click Continue button")
                            return 0
                    else:
                        logging.error("Could not find or click Select2 term dropdown")
                        return 0
            except TimeoutException:
                logging.warning("TimeoutException during term selection")
            except Exception as e:
                logging.warning(f"Term selection not needed or already completed: {e}")
            
            # Step 3: Search for course
            try:
                logging.info("Waiting for course search page to load...")
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input, select, .search")))
                logging.info("Course search page loaded successfully")
                search_field = None
                selectors_to_try = [
                    "input[placeholder*='course']",
                    "input[name*='course']",
                    "input[id*='course']",
                    "input[placeholder*='subject']",
                    "input[name*='subject']",
                    "input[id*='subject']",
                    "input[type='text']"
                ]
                for selector in selectors_to_try:
                    try:
                        search_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if search_field.is_displayed():
                            logging.info(f"Found search field with selector: {selector}")
                            break
                    except TimeoutException:
                        logging.warning(f"TimeoutException for selector {selector}")
                        continue
                    except Exception as e:
                        logging.warning(f"Selector {selector} failed: {e}")
                        continue
                if search_field:
                    search_field.clear()
                    search_field.send_keys(clean_course_code)
                    logging.info(f"SUCCESS: Typed course code: {clean_course_code}")
                    WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                    search_field.send_keys(Keys.RETURN)
                    logging.info("SUCCESS: Pressed ENTER to submit course search")
                    WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))  # Replaced blocking operation
                else:
                    logging.error("Could not find course search field")
                    return 0
            except TimeoutException:
                logging.error("TimeoutException while searching for course")
                return 0
            except Exception as e:
                logging.error(f"Failed to search for course: {e}")
                return 0
            
            # Step 4: Parse results table  # Complex section: Nested loop for parsing tables and rows
            """
            Docstring for complex parsing section:
            This section processes HTML tables to extract course information.
            It identifies relevant rows and extracts data for matching courses.
            """
            try:
                logging.info("Waiting for search results to load...")
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table, .search-results")))
                logging.info("Search results loaded, parsing course data...")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                course_tables = soup.find_all('table')  # Renamed for descriptiveness
                logging.info(f"Found {len(course_tables)} tables on the page")
                maximum_seats_available = 0  # Renamed for descriptiveness; Initialize maximum seats
                found_matching_sections = 0
                
                # More efficient structure: Use list comprehension to get all rows first
                all_table_rows = [row for table in course_tables for row in table.find_all('tr')]  # Replaced nested loop
                
                for table_row in all_table_rows:  # Iterate through flattened rows
                    # Add comment for complex logic
                    cells = table_row.find_all(['td', 'th'])  # Comment: Extract cells from the row
                    if len(cells) < 5:
                        continue  # Skip rows with insufficient cells
                    subject_cell = table_row.find('td', {'data-property': 'subject'})
                    course_number_cell = table_row.find('td', {'data-property': 'courseNumber'})
                    schedule_type_cell = table_row.find('td', {'data-property': 'scheduleType'})
                    status_cell = table_row.find('td', {'data-property': 'status'})
                    if subject_cell and course_number_cell and schedule_type_cell and status_cell:
                        subject = subject_cell.get_text(strip=True)
                        course_number = course_number_cell.get_text(strip=True)
                        schedule_type = schedule_type_cell.get_text(strip=True)
                        status_text = status_cell.get('title', '').strip() or status_cell.get_text(strip=True)
                        if course_number == clean_course_code and subject == 'CSCI' and schedule_type == 'Lecture':
                            found_matching_sections += 1
                            seats_remaining_match = re.search(r'(\d+)\s*of\s*\d+\s*seats?\s*rem(?:ain)?', status_text, re.IGNORECASE)
                            if seats_remaining_match:
                                section_seats = int(seats_remaining_match.group(1))
                            elif re.search(r'(\d+)\s*of\s*(\d+)', status_text):
                                section_seats = int(re.search(r'(\d+)\s*of\s*(\d+)', status_text).group(1))
                            elif 'FULL:' in status_text and '0 of' in status_text:
                                section_seats = 0
                            elif 'OPEN' in status_text.upper():
                                open_match = re.search(r'(\d+)', status_text)
                                section_seats = int(open_match.group(1)) if open_match else 1
                            else:
                                section_seats = 0
                            if section_seats > maximum_seats_available:
                                maximum_seats_available = section_seats
                if found_matching_sections == 0:
                    logging.info(f"Course {clean_course_code}: No CSCI lecture sections found")
                    return 0
                return maximum_seats_available
            except TimeoutException:
                logging.error("TimeoutException while parsing results")
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