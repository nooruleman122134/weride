"""
Twilio Configuration and Setup
==============================

This module centralizes all Twilio-related configuration and provides
helper functions for managing Twilio services including voice calls,
SMS, and webhooks.
"""

import os
from twilio.rest import Client
from twilio.twiml import VoiceResponse
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioConfig:
    """Twilio configuration and client management"""
    
    def __init__(self):
        # Load Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.receiver_number = os.getenv('RECEIVER_NUMBER')
        self.ngrok_base = os.getenv('NGROK_BASE', 'https://your-domain.com')
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Missing required Twilio credentials in environment variables")
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        logger.info(f"Twilio configured with phone number: {self.phone_number}")
    
    def get_client(self):
        """Get the Twilio client instance"""
        return self.client
    
    def get_webhook_url(self, endpoint):
        """Generate webhook URL for Twilio callbacks"""
        return f"{self.ngrok_base.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def make_call(self, to_number, twiml_url, **kwargs):
        """
        Make a voice call using Twilio
        
        Args:
            to_number: Phone number to call
            twiml_url: URL that returns TwiML instructions
            **kwargs: Additional call parameters (timeout, etc.)
        
        Returns:
            Twilio call SID or None if failed
        """
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=twiml_url,
                timeout=kwargs.get('timeout', 30),
                **kwargs
            )
            logger.info(f"Call initiated: {call.sid} to {to_number}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to make call to {to_number}: {str(e)}")
            return None
    
    def send_sms(self, to_number, message):
        """
        Send SMS using Twilio
        
        Args:
            to_number: Phone number to send SMS to
            message: SMS content
        
        Returns:
            Message SID or None if failed
        """
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.phone_number,
                body=message
            )
            logger.info(f"SMS sent: {message.sid} to {to_number}")
            return message.sid
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return None

class TwiMLBuilder:
    """Helper class for building TwiML responses"""
    
    @staticmethod
    def create_voice_response():
        """Create a new VoiceResponse object"""
        return VoiceResponse()
    
    @staticmethod
    def simple_message(message, voice='alice', language='en-US'):
        """
        Create a simple voice message TwiML
        
        Args:
            message: Text to speak
            voice: Twilio voice to use
            language: Language code
        
        Returns:
            TwiML string
        """
        response = VoiceResponse()
        response.say(message, voice=voice, language=language)
        return str(response)
    
    @staticmethod
    def interactive_message(message, action_url, timeout=10, num_digits=1, finish_on_key='#'):
        """
        Create an interactive voice message with keypad input
        
        Args:
            message: Text to speak before gathering input
            action_url: URL to send the gathered input
            timeout: Seconds to wait for input
            num_digits: Number of digits to collect
            finish_on_key: Key to finish input collection
        
        Returns:
            TwiML string
        """
        response = VoiceResponse()
        gather = response.gather(
            action=action_url,
            method='POST',
            timeout=timeout,
            num_digits=num_digits,
            finish_on_key=finish_on_key
        )
        gather.say(message, voice='alice', language='en-US')
        
        # Fallback if no input received
        response.say("We didn't receive your input. Thank you for calling WeRide!", 
                    voice='alice', language='en-US')
        
        return str(response)
    
    @staticmethod
    def redirect_message(redirect_url):
        """
        Create a TwiML response that redirects to another URL
        
        Args:
            redirect_url: URL to redirect the call to
        
        Returns:
            TwiML string
        """
        response = VoiceResponse()
        response.redirect(redirect_url)
        return str(response)

