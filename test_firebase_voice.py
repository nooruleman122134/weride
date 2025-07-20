from firebase_utils import get_realtime_status
from ai_logic.message_logic import get_dynamic_voice_message
import pyttsx3

ride_data = get_realtime_status("1")

if ride_data:
    message = get_dynamic_voice_message(ride_data)
    print("🗣️", message)
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()
else:
    print("❌ Ride not found in Firebase.")
