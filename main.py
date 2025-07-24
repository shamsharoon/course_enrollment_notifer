import sys
from config import validate_config, LOG_LEVEL, LOG_FILE
from utils import setup_logging
from scheduler import CourseMonitor
import logging

def main():
    """Main entry point."""
    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)
    
    # Validate configuration
    if not validate_config():
        logging.error("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    # Create and start monitor
    try:
        monitor = CourseMonitor()
        monitor.start()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 