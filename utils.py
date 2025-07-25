import logging
import sys

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

def sanitize_course_code(course_code: str) -> str:
    """Clean and format course code."""
    return course_code.strip().upper().replace(" ", "") 