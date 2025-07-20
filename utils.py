# utils.py
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def make_voice_call(to, message_url):
    try:
        call = client.calls.create(
            to=to,
            from_=TWILIO_NUMBER,
            url=message_url  # TwiML or webhook
        )
        return call.sid
    except Exception as e:
        print("❌ Call Error:", e)
        return None


def send_sms(to, body):
    try:
        message = client.messages.create(
            to=to,
            from_=TWILIO_NUMBER,
            body=body
        )
        return message.sid
    except Exception as e:
        print("❌ SMS Error:", e)
        return None
