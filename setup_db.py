#!/usr/bin/env python3
"""
Simple WeRide AI Database Setup Script
"""

import os
import random
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///weride.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models inline
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    user_type = db.Column(db.String(20), default='passenger')
    profile_photo = db.Column(db.String(200))
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    
    user = db.relationship('User', backref='driver_profile')

# Setup function
def setup_database():
    print("🔄 Setting up WeRide AI Database...")
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if drivers already exist
        existing_drivers = User.query.filter_by(user_type='driver').first()
        
        if not existing_drivers:
            print("📝 Adding sample drivers...")
            
            sample_drivers = [
                {
                    'name': 'Ahmed Khan',
                    'phone': '+923001234567',
                    'vehicle_make': 'Toyota',
                    'vehicle_model': 'Corolla',
                    'vehicle_year': 2020,
                    'vehicle_color': 'White',
                    'license_plate': 'ABC-123',
                    'license_number': 'DL123456789',
                    'lat': 24.8607,
                    'lng': 67.0011
                },
                {
                    'name': 'Muhammad Ali', 
                    'phone': '+923009876543',
                    'vehicle_make': 'Honda',
                    'vehicle_model': 'Civic',
                    'vehicle_year': 2019,
                    'vehicle_color': 'Black',
                    'license_plate': 'XYZ-789',
                    'license_number': 'DL987654321',
                    'lat': 24.8615,
                    'lng': 67.0025
                },
                {
                    'name': 'Fatima Sheikh',
                    'phone': '+923005555555',
                    'vehicle_make': 'Suzuki',
                    'vehicle_model': 'Alto',
                    'vehicle_year': 2021,
                    'vehicle_color': 'Blue',
                    'license_plate': 'DEF-456',
                    'license_number': 'DL555666777',
                    'lat': 24.8590,
                    'lng': 67.0005
                },
                {
                    'name': 'Hassan Malik',
                    'phone': '+923007777777',
                    'vehicle_make': 'Hyundai',
                    'vehicle_model': 'Elantra',
                    'vehicle_year': 2018,
                    'vehicle_color': 'Silver',
                    'license_plate': 'GHI-999',
                    'license_number': 'DL444555666',
                    'lat': 24.8580,
                    'lng': 67.0030
                },
                {
                    'name': 'Aisha Rehman',
                    'phone': '+923008888888',
                    'vehicle_make': 'KIA',
                    'vehicle_model': 'Picanto',
                    'vehicle_year': 2022,
                    'vehicle_color': 'Red',
                    'license_plate': 'JKL-555',
                    'license_number': 'DL333222111',
                    'lat': 24.8600,
                    'lng': 67.0020
                }
            ]
            
            for driver_data in sample_drivers:
                # Create user
                user = User(
                    name=driver_data['name'],
                    phone=driver_data['phone'],
                    user_type='driver',
                    rating=round(random.uniform(4.2, 5.0), 1),
                    total_rides=random.randint(50, 200)
                )
                db.session.add(user)
                db.session.flush()
                
                # Create driver profile
                driver = Driver(
                    user_id=user.id,
                    license_number=driver_data['license_number'],
                    vehicle_make=driver_data['vehicle_make'],
                    vehicle_model=driver_data['vehicle_model'],
                    vehicle_year=driver_data['vehicle_year'],
                    vehicle_color=driver_data['vehicle_color'],
                    license_plate=driver_data['license_plate'],
                    is_online=True,
                    current_lat=driver_data['lat'],
                    current_lng=driver_data['lng'],
                    last_location_update=datetime.utcnow(),
                    hourly_rate=round(random.uniform(200, 500), 2)
                )
                db.session.add(driver)
                print(f"✅ Added driver: {driver_data['name']} ({driver_data['license_plate']})")
            
            db.session.commit()
            print("✅ Sample drivers added!")
        else:
            print("ℹ️  Drivers already exist in database")
        
        # Get final counts
        total_drivers = User.query.filter_by(user_type='driver').count()
        online_drivers = Driver.query.filter_by(is_online=True).count()
        
        print("\n" + "="*60)
        print("🎉 WeRide AI Database Setup Complete!")
        print("="*60)
        print(f"👥 Total Drivers: {total_drivers}")
        print(f"🟢 Online Drivers: {online_drivers}")
        print("\n🚀 Your app is ready:")
        print("   • http://localhost:5000 - AI Caller Dashboard") 
        print("   • http://localhost:5000/real-book - InDrive-like Booking")
        print("   • http://localhost:5000/dashboard - Real Data Dashboard")
        print("\n💡 Now run: python app.py")

if __name__ == "__main__":
    setup_database()
