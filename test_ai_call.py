#!/usr/bin/env python3
"""
WeRide AI Caller Test Script
This script will help you test your Twilio AI calling functionality
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
import sys

# Load environment variables
load_dotenv()

# Get Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
RECEIVER_NUMBER = os.getenv('RECEIVER_NUMBER')
NGROK_BASE = os.getenv('NGROK_BASE')

def test_twilio_setup():
    """Test if Twilio credentials are working"""
    print("🔍 Testing Twilio Setup...")
    print(f"Account SID: {TWILIO_ACCOUNT_SID}")
    print(f"Twilio Phone: {TWILIO_PHONE_NUMBER}")
    print(f"Receiver Phone: {RECEIVER_NUMBER}")
    print(f"Ngrok Base: {NGROK_BASE}")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # Test the connection by getting account info
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Twilio connection successful!")
        print(f"Account Name: {account.friendly_name}")
        print(f"Account Status: {account.status}")
        return client
    except Exception as e:
        print(f"❌ Twilio setup failed: {e}")
        return None

def list_phone_numbers(client):
    """List available phone numbers"""
    try:
        phone_numbers = client.incoming_phone_numbers.list()
        print(f"\n📱 Available Twilio Phone Numbers:")
        for number in phone_numbers:
            print(f"  - {number.phone_number} ({number.friendly_name})")
        return phone_numbers
    except Exception as e:
        print(f"❌ Error fetching phone numbers: {e}")
        return []

def make_test_call(client, to_number, call_type="arrival"):
    """Make a test AI call"""
    print(f"\n📞 Making test {call_type} call to {to_number}...")
    
    # TwiML URL for the call (this should be your Flask app URL)
    twiml_url = f"{NGROK_BASE}/twiml/{call_type}"
    
    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            method='POST'
        )
        print(f"✅ Call initiated successfully!")
        print(f"Call SID: {call.sid}")
        print(f"Call Status: {call.status}")
        print(f"TwiML URL: {twiml_url}")
        return call
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return None

def main():
    print("🚗 WeRide AI Caller Test Suite")
    print("=" * 50)
    
    # Step 1: Test Twilio setup
    client = test_twilio_setup()
    if not client:
        print("\n❌ Cannot proceed without valid Twilio setup")
        return
    
    # Step 2: List phone numbers
    numbers = list_phone_numbers(client)
    
    # Step 3: Check if Flask app is running
    print(f"\n🌐 Make sure your Flask app is running on {NGROK_BASE}")
    print("   Run: python app.py")
    
    # Step 4: Ask user for test call
    print(f"\n📞 Ready to make a test call!")
    print(f"From: {TWILIO_PHONE_NUMBER}")
    print(f"To: {RECEIVER_NUMBER}")
    
    choice = input("\nDo you want to make a test call? (y/n): ").strip().lower()
    if choice == 'y':
        # Ask for call type
        print("\nChoose call type:")
        print("1. Arrival Call")
        print("2. Safety Call") 
        print("3. Feedback Call")
        call_choice = input("Enter choice (1-3): ").strip()
        
        call_types = {'1': 'arrival', '2': 'safety', '3': 'feedback'}
        call_type = call_types.get(call_choice, 'arrival')
        
        # Make the call
        call = make_test_call(client, RECEIVER_NUMBER, call_type)
        if call:
            print(f"\n✅ Test call completed! Check your phone at {RECEIVER_NUMBER}")
    else:
        print("Test cancelled.")
    
    print(f"\n💡 Next Steps:")
    print(f"1. Make sure your Flask app is running: python app.py")
    print(f"2. Update NGROK_BASE in .env with your ngrok URL")
    print(f"3. Test calls from the web dashboard at http://localhost:5000")

if __name__ == "__main__":
    main()
