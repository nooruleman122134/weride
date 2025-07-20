# test_dynamic_call.py
from twilio.rest import Client
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

# Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
receiver_number = os.getenv("RECEIVER_NUMBER")

# ngrok or deployed server base
ngrok_base = os.getenv("NGROK_BASE")  # e.g., https://abcd123.ngrok-free.app

# Custom dynamic message and voice
message = "Thank you for choosing WeRide. Your feedback is important to us."
voice = "Polly.Matthew"

# Prepare URL with parameters
params = urlencode({"message": message, "voice": voice})
voice_url = f"{ngrok_base}/voice-dynamic?{params}"

client = Client(account_sid, auth_token)

# Initiate the call
call = client.calls.create(
    to=receiver_number,
    from_=twilio_number,
    url=voice_url  # This hits your Flask route
)

print(f"✅ Call initiated with SID: {call.sid}")
