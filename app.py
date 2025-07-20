from flask import Flask, request, Response, render_template, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
import json
import random
from dotenv import load_dotenv
from ai_logic.ride_events import on_driver_arrival, on_ride_cancelled, on_safety_issue, on_feedback_request
try:
    from firebase_utils import get_realtime_status
    firebase_available = True
except ImportError:
    firebase_available = False
    print("⚠️  Firebase not available - running without real-time features")

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'weride-ai-caller-secret-2024')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///weride.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
RECEIVER_NUMBER = os.getenv('RECEIVER_NUMBER')
NGROK_BASE = os.getenv('NGROK_BASE', 'https://your-domain.vercel.app')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"⚠️  Twilio initialization error: {e}")
else:
    print("⚠️  Twilio credentials not found - running in demo mode")

# In-memory storage for demo (replace with your database)
active_calls = {}
ride_bookings = {}
call_logs = []
user_sessions = {}

# Enhanced AI Response templates with detailed status updates
AI_RESPONSES = {
    'booking_confirmed': [
        "Hello! This is WeRide AI assistant. Your ride has been successfully booked for {price} rupees from {pickup} to {destination}. Your booking ID is {booking_id}. We'll call you when a driver accepts your request.",
        "Hi! WeRide AI here. Great news! Your ride booking is confirmed. Route: {pickup} to {destination}. Price: {price} rupees. Booking reference: {booking_id}. You'll get another call when your driver is assigned.",
        "Thank you for choosing WeRide! Your booking is confirmed. From {pickup} to {destination} for {price} rupees. Booking ID: {booking_id}. We'll notify you once a driver accepts."
    ],
    'driver_assigned': [
        "Good news! Driver {driver_name} has accepted your ride request. They're driving a {vehicle} with license plate {plate}. Driver rating: {rating} stars. They'll reach you in approximately {eta} minutes.",
        "WeRide AI here! Your driver {driver_name} is confirmed. Vehicle: {vehicle}, Plate: {plate}, Rating: {rating} stars. Estimated arrival: {eta} minutes. Get ready!",
        "Hello! Driver {driver_name} has accepted your WeRide booking. They're in a {vehicle} ({plate}) with {rating} star rating. Expected pickup time: {eta} minutes."
    ],
    'driver_enroute': [
        "Your WeRide driver {driver_name} is now on the way to pick you up. They're currently {distance} away and should arrive in {eta} minutes. Vehicle: {vehicle}, Plate: {plate}.",
        "WeRide update: Driver {driver_name} is heading to your location. Current distance: {distance}. Arrival time: approximately {eta} minutes. Look for {vehicle} with plate {plate}.",
        "Hi! Your driver {driver_name} is en route. They're {distance} away in a {vehicle} ({plate}). Estimated arrival: {eta} minutes. Please be ready!"
    ],
    'driver_arrived': [
        "Your WeRide driver {driver_name} has arrived at your pickup location! They're waiting in a {vehicle} with license plate {plate}. Please come out and look for your driver. Press 1 when you see them, or 2 if you need more time.",
        "Hi! This is WeRide AI. Driver {driver_name} is now at your location in a {vehicle}, plate number {plate}. They're waiting for you outside. Press 1 to confirm you're coming out, or 2 if you need a few more minutes.",
        "Good day! Your WeRide driver {driver_name} has reached your pickup point. Look for a {vehicle} with plate {plate}. Press 1 when you spot your driver, or 2 if you need additional time to come out."
    ],
    'ride_started': [
        "Your WeRide journey has begun! Driver {driver_name} is taking you from {pickup} to {destination}. Estimated trip time: {duration} minutes. For safety, we may call to check on you during the ride.",
        "WeRide AI here! Your trip has started with driver {driver_name}. Route: {pickup} to {destination}. Journey time: approximately {duration} minutes. Have a safe ride!",
        "Hello! Your WeRide trip is underway. Driver {driver_name} is driving you to {destination}. Expected arrival: {duration} minutes. Enjoy your ride and stay safe!"
    ],
    'safety_check': [
        "This is WeRide AI safety monitoring. We're checking in on your ongoing ride with driver {driver_name}. Press 1 if everything is fine and you feel safe. Press 2 if you need immediate assistance or feel unsafe.",
        "WeRide safety AI here. How is your ride going with driver {driver_name}? Press 1 if you're comfortable and safe. Press 2 if you have any safety concerns or need help.",
        "Hi, this is WeRide AI conducting a safety check. You're currently on a ride with {driver_name}. Press 1 to confirm you're safe and comfortable. Press 2 if you need emergency assistance."
    ],
    'ride_completed': [
        "Your WeRide journey is complete! You've arrived at {destination}. Total fare: {final_price} rupees. Driver: {driver_name}. We hope you had a pleasant experience. A feedback call will follow shortly.",
        "WeRide AI here! Trip completed successfully to {destination}. Final amount: {final_price} rupees. Thank you for riding with driver {driver_name}. Please expect a feedback call in a moment.",
        "Hello! Your WeRide trip has ended at {destination}. Total cost: {final_price} rupees. Driver {driver_name} thanks you for the ride. We'll call back shortly for your feedback."
    ],
    'feedback_request': [
        "Hi! WeRide AI here for your ride feedback. How was your experience with driver {driver_name} from {pickup} to {destination}? Press 1 for excellent, 2 for good, 3 for average, 4 for poor, or 5 if you had serious issues.",
        "WeRide feedback collection! Please rate your recent trip with {driver_name}. Route: {pickup} to {destination}. Press 1 for 5 stars, 2 for 4 stars, 3 for 3 stars, 4 for 2 stars, or 5 for 1 star.",
        "Hello! How was your WeRide experience? Driver: {driver_name}, Route: {pickup} to {destination}. Rate your trip: Press 1 for excellent service, 2 for good, 3 for okay, 4 for poor, or 5 for very poor."
    ],
    'ride_cancelled': [
        "WeRide AI notification: Your ride booking has been cancelled. Reason: {reason}. If this was unexpected, please contact our support. You can book a new ride anytime through our app.",
        "Hi! This is WeRide AI. Your ride from {pickup} to {destination} has been cancelled due to: {reason}. No charges applied. Feel free to book another ride when you're ready.",
        "WeRide update: Your booking for {pickup} to {destination} is cancelled. Reason: {reason}. We apologize for any inconvenience. You can make a new booking immediately."
    ],
    'payment_reminder': [
        "WeRide AI payment reminder: Your trip with {driver_name} costs {final_price} rupees. Please complete the payment to your driver. Trip: {pickup} to {destination}. Thank you!",
        "Payment reminder from WeRide AI! Please pay {final_price} rupees to driver {driver_name} for your ride from {pickup} to {destination}. We appreciate your prompt payment."
    ],
    'driver_delay': [
        "WeRide AI update: Your driver {driver_name} is running approximately {delay} minutes late due to {reason}. They'll reach you as soon as possible. We apologize for the delay.",
        "Hi! Driver {driver_name} is delayed by about {delay} minutes because of {reason}. They're still coming to pick you up. Thank you for your patience with WeRide."
    ]
}

