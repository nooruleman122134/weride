# ai_logic/call_triggers.py

from utils import make_voice_call, send_sms

def arrival_call(phone):
    url = "https://your-ngrok-url/voice-arrival"
    return make_voice_call(phone, url)


def cancellation_notice(phone):
    body = "Your ride has been cancelled. Let us know if you need help."
    return send_sms(phone, body)


def safety_alert_call(phone):
    url = "https://your-ngrok-url/voice-safety"
    return make_voice_call(phone, url)


def feedback_call(phone):
    url = "https://your-ngrok-url/voice-feedback"
    return make_voice_call(phone, url)
