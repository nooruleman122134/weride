#!/usr/bin/env python3
"""
WeRide AI Database Initialization Script
Run this to set up the database with sample drivers
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
from dotenv import load_dotenv

load_dotenv()

# Create a minimal Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///weride.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models after db initialization
sys.path.insert(0, 'db')
from models import User, Driver, Ride, RideOffer, RideTracking, Rating

def init_database():
    """Initialize database with sample data"""
    print("🔄 Initializing WeRide AI Database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Add sample drivers if none exist
        existing_drivers = User.query.filter_by(user_type='driver').first()
        if not existing_drivers:
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
                db.session.flush()  # Get user ID
                
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
                    hourly_rate=random.uniform(200, 500)
                )
                db.session.add(driver)
                print(f"✅ Added driver: {driver_data['name']} ({driver_data['license_plate']})")
            
            db.session.commit()
            print("✅ Sample drivers added to database")
            
        # Add sample passengers if needed
        if User.query.filter_by(user_type='passenger').count() == 0:
            sample_passengers = [
                {'name': 'John Doe', 'phone': '+923331234567'},
                {'name': 'Jane Smith', 'phone': '+923339876543'},
                {'name': 'Ali Ahmed', 'phone': '+923335555555'}
            ]
            
            for passenger_data in sample_passengers:
                user = User(
                    name=passenger_data['name'],
                    phone=passenger_data['phone'],
                    user_type='passenger',
                    rating=round(random.uniform(4.0, 5.0), 1),
                    total_rides=random.randint(5, 50)
                )
                db.session.add(user)
                print(f"✅ Added passenger: {passenger_data['name']}")
            
            db.session.commit()
            print("✅ Sample passengers added to database")
        
        # Print summary
        total_drivers = User.query.filter_by(user_type='driver').count()
        total_passengers = User.query.filter_by(user_type='passenger').count()
        online_drivers = db.session.query(Driver).filter_by(is_online=True).count()
        
        print("\n" + "="*50)
        print("🎉 WeRide AI Database Initialized Successfully!")
        print("="*50)
        print(f"👥 Total Drivers: {total_drivers}")
        print(f"🟢 Online Drivers: {online_drivers}")
        print(f"🚶 Total Passengers: {total_passengers}")
        print(f"📊 Database ready for InDrive-like operations!")
        print("\n🚀 Ready to use:")
        print("   • http://localhost:5000 - AI Caller Dashboard")
        print("   • http://localhost:5000/real-book - InDrive-like Booking")
        print("   • http://localhost:5000/dashboard - Real Data Dashboard")

if __name__ == "__main__":
    init_database()