# Import models and use their db instance
from db.models import db, User, Driver, Ride, RideOffer, RideTracking, Rating

# Initialize db with app
db.init_app(app)

# ─────────── MAIN DASHBOARD ───────────
@app.route("/")
def dashboard():
    return render_template('index.html', 
                         total_calls=len(call_logs),
                         active_rides=len(ride_bookings),
                         twilio_status='Connected' if twilio_client else 'Demo Mode')

# ─────────── BOOKING PAGE ───────────
@app.route("/book")
def book_ride():
    return render_template('book.html')

@app.route("/real-book")
def real_book_ride():
    """Enhanced booking page with InDrive-like features"""
    return render_template('real_book.html')

@app.route("/book", methods=["POST"])
def book_ride_post():
    name = request.form.get('name')
    phone = request.form.get('phone')
    pickup = request.form.get('pickup', 'Unknown')
    destination = request.form.get('destination', 'Unknown')
    
    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Create booking
    booking_id = f"WR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ride_bookings[booking_id] = {
        'id': booking_id,
        'name': name,
        'phone': phone,
        'pickup': pickup,
        'destination': destination,
        'status': 'booked',
        'created_at': datetime.now().isoformat()
    }
    
    # Trigger booking confirmation call
    if make_ai_call(phone, 'booking', {'booking_id': booking_id, 'name': name}):
        return jsonify({
            'success': True, 
            'booking_id': booking_id,
            'message': 'Ride booked successfully! You will receive a confirmation call.'
        })
    else:
        return jsonify({
            'success': True,
            'booking_id': booking_id, 
            'message': 'Ride booked successfully! (Demo mode - no actual call)'
        })

