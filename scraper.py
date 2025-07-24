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
from config import CHROME_PROFILE_PATH, HEADLESS, SITE_USERNAME, SITE_PASSWORD, BASE_URL
from utils import format_course_url, sanitize_course_code

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
                    except:
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
                    except:
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
                        time.sleep(2)  # Brief wait to check if it worked
                        
                        # Check if login worked with Enter key
                        new_url = self.driver.current_url.lower()
                        if not any(keyword in new_url for keyword in login_indicators):
                            logging.info("SUCCESS: Login successful with ENTER key!")
                            return True
                        else:
                            logging.info("ENTER key didn't work, trying sign in button...")
                    except:
                        logging.info("ENTER key method failed, trying sign in button...")
                    
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
                        except Exception as e:
                            logging.debug(f"Selector {selector} failed: {e}")
                            continue
                    
                    if not signin_clicked:
                        logging.error("Could not find or click sign in button")
                        return False
                    
                    # Wait for login to process
                    logging.info("Waiting for login to complete...")
                    time.sleep(2)
                    
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
            
        except Exception as e:
            logging.error(f"Login process failed: {e}")
            return False
    
    def check_course(self, course_code: str) -> int:
        """
        Check availability for a specific course code on Ontario Tech University system.
        Returns number of available lecture seats, or 0 if none/error.
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
                time.sleep(5)
                
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
                    
                    dropdown_clicked = False
                    for selector in select2_selectors:
                        try:
                            dropdown_trigger = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if dropdown_trigger.is_displayed():
                                logging.info(f"Found Select2 dropdown with selector: {selector}")
                                
                                # Click to open the dropdown
                                dropdown_trigger.click()
                                logging.info("SUCCESS: Clicked Select2 dropdown to open it")
                                dropdown_clicked = True
                                
                                # Wait for dropdown options to appear
                                time.sleep(1)
                                break
                        except Exception as e:
                            logging.debug(f"Select2 selector {selector} failed: {e}")
                            continue
                    
                    if dropdown_clicked:
                        # NEW STRATEGY: Type "winter" and press Enter to select
                        logging.info("NEW STRATEGY: Typing 'winter' and pressing Enter...")
                        
                        option_selected = False
                        
                        # Method 1: Find Select2 search input field and type
                        try:
                            search_selectors = [
                                ".select2-search input",
                                ".select2-input", 
                                "#s2id_autogen1",  # From your HTML
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
                                        break
                                except:
                                    continue
                            
                            if search_input:
                                # Clear and type "winter"
                                search_input.clear()
                                search_input.send_keys("winter")
                                logging.info("SUCCESS: Typed 'winter' in search field")
                                
                                # Wait for filter to apply
                                time.sleep(1)
                                
                                # Press Enter to select the filtered option
                                from selenium.webdriver.common.keys import Keys
                                search_input.send_keys(Keys.RETURN)
                                logging.info("SUCCESS: Pressed ENTER to select filtered option")
                                
                                option_selected = True
                                
                            else:
                                logging.info("No search input found, trying alternative method...")
                                
                        except Exception as e:
                            logging.debug(f"Type + Enter method failed: {e}")
                        
                        # Method 2: If no search input, try typing directly in the dropdown area
                        if not option_selected:
                            try:
                                # Click the dropdown area and type
                                dropdown_area = self.driver.find_element(By.CSS_SELECTOR, ".select2-container, .select2-choice")
                                dropdown_area.click()  # Ensure focus
                                
                                # Type "winter" directly
                                from selenium.webdriver.common.keys import Keys
                                dropdown_area.send_keys("winter")
                                logging.info("SUCCESS: Typed 'winter' directly in dropdown area")
                                
                                time.sleep(1)
                                
                                # Press Enter
                                dropdown_area.send_keys(Keys.RETURN)
                                logging.info("SUCCESS: Pressed ENTER to select")
                                
                                option_selected = True
                                
                            except Exception as e:
                                logging.debug(f"Direct typing method failed: {e}")
                        
                        # Method 3: JavaScript typing as final fallback
                        if not option_selected:
                            try:
                                js_script = """
                                // Find the dropdown container
                                var container = document.querySelector('.select2-container');
                                if (container) {
                                    // Simulate typing 'winter'
                                    var event = new Event('input', { bubbles: true });
                                    var keyEvent = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
                                    
                                    // Try to find search input
                                    var searchInput = container.querySelector('input');
                                    if (searchInput) {
                                        searchInput.value = 'winter';
                                        searchInput.dispatchEvent(event);
                                        setTimeout(function() {
                                            searchInput.dispatchEvent(keyEvent);
                                        }, 500);
                                        return 'Success: Typed winter and pressed Enter';
                                    }
                                }
                                return 'Failed: Could not find search input';
                                """
                                result = self.driver.execute_script(js_script)
                                logging.info(f"JavaScript typing result: {result}")
                                
                                if "Success" in result:
                                    option_selected = True
                                    logging.info("SUCCESS: Successfully typed 'winter' + Enter with JavaScript")
                                    time.sleep(2)  # Wait for selection
                                
                            except Exception as e:
                                logging.debug(f"JavaScript typing failed: {e}")
                        
                        if not option_selected:
                            # Try to find all available options for debugging
                            try:
                                available_options = self.driver.find_elements(By.CSS_SELECTOR, ".select2-result, .select2-results li")
                                option_texts = [opt.text.strip() for opt in available_options if opt.text.strip()]
                                logging.error(f"Could not find Winter 2026. Available options: {option_texts}")
                            except:
                                logging.error("Could not find Winter 2026 option and failed to get available options")
                            return 0
                        
                        # Wait a moment for selection to register
                        time.sleep(2)
                        
                        # Click Continue button (using specific button from HTML)
                        continue_selectors = [
                            "#term-go",  # Specific ID from user's HTML
                            "button[id='term-go']",  # Button with specific ID
                            "button.form-button",  # Button with form-button class
                            "button[data-endpoint*='term/search']",  # Button with term/search endpoint
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
                            except Exception as e:
                                logging.debug(f"Continue selector {selector} failed: {e}")
                                continue
                        
                        if not continue_clicked:
                            logging.error("Could not find or click Continue button")
                            return 0
                        
                        logging.info("Selected Winter 2026 term and clicked Continue")
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
                    except:
                        continue
                
                if not search_field:
                    logging.error("Could not find course search field")
                    return 0
                
                # Clear and enter the course code
                search_field.clear()
                search_field.send_keys(clean_code)
                logging.info(f"SUCCESS: Typed course code: {clean_code}")
                
                # NEW STRATEGY: Just press Enter immediately after typing
                logging.info("NEW STRATEGY: Pressing ENTER to search for course...")
                
                # Wait a brief moment for typing to register
                time.sleep(1)
                
                # Press Enter to submit search
                from selenium.webdriver.common.keys import Keys
                search_field.send_keys(Keys.RETURN)
                logging.info("SUCCESS: Pressed ENTER to submit course search")
                
                # Wait a moment to see if Enter worked
                time.sleep(2)
                
                # Check if search was submitted by looking for results or changes
                current_url = self.driver.current_url
                page_source_length = len(self.driver.page_source)
                
                logging.info(f"After Enter - URL: {current_url}")
                logging.info(f"After Enter - Page length: {page_source_length}")
                
                # Fallback: Try search button if Enter didn't seem to work
                try:
                    # Check if we still need to click a search button
                    search_buttons = [
                        "input[value*='Search']",
                        "button[type='submit']", 
                        "input[type='submit']",
                        "button[id*='search']",
                        ".search-button",
                        ".btn-search"
                    ]
                    
                    button_clicked = False
                    for button_selector in search_buttons:
                        try:
                            search_button = self.driver.find_element(By.CSS_SELECTOR, button_selector)
                            if search_button.is_displayed() and search_button.is_enabled():
                                search_button.click()
                                logging.info(f"🔄 Fallback: Clicked search button: {button_selector}")
                                button_clicked = True
                                break
                        except:
                            continue
                    
                    if not button_clicked:
                        logging.info("SUCCESS: Enter key worked - no search button needed")
                        
                except Exception as e:
                    logging.debug(f"Search button fallback failed: {e}")
                
                logging.info("Submitted course search")
                
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
                
                # Track the maximum available seats across all matching sections
                max_available_seats = 0
                found_matching_sections = 0
                
                for table_idx, table in enumerate(tables):
                    rows = table.find_all('tr')
                    logging.info(f"Table {table_idx}: Found {len(rows)} rows")
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 5:  # Skip header or incomplete rows
                            continue
                        
                        # Look for specific cells using data-property attributes
                        subject_cell = row.find('td', {'data-property': 'subject'})
                        course_number_cell = row.find('td', {'data-property': 'courseNumber'})
                        schedule_type_cell = row.find('td', {'data-property': 'scheduleType'})
                        status_cell = row.find('td', {'data-property': 'status'})
                        
                        if subject_cell and course_number_cell and schedule_type_cell and status_cell:
                            subject = subject_cell.get_text(strip=True)
                            course_number = course_number_cell.get_text(strip=True)
                            schedule_type = schedule_type_cell.get_text(strip=True)
                            
                            # Extract status text more robustly - try title attribute first, then text content
                            status_text = status_cell.get('title', '').strip()
                            if not status_text:
                                status_text = status_cell.get_text(strip=True)
                            
                            logging.info(f"DEBUG: Row {row_idx} - Subject: {subject}, Course: {course_number}, Type: {schedule_type}, Status: '{status_text}'")
                            
                            # Check if this matches our course, is CSCI subject, and is a lecture
                            if course_number == clean_code and subject == 'CSCI' and schedule_type == 'Lecture':
                                found_matching_sections += 1
                                logging.info(f"DEBUG: MATCH #{found_matching_sections}! Found CSCI {clean_code} lecture with status: '{status_text}'")
                                
                                section_seats = 0  # Default to 0 seats for this section
                                
                                # Pattern 1: "X of Y seats remain/rem..." (case-insensitive, flexible spacing)
                                seats_remaining_match = re.search(r'(\d+)\s*of\s*\d+\s*seats?\s*rem(?:ain)?', status_text, re.IGNORECASE)
                                if seats_remaining_match:
                                    section_seats = int(seats_remaining_match.group(1))
                                    logging.info(f"PARSED: Section has {section_seats} seats remaining")
                                
                                # Pattern 1b: More flexible "X of Y" pattern (backup, flexible spacing)  
                                elif re.search(r'(\d+)\s*of\s*(\d+)', status_text):
                                    flexible_match = re.search(r'(\d+)\s*of\s*(\d+)', status_text)
                                    section_seats = int(flexible_match.group(1))
                                    total_seats = int(flexible_match.group(2))
                                    logging.info(f"PARSED: Section has {section_seats} of {total_seats} seats available")
                                
                                # Pattern 2: "FULL: 0 of X" - just log it, don't return early
                                elif 'FULL:' in status_text and '0 of' in status_text:
                                    section_seats = 0
                                    logging.info(f"PARSED: Section is full (0 seats)")
                                
                                # Pattern 3: Check for "OPEN" status
                                elif 'OPEN' in status_text.upper():
                                    # Try to extract number if available
                                    open_match = re.search(r'(\d+)', status_text)
                                    if open_match:
                                        section_seats = int(open_match.group(1))
                                        logging.info(f"PARSED: Section is open with {section_seats} seats")
                                    else:
                                        section_seats = 1  # At least 1 spot available
                                        logging.info(f"PARSED: Section is open (assuming 1+ seats)")
                                
                                # Update maximum available seats
                                if section_seats > max_available_seats:
                                    max_available_seats = section_seats
                                    logging.info(f"NEW MAX: Updated max available seats to {max_available_seats}")
                
                # Final result
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