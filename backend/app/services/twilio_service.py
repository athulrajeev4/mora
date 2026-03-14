"""
Twilio Service - Voice Call Management
"""
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.config import settings


class TwilioService:
    """Service for managing Twilio voice calls"""
    
    def __init__(self):
        """Initialize Twilio client with credentials"""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
    
    def make_call(
        self,
        to_phone: str,
        twiml_url: str,
        status_callback_url: str,
        recording_status_callback_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Initiate an outbound voice call
        
        Args:
            to_phone: Destination phone number (E.164 format)
            twiml_url: URL that returns TwiML instructions for the call
            status_callback_url: URL for call status updates (webhooks)
            recording_status_callback_url: URL for recording status updates
            
        Returns:
            call_sid: Twilio Call SID if successful, None if failed
        """
        try:
            call = self.client.calls.create(
                to=to_phone,
                from_=self.from_phone,
                url=twiml_url,
                status_callback=status_callback_url,
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST',
                record=True,  # Enable call recording
                recording_status_callback=recording_status_callback_url,
                recording_status_callback_method='POST'
            )
            
            return call.sid
            
        except TwilioRestException as e:
            print(f"Twilio API Error: {e.code} - {e.msg}")
            return None
        except Exception as e:
            print(f"Error making call: {str(e)}")
            return None
    
    def get_call_status(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a call
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            Dictionary with call details (status, duration, etc.)
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
            
        except TwilioRestException as e:
            print(f"Error fetching call: {e.code} - {e.msg}")
            return None
    
    def get_call_recordings(self, call_sid: str) -> list:
        """
        Get all recordings for a specific call
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            List of recording dictionaries with URLs
        """
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            
            return [
                {
                    "sid": rec.sid,
                    "duration": rec.duration,
                    "url": f"https://api.twilio.com{rec.uri.replace('.json', '.mp3')}",
                    "date_created": rec.date_created
                }
                for rec in recordings
            ]
            
        except TwilioRestException as e:
            print(f"Error fetching recordings: {e.code} - {e.msg}")
            return []
    
    def get_transcription(self, recording_sid: str) -> Optional[str]:
        """
        Get transcription for a recording
        
        Args:
            recording_sid: Twilio Recording SID
            
        Returns:
            Transcription text if available
        """
        try:
            transcriptions = self.client.recordings(recording_sid).transcriptions.list()
            
            if transcriptions:
                return transcriptions[0].transcription_text
            return None
            
        except TwilioRestException as e:
            print(f"Error fetching transcription: {e.code} - {e.msg}")
            return None
        except Exception as e:
            print(f"Transcription lookup not available: {str(e)}")
            return None
    
    def hangup_call(self, call_sid: str) -> bool:
        """
        Terminate an active call
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            call = self.client.calls(call_sid).update(status='completed')
            return call.status == 'completed'
            
        except TwilioRestException as e:
            print(f"Error hanging up call: {e.code} - {e.msg}")
            return False


    async def make_outbound_test_call(
        self,
        to_phone: str,
        room_name: str,
        sip_uri: str,
        test_run_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Make outbound call to user's bot and connect to LiveKit room via SIP
        
        This is for TEST CALLS where our AI caller calls the user's bot.
        The call is connected to a LiveKit room where our AI agent is waiting.
        
        Args:
            to_phone: User's bot phone number to call (e.164 format)
            room_name: LiveKit room name where AI agent is waiting
            sip_uri: SIP URI to connect the call to LiveKit
            test_run_id: Optional test run ID for webhook routing
            
        Returns:
            call_sid: Twilio Call SID if successful, None if failed
        """
        try:
            from twilio.twiml.voice_response import VoiceResponse, Dial
            
            response = VoiceResponse()
            dial = Dial()
            
            dial.sip(sip_uri)
            response.append(dial)
            
            twiml_str = str(response)
            
            # Build webhook URLs that match actual route definitions
            status_url = None
            recording_url = None
            if settings.PUBLIC_URL and test_run_id:
                status_url = f"{settings.PUBLIC_URL}/api/webhooks/twilio/status/{test_run_id}"
                recording_url = f"{settings.PUBLIC_URL}/api/webhooks/twilio/recording/{test_run_id}"
            
            call_kwargs = dict(
                to=to_phone,
                from_=self.from_phone,
                twiml=twiml_str,
                record=True,
                timeout=60,
            )
            
            if status_url:
                call_kwargs["status_callback"] = status_url
                call_kwargs["status_callback_event"] = ['initiated', 'ringing', 'answered', 'completed']
                call_kwargs["status_callback_method"] = 'POST'
            
            if recording_url:
                call_kwargs["recording_status_callback"] = recording_url
                call_kwargs["recording_status_callback_method"] = 'POST'
            
            call = self.client.calls.create(**call_kwargs)
            
            return call.sid
            
        except TwilioRestException as e:
            print(f"Twilio API Error making outbound test call: {e.code} - {e.msg}")
            return None
        except Exception as e:
            print(f"Error making outbound test call: {str(e)}")
            return None


# Singleton instance
twilio_service = TwilioService()
