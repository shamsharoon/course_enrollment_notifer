from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from datetime import datetime
import logging
from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, TWILIO_TO
from utils import format_course_url

class NotificationService:
    def __init__(self):
        self.client = None
        self.setup_twilio()
        self.sent_notifications = set()  # Track sent notifications to avoid spam
    
    def setup_twilio(self) -> None:
        """Initialize Twilio client."""
        try:
            self.client = Client(TWILIO_SID, TWILIO_TOKEN)
            logging.info("Twilio client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Twilio client: {e}")
            raise
    
    def send_sms(self, course_code: str, spots: int) -> bool:
        """
        Send SMS notification for course availability.
        Returns True if successful, False otherwise.
        """
        try:
            # Create notification key to avoid duplicate notifications
            notification_key = f"{course_code}_{spots}"
            
            # Skip if we've already sent this exact notification recently
            if notification_key in self.sent_notifications:
                logging.info(f"Skipping duplicate notification for {course_code} with {spots} spots")
                return True
            
            # Prepare SHORT message for trial account
            message_body = f"{course_code} available now! {spots} seats"
            
            # Send SMS
            message = self.client.messages.create(
                from_=TWILIO_FROM,
                to=TWILIO_TO,
                body=message_body
            )
            
            # Track successful notification
            self.sent_notifications.add(notification_key)
            
            logging.info(f"SMS sent successfully for {course_code} (SID: {message.sid})")
            return True
            
        except TwilioException as e:
            logging.error(f"Twilio error sending SMS for {course_code}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending SMS for {course_code}: {e}")
            return False
    
    def clear_notification_cache(self) -> None:
        """Clear the notification cache (useful for testing or long-running processes)."""
        self.sent_notifications.clear()
        logging.info("Notification cache cleared") 