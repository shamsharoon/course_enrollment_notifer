from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import signal
import sys
import atexit
import time
import logging
import os
from config import COURSE_CODES, INTERVAL_MIN
from scraper import CourseScraper
from notifier import NotificationService
import os

class CourseMonitor:
    def __init__(self):
        self.scraper = None
        self.notifier = None
        self.scheduler = None
        self.setup_components()
        self.setup_scheduler()
        self.setup_signal_handlers()
    
    def setup_components(self) -> None:
        """Initialize scraper and notification components."""
        try:
            self.scraper = CourseScraper()
            self.notifier = NotificationService()
            
            # Try to login if needed
            if not self.scraper.login_if_needed():
                logging.warning("Login may have failed, but continuing...")
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            raise
    
    def setup_scheduler(self) -> None:
        """Initialize APScheduler."""
        self.scheduler = BlockingScheduler()
        
        # Add job listener for monitoring
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        def signal_handler(signum):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def job_listener(self, event) -> None:
        """Listen for job events and log them."""
        if event.exception:
            logging.error(f"Job crashed: {event.exception}")
        else:
            logging.info("Job executed successfully")
    
    def check_all_courses(self) -> None:
        """Main job function - check all courses for availability."""
        logging.info(f"Starting course availability check for {len(COURSE_CODES)} courses")
        
        found_available = False
        
        for course_code in COURSE_CODES:
            try:
                spots = self.scraper.check_course(course_code)
                
                if spots > 0:
                    logging.info(f"SUCCESS: Found {spots} available spots for {course_code}!")
                    
                    # Send notification
                    if self.notifier.send_sms(course_code, spots):
                        found_available = True
                    else:
                        logging.error(f"Failed to send notification for {course_code}")
                
                # Small delay between course checks to be respectful
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error checking course {course_code}: {e}")
                continue
        
        if found_available:
            logging.info("Course availability check completed - notifications sent!")
        else:
            logging.info("Course availability check completed - no spots available")
        
        # Periodically clear notification cache (every 24 hours worth of checks)
        checks_per_day = (24 * 60) // INTERVAL_MIN
        if hasattr(self, 'check_count'):
            self.check_count += 1
        else:
            self.check_count = 1
        
        if self.check_count >= checks_per_day:
            self.notifier.clear_notification_cache()
            self.check_count = 0
    
    def start(self) -> None:
        """Start the monitoring service."""
        try:
            logging.info(f"Starting Course Availability Notifier")
            logging.info(f"Monitoring courses: {', '.join(COURSE_CODES)}")
            logging.info(f"Check interval: {INTERVAL_MIN} minutes")
            logging.info(f"Notifications will be sent to: {os.getenv('TWILIO_TO', 'CONFIGURED_NUMBER')}")
            
            # Schedule the job
            self.scheduler.add_job(
                func=self.check_all_courses,
                trigger="interval",
                minutes=INTERVAL_MIN,
                id="course_check",
                name="Course Availability Check"
            )
            
            # Run once immediately
            logging.info("Running initial course check...")
            self.check_all_courses()
            
            # Start scheduler
            logging.info("Scheduler started - monitoring for course availability...")
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
            self.shutdown()
        except Exception as e:
            logging.error(f"Error starting service: {e}")
            raise
    
    def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        logging.info("Shutting down Course Availability Notifier...")
        
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("Scheduler stopped")
        
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.scraper:
            self.scraper.close() 