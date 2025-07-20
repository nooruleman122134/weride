import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

# 🔄 Load .env
load_dotenv()

# 🔐 Firebase Credentials
cred_path = os.getenv("FIREBASE_CRED_PATH")
db_url = os.getenv("FIREBASE_DB")

if not cred_path or not db_url:
    raise Exception("❌ Firebase config missing in .env")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': db_url
})

# ✅ THIS is the missing part: 'db' is the firebase_admin.db now available

# 🎯 Function you need
def get_realtime_status(ride_id):
    ref = db.reference(f"rides/{ride_id}")
    return ref.get() or {}
