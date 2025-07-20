import pyttsx3
from ai_logic.message_logic import get_dynamic_voice_message

# Simulated DB or Firebase ride data
ride = {
    "name": "Ali",
    "status": "arrived",         # Change to: delayed, cancelled, etc.
    "complaint": None
}

# Get dynamic message
message = get_dynamic_voice_message(ride)

# Speak it
engine = pyttsx3.init()
engine.say(message)
engine.runAndWait()
