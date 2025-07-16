from app import app, db
from db.models import Ride

with app.app_context():
    rides = Ride.query.all()
    for r in rides:
        print(f"✅ ID: {r.id}, Name: {r.name}, Phone: {r.phone}, Time: {r.timestamp}")
