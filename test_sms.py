#!/usr/bin/env python3
"""
Test script to verify Twilio SMS sending
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

def test_sms():
    # Load environment variables
    load_dotenv()
    
    # Get Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    to_number = os.getenv('PHONE_NUMBER')
    
    print(f"Account SID: {account_sid}")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    
    if not all([account_sid, auth_token, from_number, to_number]):
        print("❌ Missing Twilio credentials in .env file")
        return
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Get account info
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Account Status: {account.status}")
        print(f"✅ Account Type: {account.type}")
        
        # Send SHORT test SMS
        message = client.messages.create(
            body="TEST: Course notifier working!",  # Much shorter message
            from_=from_number,
            to=to_number
        )
        
        print(f"✅ SMS sent successfully!")
        print(f"📱 Message SID: {message.sid}")
        print(f"📊 Status: {message.status}")
        
        # Fetch updated status
        message = client.messages(message.sid).fetch()
        print(f"📊 Updated Status: {message.status}")
        print(f"📊 Error Code: {message.error_code}")
        print(f"📊 Error Message: {message.error_message}")
        
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")

if __name__ == "__main__":
    test_sms() 