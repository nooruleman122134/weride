from ai_logic.message_logic import get_dynamic_voice_message
import pyttsx3

ride = {
    "name": "Ali",
    "status": "arrived",
    "complaint": None
}

msg = get_dynamic_voice_message(ride)
print("🗣️", msg)

# 🔊 AI Voice Code
engine = pyttsx3.init()
engine.say(msg)
engine.runAndWait()