# ─────────── DYNAMIC AI VOICE CALL ───────────
@app.route("/voice-dynamic", methods=["POST"])
def voice_dynamic():
    message = request.form.get("message", "This is a default AI message.")
    voice = request.form.get("voice", "Polly.Joanna")  # Options: Polly.Matthew, Polly.Ivy, etc.

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" language="en-US">{message}</Say>
</Response>"""
    return Response(xml, mimetype='text/xml')

# ─────────── STATIC XML VOICE ROUTES ───────────
@app.route("/voice-arrival", methods=["POST"])
def voice_arrival():
    resp = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">
        Your WeRide driver has arrived. Please confirm before boarding.
    </Say>
</Response>"""
    return Response(resp, mimetype='text/xml')

@app.route("/voice-safety", methods=["POST"])
def voice_safety():
    resp = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather action="/safety-response" numDigits="1">
        <Say voice="Polly.Matthew" language="en-US">
            We detected a possible issue. Press 1 if you're safe. Press 2 if you need help.
        </Say>
    </Gather>
</Response>"""
    return Response(resp, mimetype='text/xml')

@app.route("/voice-feedback", methods=["POST"])
def voice_feedback():
    resp = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Ivy" language="en-US">
        How was your ride today? Press 1 for good, 2 for bad, or leave a short message after the tone.
    </Say>
</Response>"""
    return Response(resp, mimetype='text/xml')