# AI Voice Message Templates
class AIVoiceTemplates:
    """Pre-defined AI voice message templates for different ride statuses"""
    
    @staticmethod
    def booking_confirmation(passenger_name, ride_id, pickup_location, destination):
        """Booking confirmation message"""
        return f"""
        Hello {passenger_name}! This is WeRide AI calling to confirm your booking.
        Your ride has been successfully booked with ID {ride_id}.
        We will pick you up from {pickup_location} and take you to {destination}.
        We're finding the best driver for you. You'll receive another call when a driver is assigned.
        Thank you for choosing WeRide!
        """
    
    @staticmethod
    def driver_assigned(passenger_name, driver_name, vehicle_info, eta_minutes):
        """Driver assignment notification"""
        return f"""
        Hello {passenger_name}! Great news from WeRide AI.
        Your driver {driver_name} has been assigned to your ride.
        They're driving a {vehicle_info} and will arrive in approximately {eta_minutes} minutes.
        You can track your driver's location in the WeRide app.
        We'll call you again when your driver arrives at the pickup location.
        """
    
    @staticmethod
    def driver_arrival(passenger_name, driver_name, location):
        """Driver arrival notification with interaction"""
        return f"""
        Hello {passenger_name}! This is WeRide AI.
        Your driver {driver_name} has arrived at {location}.
        Please come to the pickup point and look for your assigned vehicle.
        If you can see your driver and are ready to start your ride, press 1.
        If you need more time or can't find your driver, press 2.
        If you want to cancel this ride, press 3.
        """
    
    @staticmethod
    def safety_check(passenger_name, driver_name):
        """Mid-ride safety check with interaction"""
        return f"""
        Hello {passenger_name}! This is WeRide AI conducting a routine safety check.
        You're currently on a ride with driver {driver_name}.
        If everything is going well and you feel safe, press 1.
        If you need assistance or feel unsafe, press 9 immediately.
        If you don't respond, we'll follow up with additional safety measures.
        Your safety is our top priority.
        """
    
    @staticmethod
    def ride_completion(passenger_name, destination, fare):
        """Ride completion notification"""
        return f"""
        Hello {passenger_name}! This is WeRide AI.
        Your ride to {destination} has been completed successfully.
        The total fare is ${fare}.
        We hope you had a pleasant journey with WeRide.
        You'll receive a receipt via email shortly.
        Thank you for choosing WeRide for your transportation needs!
        """
    
    @staticmethod
    def feedback_request(passenger_name, driver_name):
        """Post-ride feedback collection"""
        return f"""
        Hello {passenger_name}! This is WeRide AI.
        We hope you enjoyed your ride with driver {driver_name}.
        We'd love to hear about your experience to help us improve our service.
        To rate your ride, press a number from 1 to 5, where 5 is excellent and 1 is poor.
        Press 5 for excellent, 4 for good, 3 for average, 2 for below average, or 1 for poor.
        Your feedback helps us maintain high service quality.
        """

# Call Status Templates
class CallStatusTemplates:
    """Templates for different call status scenarios"""
    
    @staticmethod
    def driver_delay(passenger_name, driver_name, new_eta):
        """Driver delay notification"""
        return f"""
        Hello {passenger_name}! This is WeRide AI with an update.
        Your driver {driver_name} is experiencing a slight delay due to traffic conditions.
        The new estimated arrival time is {new_eta} minutes.
        We apologize for any inconvenience and appreciate your patience.
        You can track the driver's real-time location in the WeRide app.
        """
    
    @staticmethod
    def ride_cancellation(passenger_name, reason, refund_info=None):
        """Ride cancellation notification"""
        base_message = f"""
        Hello {passenger_name}! This is WeRide AI calling about your recent booking.
        Unfortunately, your ride has been cancelled due to {reason}.
        We sincerely apologize for the inconvenience.
        """
        
        if refund_info:
            base_message += f" {refund_info}"
        
        base_message += """
        You can immediately book a new ride through the WeRide app.
        Thank you for your understanding and for choosing WeRide.
        """
        
        return base_message
    
    @staticmethod
    def payment_reminder(passenger_name, amount, ride_date):
        """Payment reminder for outstanding rides"""
        return f"""
        Hello {passenger_name}! This is WeRide AI calling regarding your ride on {ride_date}.
        We notice there's an outstanding payment of ${amount} for your recent trip.
        Please complete the payment through the WeRide app at your earliest convenience.
        If you've already made the payment, please disregard this call.
        For payment assistance, you can contact our support team.
        Thank you for using WeRide!
        """

