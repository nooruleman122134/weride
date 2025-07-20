# ai_logic/ride_events.py

from ai_logic.call_triggers import (
    arrival_call,
    cancellation_notice,
    safety_alert_call,
    feedback_call
)

def on_driver_arrival(phone):
    print("📞 Calling rider for arrival...")
    return arrival_call(phone)

def on_ride_cancelled(phone):
    print("📩 Sending cancellation SMS...")
    return cancellation_notice(phone)

def on_safety_issue(phone):
    print("🚨 Safety alert triggered...")
    return safety_alert_call(phone)

def on_feedback_request(phone):
    print("📞 Feedback call being placed...")
    return feedback_call(phone)