# ─────────── CORE AI CALLER FUNCTIONS ───────────
def make_ai_call(phone_number, call_type, context=None):
    """Make an AI voice call using Twilio"""
    if not twilio_client:
        print(f"📱 DEMO: Would call {phone_number} with {call_type} message")
        # Log the demo call
        call_logs.append({
            'id': len(call_logs) + 1,
            'phone': phone_number,
            'type': call_type,
            'status': 'demo',
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        return False
    
    try:
        # Select AI response based on call type
        message = random.choice(AI_RESPONSES.get(call_type, AI_RESPONSES['booking']))
        
        # Create call using Twilio
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_BASE}/twiml/{call_type}",
            method='POST'
        )
        
        # Log the call
        call_logs.append({
            'id': len(call_logs) + 1,
            'phone': phone_number,
            'type': call_type,
            'status': 'initiated',
            'call_sid': call.sid,
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        
        print(f"📞 AI call initiated to {phone_number} - SID: {call.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Error making call to {phone_number}: {e}")
        call_logs.append({
            'id': len(call_logs) + 1,
            'phone': phone_number,
            'type': call_type,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        return False

# ─────────── ENHANCED AI CALLER FUNCTION ───────────
def make_contextual_ai_call(phone_number, call_type, ride_data=None):
    """Make a context-aware AI voice call with dynamic content"""
    if not twilio_client:
        print(f"📱 DEMO: Would call {phone_number} with {call_type} message (with context)")
        return False
    
    try:
        # Create call with dynamic TwiML URL containing context
        twiml_params = f"?call_type={call_type}"
        if ride_data:
            # Add ride context as URL parameters
            for key, value in ride_data.items():
                twiml_params += f"&{key}={value}"
        
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_BASE}/twiml-enhanced{twiml_params}",
            method='POST'
        )
        
        print(f"📞 Enhanced AI call initiated to {phone_number} - SID: {call.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Error making contextual call: {e}")
        return False

# ─────────── ENHANCED TWIML RESPONSE HANDLERS ───────────
@app.route("/twiml-enhanced", methods=["POST"])
def generate_enhanced_twiml():
    """Generate enhanced TwiML responses with context"""
    call_type = request.args.get('call_type', 'booking')
    response = VoiceResponse()
    
    # Get context data from URL parameters
    ride_id = request.args.get('ride_id')
    driver_name = request.args.get('driver_name', 'your driver')
    vehicle = request.args.get('vehicle', 'vehicle')
    plate = request.args.get('plate', 'unknown')
    pickup = request.args.get('pickup', 'your location')
    destination = request.args.get('destination', 'your destination')
    price = request.args.get('price', '0')
    eta = request.args.get('eta', '5')
    rating = request.args.get('rating', '5.0')
    
    try:
        if call_type == 'booking_confirmed':
            message_template = random.choice(AI_RESPONSES['booking_confirmed'])
            message = message_template.format(
                pickup=pickup,
                destination=destination,
                price=price,
                booking_id=ride_id or 'WR12345'
            )
            response.say(message, voice='Polly.Joanna', language='en-US')
            
        elif call_type == 'driver_assigned':
            message_template = random.choice(AI_RESPONSES['driver_assigned'])
            message = message_template.format(
                driver_name=driver_name,
                vehicle=vehicle,
                plate=plate,
                rating=rating,
                eta=eta
            )
            response.say(message, voice='Polly.Joanna', language='en-US')
            
        elif call_type == 'driver_arrived':
            message_template = random.choice(AI_RESPONSES['driver_arrived'])
            message = message_template.format(
                driver_name=driver_name,
                vehicle=vehicle,
                plate=plate
            )
            response.say(message, voice='Polly.Joanna', language='en-US')
            
            # Add interactive response gathering
            gather = Gather(numDigits=1, action='/handle-arrival-response-enhanced', method='POST')
            gather.say("Press 1 when you see your driver, or 2 if you need more time.", 
                      voice='Polly.Joanna', language='en-US')
            response.append(gather)
            
        elif call_type == 'safety_check':
            message_template = random.choice(AI_RESPONSES['safety_check'])
            message = message_template.format(driver_name=driver_name)
            
            gather = Gather(numDigits=1, action='/handle-safety-response-enhanced', method='POST')
            gather.say(message, voice='Polly.Matthew', language='en-US')
            response.append(gather)
            
        elif call_type == 'feedback_request':
            message_template = random.choice(AI_RESPONSES['feedback_request'])
            message = message_template.format(
                driver_name=driver_name,
                pickup=pickup,
                destination=destination
            )
            
            gather = Gather(numDigits=1, action='/handle-feedback-response-enhanced', method='POST')
            gather.say(message, voice='Polly.Ivy', language='en-US')
            response.append(gather)
            
        elif call_type == 'ride_completed':
            message_template = random.choice(AI_RESPONSES['ride_completed'])
            message = message_template.format(
                destination=destination,
                final_price=price,
                driver_name=driver_name
            )
            response.say(message, voice='Polly.Joanna', language='en-US')
            
        elif call_type == 'ride_cancelled':
            reason = request.args.get('reason', 'driver unavailable')
            message_template = random.choice(AI_RESPONSES['ride_cancelled'])
            message = message_template.format(
                pickup=pickup,
                destination=destination,
                reason=reason
            )
            response.say(message, voice='Polly.Joanna', language='en-US')
            
        else:
            # Fallback to basic response
            response.say("Hello from WeRide AI Assistant. Thank you for using our service.", 
                        voice='Polly.Joanna', language='en-US')
            
    except Exception as e:
        print(f"Error generating enhanced TwiML: {e}")
        response.say("Hello from WeRide AI Assistant. Thank you for using our service.", 
                    voice='Polly.Joanna', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

# ─────────── LEGACY TWIML RESPONSE HANDLERS ───────────
@app.route("/twiml/<call_type>", methods=["POST"])
def generate_twiml(call_type):
    """Generate TwiML responses for different call types (legacy support)"""
    response = VoiceResponse()
    
    if call_type == 'arrival':
        response.say("Your WeRide driver has arrived at your pickup location. Please come out when ready.", 
                    voice='Polly.Joanna', language='en-US')
        
        gather = Gather(numDigits=1, action='/handle-arrival-response', method='POST')
        gather.say("Press 1 to confirm you're coming out, or 2 if you need more time.", 
                  voice='Polly.Joanna', language='en-US')
        response.append(gather)
        
    elif call_type == 'safety':
        gather = Gather(numDigits=1, action='/handle-safety-response', method='POST')
        gather.say("WeRide AI safety check: Are you okay? Press 1 for yes, 2 if you need help immediately.", 
                  voice='Polly.Matthew', language='en-US')
        response.append(gather)
        
    elif call_type == 'feedback':
        gather = Gather(numDigits=1, action='/handle-feedback-response', method='POST')
        gather.say("Hi! This is WeRide AI. How was your ride? Press 1 for excellent, 2 for good, 3 for average, or 4 for poor.", 
                  voice='Polly.Ivy', language='en-US')
        response.append(gather)
        
    elif call_type == 'booking':
        response.say("Thank you for booking with WeRide! Your ride has been confirmed. We'll call you when your driver arrives.", 
                    voice='Polly.Joanna', language='en-US')
        
    else:
        response.say("Hello from WeRide AI Assistant. Thank you for using our service.", 
                    voice='Polly.Joanna', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

# ─────────── RESPONSE HANDLERS ───────────
@app.route("/handle-arrival-response", methods=["POST"])
def handle_arrival_response():
    """Handle user response to arrival call"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    if digit_pressed == '1':
        response.say("Great! Your driver will wait for you. Have a safe ride!", 
                    voice='Polly.Joanna', language='en-US')
    elif digit_pressed == '2':
        response.say("No problem! Take your time. Your driver has been notified.", 
                    voice='Polly.Joanna', language='en-US')
    else:
        response.say("Thank you for your response. Have a great day!", 
                    voice='Polly.Joanna', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

@app.route("/handle-safety-response", methods=["POST"])
def handle_safety_response():
    """Handle user response to safety call"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    if digit_pressed == '1':
        response.say("Great to hear you're safe! Continue with your ride.", 
                    voice='Polly.Matthew', language='en-US')
    elif digit_pressed == '2':
        response.say("We're connecting you to emergency services immediately. Stay on the line.", 
                    voice='Polly.Matthew', language='en-US')
        # In production, trigger emergency response
    else:
        response.say("If this is an emergency, please call emergency services directly.", 
                    voice='Polly.Matthew', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

@app.route("/handle-feedback-response", methods=["POST"])
def handle_feedback_response():
    """Handle user response to feedback call (legacy)"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    feedback_responses = {
        '1': "Thank you for the excellent rating! We're glad you enjoyed your ride.",
        '2': "Thanks for the good rating! We appreciate your feedback.",
        '3': "Thank you for your feedback. We'll work to improve our service.",
        '4': "We're sorry about the issues. A customer service representative will contact you soon."
    }
    
    message = feedback_responses.get(digit_pressed, "Thank you for your feedback!")
    response.say(message, voice='Polly.Ivy', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

# ─────────── ENHANCED INTERACTIVE RESPONSE HANDLERS ───────────
@app.route("/handle-arrival-response-enhanced", methods=["POST"])
def handle_arrival_response_enhanced():
    """Handle enhanced user response to arrival call"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    if digit_pressed == '1':
        response.say("Perfect! We've notified your driver that you're on your way out. Please look for their vehicle and confirm with them before getting in. Have a safe and pleasant ride with WeRide!", 
                    voice='Polly.Joanna', language='en-US')
    elif digit_pressed == '2':
        response.say("No problem! We've let your driver know you need a few more minutes. They'll wait for you. Please come out as soon as you're ready. Thank you for using WeRide!", 
                    voice='Polly.Joanna', language='en-US')
    else:
        response.say("Thank you for responding to WeRide AI assistant. If you need any assistance, please call our support line. Have a great day!", 
                    voice='Polly.Joanna', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

@app.route("/handle-safety-response-enhanced", methods=["POST"])
def handle_safety_response_enhanced():
    """Handle enhanced user response to safety call"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    if digit_pressed == '1':
        response.say("Excellent! We're happy to confirm you're safe and comfortable during your WeRide journey. Continue enjoying your ride. We may check in again if the trip is long. Thank you!", 
                    voice='Polly.Matthew', language='en-US')
    elif digit_pressed == '2':
        response.say("We understand you need immediate assistance. WeRide emergency protocol is now activated. We're connecting you to our emergency response team and local authorities. Please stay on the line and provide your location.", 
                    voice='Polly.Matthew', language='en-US')
        # In production, trigger emergency response system
        # - Contact emergency services
        # - Alert WeRide safety team  
        # - Track ride location
        # - Notify emergency contacts
    else:
        response.say("This is WeRide safety monitoring. If you're in immediate danger, please call emergency services directly at your local emergency number. For non-urgent issues, contact WeRide support.", 
                    voice='Polly.Matthew', language='en-US')
    
    return Response(str(response), mimetype='text/xml')

@app.route("/handle-feedback-response-enhanced", methods=["POST"])
def handle_feedback_response_enhanced():
    """Handle enhanced user response to feedback call"""
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()
    
    enhanced_feedback_responses = {
        '1': "Fantastic! We're thrilled you had an excellent WeRide experience. Your 5-star rating means the world to us and your driver. Thank you for choosing WeRide, and we look forward to serving you again soon!",
        '2': "Great to hear you had a good ride! Your positive feedback helps us maintain high service standards. We appreciate you taking the time to rate your WeRide experience. Thank you for riding with us!",
        '3': "Thank you for your honest feedback. We value all passenger input as it helps us improve our WeRide service. We'll take note of your experience and work to make your next ride even better.",
        '4': "We're sorry to hear your ride wasn't up to your expectations. Your feedback is important to us. A WeRide customer service representative will contact you within 24 hours to discuss your experience and make things right.",
        '5': "We sincerely apologize for the serious issues you experienced during your WeRide trip. This is not the standard we strive for. A senior customer service manager will call you within 2 hours to personally address your concerns and ensure this doesn't happen again."
    }
    
    message = enhanced_feedback_responses.get(digit_pressed, "Thank you for providing feedback to WeRide AI assistant. Your input helps us improve our service quality.")
    response.say(message, voice='Polly.Ivy', language='en-US')
    
    # In production, log the feedback rating to database
    # and trigger appropriate follow-up actions based on rating
    
    return Response(str(response), mimetype='text/xml')

# ─────────── API TRIGGER ROUTE ───────────
@app.route("/api/trigger-call", methods=["POST"])
def api_trigger_call():
    """API endpoint to trigger different types of calls"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    phone = data.get('phone')
    call_type = data.get('type')
    
    if not phone or not call_type:
        return jsonify({'success': False, 'error': 'Phone and type are required'}), 400
    
    try:
        if call_type == 'arrival':
            result = make_ai_call(phone, 'arrival', {'trigger': 'manual'})
        elif call_type == 'safety':
            result = make_ai_call(phone, 'safety', {'trigger': 'manual'})
        elif call_type == 'feedback':
            result = make_ai_call(phone, 'feedback', {'trigger': 'manual'})
        else:
            return jsonify({'success': False, 'error': 'Invalid call type'}), 400
        
        if result:
            return jsonify({'success': True, 'message': f'{call_type.title()} call initiated successfully'})
        else:
            return jsonify({'success': True, 'message': f'{call_type.title()} call logged in demo mode'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ─────────── INDRIVE-LIKE FEATURES ───────────

@app.route("/api/create-ride", methods=["POST"])
def create_real_ride():
    """Create a real ride with InDrive-like features"""
    data = request.get_json()
    
    try:
        # Get or create passenger
        passenger = User.query.filter_by(phone=data['phone']).first()
        if not passenger:
            passenger = User(
                name=data['name'],
                phone=data['phone'],
                user_type='passenger'
            )
            db.session.add(passenger)
            db.session.commit()
        
        # Create ride with passenger's price offer
        ride = Ride(
            passenger_id=passenger.id,
            pickup_address=data['pickup'],
            destination_address=data['destination'],
            passenger_offer=float(data['price_offer']),
            pickup_lat=data.get('pickup_lat'),
            pickup_lng=data.get('pickup_lng'),
            destination_lat=data.get('dest_lat'),
            destination_lng=data.get('dest_lng')
        )
        
        db.session.add(ride)
        db.session.commit()
        
        # Trigger AI confirmation call
        make_ai_call(passenger.phone, 'booking', {'ride_id': ride.id})
        
        return jsonify({
            'success': True,
            'ride_id': ride.id,
            'message': 'Ride created! Drivers will see your request.',
            'passenger_offer': ride.passenger_offer
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/available-rides")
def get_available_rides():
    """Get available rides for drivers"""
    rides = Ride.query.filter_by(status='pending').all()
    
    rides_data = []
    for ride in rides:
        rides_data.append({
            'id': ride.id,
            'pickup': ride.pickup_address,
            'destination': ride.destination_address,
            'passenger_offer': ride.passenger_offer,
            'passenger_name': ride.passenger.name,
            'distance': ride.estimated_distance or 'Calculating...',
            'created_at': ride.requested_at.isoformat()
        })
    
    return jsonify({'rides': rides_data})

@app.route("/api/make-offer", methods=["POST"])
def driver_make_offer():
    """Driver makes counter-offer for a ride"""
    data = request.get_json()
    
    try:
        # Get or create driver
        driver = User.query.filter_by(phone=data['driver_phone']).first()
        if not driver:
            driver = User(
                name=data['driver_name'],
                phone=data['driver_phone'],
                user_type='driver'
            )
            db.session.add(driver)
            db.session.commit()
        
        # Create ride offer
        offer = RideOffer(
            ride_id=data['ride_id'],
            driver_id=driver.id,
            offered_price=float(data['offered_price']),
            estimated_pickup_time=data.get('pickup_time', 5),
            message=data.get('message', '')
        )
        
        db.session.add(offer)
        db.session.commit()
        
        # Notify passenger via AI call about new offer
        ride = Ride.query.get(data['ride_id'])
        make_ai_call(ride.passenger.phone, 'arrival', {
            'message': f'You have a new offer from {driver.name} for ${offer.offered_price}',
            'ride_id': ride.id,
            'offer_id': offer.id
        })
        
        return jsonify({
            'success': True,
            'offer_id': offer.id,
            'message': 'Offer sent to passenger!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/accept-offer", methods=["POST"])
def accept_offer():
    """Passenger accepts a driver's offer"""
    data = request.get_json()
    
    try:
        offer = RideOffer.query.get(data['offer_id'])
        ride = offer.ride
        
        # Update ride status
        ride.driver_id = offer.driver_id
        ride.final_price = offer.offered_price
        ride.status = 'accepted'
        ride.accepted_at = datetime.utcnow()
        
        # Update offer status
        offer.status = 'accepted'
        
        # Reject other offers
        other_offers = RideOffer.query.filter_by(ride_id=ride.id).filter(RideOffer.id != offer.id).all()
        for other_offer in other_offers:
            other_offer.status = 'rejected'
        
        db.session.commit()
        
        # AI call to both driver and passenger
        make_ai_call(offer.driver.phone, 'booking', {
            'message': f'Congratulations! Your offer was accepted. Pickup: {ride.pickup_address}',
            'ride_id': ride.id
        })
        
        make_ai_call(ride.passenger.phone, 'booking', {
            'message': f'Your ride is confirmed! Driver {offer.driver.name} will pick you up.',
            'ride_id': ride.id
        })
        
        return jsonify({
            'success': True,
            'message': 'Ride confirmed!',
            'driver_name': offer.driver.name,
            'final_price': ride.final_price
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/update-driver-location", methods=["POST"])
def update_driver_location():
    """Update driver's real-time location"""
    data = request.get_json()
    
    try:
        driver = User.query.filter_by(phone=data['driver_phone']).first()
        if not driver:
            return jsonify({'success': False, 'error': 'Driver not found'}), 404
        
        # Update driver location in driver profile
        if driver.driver_profile:
            driver.driver_profile.current_lat = data['lat']
            driver.driver_profile.current_lng = data['lng']
            driver.driver_profile.last_location_update = datetime.utcnow()
        
        # If driver has active ride, track location
        active_ride = Ride.query.filter_by(driver_id=driver.id, status='accepted').first()
        if active_ride:
            tracking = RideTracking(
                ride_id=active_ride.id,
                driver_lat=data['lat'],
                driver_lng=data['lng']
            )
            db.session.add(tracking)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Location updated'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/driver-arrived", methods=["POST"])
def driver_arrived():
    """Mark driver as arrived and trigger AI call"""
    data = request.get_json()
    
    try:
        ride = Ride.query.get(data['ride_id'])
        ride.status = 'arrived'
        ride.pickup_time = datetime.utcnow()
        
        db.session.commit()
        
        # Trigger AI arrival call
        if not ride.arrival_call_made:
            make_ai_call(ride.passenger.phone, 'arrival', {'ride_id': ride.id})
            ride.arrival_call_made = True
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Passenger notified of arrival via AI call!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/complete-ride", methods=["POST"])
def complete_ride():
    """Mark ride as completed and trigger feedback AI call"""
    data = request.get_json()
    
    try:
        ride = Ride.query.get(data['ride_id'])
        ride.status = 'completed'
        ride.completed_at = datetime.utcnow()
        
        # Update total rides for both users
        ride.passenger.total_rides += 1
        ride.driver.total_rides += 1
        
        db.session.commit()
        
        # Trigger feedback AI call
        if not ride.feedback_call_made:
            make_ai_call(ride.passenger.phone, 'feedback', {'ride_id': ride.id})
            ride.feedback_call_made = True
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ride completed! Feedback call initiated.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/online-drivers")
def get_online_drivers():
    """Get list of online drivers with their locations"""
    drivers = db.session.query(User, Driver).join(Driver, User.id == Driver.user_id).filter(Driver.is_online == True).all()
    
    drivers_data = []
    for user, driver in drivers:
        drivers_data.append({
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'rating': user.rating,
            'vehicle': f"{driver.vehicle_make} {driver.vehicle_model}",
            'license_plate': driver.license_plate,
            'current_lat': driver.current_lat,
            'current_lng': driver.current_lng,
            'hourly_rate': driver.hourly_rate
        })
    
    return jsonify({'drivers': drivers_data})

# ─────────── DASHBOARD WITH REAL DATA ───────────
@app.route("/dashboard")
def real_dashboard():
    """Dashboard showing real ride statistics"""
    total_rides = Ride.query.count()
    active_rides = Ride.query.filter(Ride.status.in_(['pending', 'accepted', 'arrived', 'in_progress'])).count()
    total_drivers = User.query.filter_by(user_type='driver').count()
    online_drivers = db.session.query(Driver).filter_by(is_online=True).count()
    
    recent_rides = Ride.query.order_by(Ride.requested_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_rides=total_rides,
                         active_rides=active_rides,
                         total_drivers=total_drivers,
                         online_drivers=online_drivers,
                         recent_rides=recent_rides,
                         twilio_status='Connected' if twilio_client else 'Demo Mode')

# ─────────── TRIGGER ROUTES ───────────
@app.route("/arrival", methods=["POST"])
def arrival_trigger():
    phone = request.form['phone']
    on_driver_arrival(phone)
    return "✅ Arrival call triggered"

@app.route("/cancel", methods=["POST"])
def cancel_trigger():
    phone = request.form['phone']
    on_ride_cancelled(phone)
    return "✅ Cancellation SMS sent"

@app.route("/safety", methods=["POST"])
def safety_trigger():
    phone = request.form['phone']
    on_safety_issue(phone)
    return "📞 Safety alert call triggered"

@app.route("/feedback", methods=["POST"])
def feedback_trigger():
    phone = request.form['phone']
    on_feedback_request(phone)
    return "📞 Feedback call sent"

# ─────────── DATABASE INITIALIZATION ───────────
def create_tables():
    """Create database tables and add sample data"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")

# ─────────── FLASK RUN ───────────
if __name__ == "__main__":
    app.run(debug=True)
