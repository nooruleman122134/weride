# db/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