# Response handlers for interactive calls
class CallResponseHandlers:
    """Handle responses from interactive voice calls"""
    
    @staticmethod
    def handle_arrival_response(digits):
        """Handle driver arrival response"""
        response = VoiceResponse()
        
        if digits == '1':
            response.say(
                "Perfect! Your driver will wait for you to board. "
                "Have a safe and pleasant ride with WeRide!",
                voice='alice'
            )
        elif digits == '2':
            response.say(
                "No problem! We've notified your driver that you need more time. "
                "They will wait for you. Please board when you're ready.",
                voice='alice'
            )
        elif digits == '3':
            response.say(
                "We understand. Your ride has been cancelled. "
                "You can book a new ride anytime through the WeRide app. "
                "Thank you for using WeRide!",
                voice='alice'
            )
        else:
            response.say(
                "We didn't recognize your input. "
                "Please contact WeRide support if you need assistance. "
                "Thank you for using WeRide!",
                voice='alice'
            )
        
        return str(response)
    
    @staticmethod
    def handle_safety_response(digits):
        """Handle safety check response"""
        response = VoiceResponse()
        
        if digits == '1':
            response.say(
                "Thank you for confirming your safety. "
                "Enjoy the rest of your ride with WeRide!",
                voice='alice'
            )
        elif digits == '9':
            # Emergency response - this should trigger actual emergency protocols
            response.say(
                "Emergency assistance has been requested. "
                "We're immediately connecting you to our safety team and local authorities. "
                "Stay on the line.",
                voice='alice'
            )
            # TODO: Integrate with emergency services and safety team
            # emergency_service.trigger_emergency_response(call_info)
        else:
            response.say(
                "We're concerned about your safety since we didn't receive a clear response. "
                "Our safety team will follow up with you shortly. "
                "If this is an emergency, please call local emergency services immediately.",
                voice='alice'
            )
            # TODO: Trigger safety follow-up protocol
        
        return str(response)
    
    @staticmethod
    def handle_feedback_response(digits):
        """Handle feedback rating response"""
        response = VoiceResponse()
        
        ratings = {
            '5': 'excellent',
            '4': 'good', 
            '3': 'average',
            '2': 'below average',
            '1': 'poor'
        }
        
        if digits in ratings:
            response.say(
                f"Thank you for rating your ride as {ratings[digits]}! "
                "Your feedback helps us improve our service. "
                "We appreciate you choosing WeRide and look forward to serving you again!",
                voice='alice'
            )
            # TODO: Store rating in database
            # feedback_service.store_rating(ride_id, rating=int(digits))
        else:
            response.say(
                "Thank you for your time. "
                "If you'd like to provide feedback later, "
                "you can do so through the WeRide app. "
                "We appreciate you choosing WeRide!",
                voice='alice'
            )
        
        return str(response)

# Global instance
twilio_config = TwilioConfig()

# Convenience functions
def make_ai_call(to_number, message_type, **context):
    """
    Make an AI call with the specified message type
    
    Args:
        to_number: Phone number to call
        message_type: Type of AI message to send
        **context: Context variables for the message template
    
    Returns:
        Call SID if successful, None otherwise
    """
    webhook_url = twilio_config.get_webhook_url(f'/ai-call/{message_type}')
    
    # Add context as URL parameters
    if context:
        params = '&'.join([f'{k}={v}' for k, v in context.items()])
        webhook_url += f'?{params}'
    
    return twilio_config.make_call(to_number, webhook_url)

def send_notification_sms(to_number, message_type, **context):
    """Send SMS notification"""
    # Create appropriate SMS message based on type
    messages = {
        'booking_confirmed': f"WeRide: Your ride has been confirmed! Booking ID: {context.get('ride_id', 'N/A')}",
        'driver_assigned': f"WeRide: Driver {context.get('driver_name', 'assigned')} is on the way! ETA: {context.get('eta_minutes', 'TBD')} min",
        'driver_arrived': f"WeRide: Your driver has arrived at the pickup location!",
        'ride_completed': f"WeRide: Ride completed! Fare: ${context.get('fare', '0.00')}. Thank you!",
    }
    
    message = messages.get(message_type, "WeRide: Thank you for using our service!")
    return twilio_config.send_sms(to_number, message)

if __name__ == "__main__":
    # Test configuration
    print(f"Twilio Phone Number: {twilio_config.phone_number}")
    print(f"Webhook Base URL: {twilio_config.ngrok_base}")
    print("Twilio configuration loaded successfully!")
