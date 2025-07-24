import logging
import sys
from config import BASE_URL

def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Set up logging configuration."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

def format_course_url(course_code: str) -> str:
    """Format course URL for registration."""
    # This would need to be customized based on your actual university's URL structure
    return f"{BASE_URL}?course={course_code}"

def sanitize_course_code(course_code: str) -> str:
    """Clean and format course code."""
    return course_code.strip().upper().replace(" ", "") 