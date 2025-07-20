from flask import Flask
from db.db_setup import db
from db.models import Ride
from ai_logic.message_logic import get_dynamic_voice_message
import pyttsx3

# 🔧 Setup Flask app and initialize DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/weride_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 🔄 Use app context
with app.app_context():
    ride = Ride.query.get(1)

    if ride:
        ride_data = {
            "name": ride.name,
            "status": ride.status,
            "complaint": ride.complaint_flag
        }

        message = get_dynamic_voice_message(ride_data)
        print("🗣️", message)
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    else:
        print("❌ Ride not found.")
