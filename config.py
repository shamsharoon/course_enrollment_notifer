import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

# Course Configuration
COURSE_CODES = [c.strip() for c in os.getenv("COURSE_CODES").split(",") if c.strip()]
INTERVAL_MIN = int(os.getenv("INTERVAL_MIN"))

# Site Configuration
BASE_URL = os.getenv("BASE_URL", "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/registration/registerPostSignIn?mode=registration&mepCode=UOIT")
SITE_USERNAME = os.getenv("SITE_USERNAME")  
SITE_PASSWORD = os.getenv("SITE_PASSWORD")

# Browser Configuration
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")
HEADLESS = os.getenv("HEADLESS").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_FILE = os.getenv("LOG_FILE")

def validate_config() -> bool:
    """Validate that all required configuration is present."""
    required_vars = {
        "TWILIO_SID": TWILIO_SID,
        "TWILIO_TOKEN": TWILIO_TOKEN,
        "TWILIO_FROM": TWILIO_FROM,
        "TWILIO_TO": TWILIO_TO,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    if not COURSE_CODES:
        logging.error("No course codes specified in COURSE_CODES")
        return False
    
    return True 