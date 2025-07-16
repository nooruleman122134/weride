from flask import Flask, request, render_template, Response
from db.models import db, Ride
from db.db_setup import init_db
from utils import make_call
from firebase_utils import save_ride_to_firebase

app = Flask(__name__)
init_db(app)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")

        # 🔸 PostgreSQL save
        ride = Ride(name=name, phone=phone)
        db.session.add(ride)
        db.session.commit()

        # 🔸 Firebase save
        save_ride_to_firebase(name, phone)

        # 🔸 Twilio call
        voice_url = "https://8bc694cfce38.ngrok-free.app/voice"
        make_call(phone, voice_url)

        return "✅ Ride booked, saved to DB & Firebase. AI call on the way."

    return render_template("index.html")


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Your WeRide ride is confirmed. Please wait for your driver. Thank you!</Say>
</Response>"""
    return Response(response, mimetype='text/xml')

if __name__ == "__main__":
    app.run(port=5000)
