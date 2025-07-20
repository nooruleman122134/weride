# db/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    user_type = db.Column(db.String(20), default='passenger')  # passenger or driver
    profile_photo = db.Column(db.String(200))
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rides_as_passenger = db.relationship('Ride', foreign_keys='Ride.passenger_id', backref='passenger', lazy='dynamic')
    rides_as_driver = db.relationship('Ride', foreign_keys='Ride.driver_id', backref='driver', lazy='dynamic')

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_year = db.Column(db.Integer)
    vehicle_color = db.Column(db.String(30))
    license_plate = db.Column(db.String(20), unique=True)
    is_online = db.Column(db.Boolean, default=False)
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    hourly_rate = db.Column(db.Float, default=15.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='driver_profile')

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Pickup details
    pickup_address = db.Column(db.String(300), nullable=False)
    pickup_lat = db.Column(db.Float)
    pickup_lng = db.Column(db.Float)
    
    # Destination details
    destination_address = db.Column(db.String(300), nullable=False)
    destination_lat = db.Column(db.Float)
    destination_lng = db.Column(db.Float)
    
    # Ride details
    passenger_offer = db.Column(db.Float, nullable=False)  # InDrive style - passenger sets price
    driver_counter_offer = db.Column(db.Float)
    final_price = db.Column(db.Float)
    estimated_distance = db.Column(db.Float)
    estimated_duration = db.Column(db.Integer)  # in minutes
    
    # Status tracking
    status = db.Column(db.String(30), default='pending')  # pending, accepted, en_route, arrived, in_progress, completed, cancelled
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    pickup_time = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # AI Caller Integration
    arrival_call_made = db.Column(db.Boolean, default=False)
    safety_check_made = db.Column(db.Boolean, default=False)
    feedback_call_made = db.Column(db.Boolean, default=False)
    
class RideOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    offered_price = db.Column(db.Float, nullable=False)
    estimated_pickup_time = db.Column(db.Integer)  # minutes
    message = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ride = db.relationship('Ride', backref='offers')
    driver = db.relationship('User', backref='ride_offers')
    
class RideTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    driver_lat = db.Column(db.Float, nullable=False)
    driver_lng = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    ride = db.relationship('Ride', backref='tracking_points')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # who gave the rating
    rated_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # who received the rating
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ride = db.relationship('Ride', backref='ratings')
    rater = db.relationship('User', foreign_keys=[rater_id], backref='ratings_given')
    rated = db.relationship('User', foreign_keys=[rated_id], backref='ratings_received')
