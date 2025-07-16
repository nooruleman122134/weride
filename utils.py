from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

def make_call(to_number, message_text):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            twiml=f'<Response><Say>{message_text}</Say></Response>',
            to=to_number,
            from_=TWILIO_PHONE_NUMBER
        )

        print("✅ Twilio call initiated. Call SID:", call.sid)
        return call.sid

    except Exception as e:
        print("❌ Twilio Call Error:", e)
        return None
