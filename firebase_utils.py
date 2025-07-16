import firebase_admin
from firebase_admin import credentials, db as fdb
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

cred_path = os.getenv("FIREBASE_CRED_PATH")
db_url = os.getenv("FIREBASE_DB")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'databaseURL': db_url})

def save_ride_to_firebase(name, phone):
    ride_ref = fdb.reference("rides")
    new_ref = ride_ref.push()
    new_ref.set({
        "name": name,
        "phone": phone,
        "timestamp": datetime.utcnow().isoformat()
    })
