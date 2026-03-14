"""
Twilio Media Stream to LiveKit Bridge
Handles WebSocket connection from Twilio and forwards audio to LiveKit room
"""

import asyncio
import base64
import json
import logging
from typing import Optional, Dict
from fastapi import WebSocket, WebSocketDisconnect
from livekit import api, rtc
from app.core.config import settings

logger = logging.getLogger(__name__)


class TwilioLiveKitBridge:
    """
    Bridges Twilio Media Stream (WebSocket) to LiveKit Room
    - Receives audio from Twilio call (mulaw 8kHz)
    - Converts and sends to LiveKit room
    - Receives audio from LiveKit agent
    - Sends back to Twilio call
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        room_name: str,
        test_run_id: str
    ):
        self.websocket = websocket
        self.room_name = room_name
        self.test_run_id = test_run_id
        
        # LiveKit components
        self.lk_room: Optional[rtc.Room] = None
        self.lk_source: Optional[rtc.AudioSource] = None
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        
        # Audio configuration
        self.sample_rate = 8000  # Twilio uses 8kHz mulaw
        self.channels = 1
        self.bytes_per_sample = 2  # 16-bit audio
        
        logger.info(f"🌉 Bridge initialized for room: {room_name}")
    
    async def connect_to_livekit(self) -> bool:
        """
        Connect to LiveKit room as a participant
        """
        try:
            # Create access token for this bridge participant
            token = api.AccessToken(
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
            )
            token.with_identity(f"twilio-{self.test_run_id}")
            token.with_name("Twilio Caller")
            token.with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            
            # Connect to room
            self.lk_room = rtc.Room()
            await self.lk_room.connect(
                url=settings.LIVEKIT_URL,
                token=token.to_jwt()
            )
            
            # Create audio source for publishing Twilio audio
            self.lk_source = rtc.AudioSource(
                sample_rate=self.sample_rate,
                num_channels=self.channels
            )
            
            # Publish audio track
            track = rtc.LocalAudioTrack.create_audio_track("caller-audio", self.lk_source)
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            await self.lk_room.local_participant.publish_track(track, options)
            
            logger.info(f"✅ Connected to LiveKit room: {self.room_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to LiveKit: {e}")
            return False
    
    async def handle_twilio_stream(self):
        """
        Main handler for Twilio Media Stream WebSocket
        """
        try:
            # Accept WebSocket connection
            await self.websocket.accept()
            logger.info(f"📞 Twilio WebSocket connected for test run: {self.test_run_id}")
            
            # Connect to LiveKit
            if not await self.connect_to_livekit():
                await self.websocket.close()
                return
            
            # Process messages from Twilio
            while True:
                try:
                    # Receive message from Twilio
                    data = await self.websocket.receive_text()
                    message = json.loads(data)
                    
                    event = message.get("event")
                    
                    if event == "start":
                        # Stream started
                        self.stream_sid = message["start"]["streamSid"]
                        self.call_sid = message["start"]["callSid"]
                        logger.info(f"🎬 Stream started: {self.stream_sid}")
                        
                    elif event == "media":
                        # Audio payload from caller
                        payload = message["media"]["payload"]
                        
                        # Decode mulaw audio (base64 -> bytes)
                        audio_data = base64.b64decode(payload)
                        
                        # Convert mulaw to PCM16 and send to LiveKit
                        await self._forward_audio_to_livekit(audio_data)
                        
                    elif event == "stop":
                        # Stream ended
                        logger.info(f"🛑 Stream stopped: {self.stream_sid}")
                        break
                        
                except WebSocketDisconnect:
                    logger.info(f"📵 Twilio WebSocket disconnected")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error in Twilio stream handler: {e}")
            
        finally:
            # Cleanup
            await self._cleanup()
    
    async def _forward_audio_to_livekit(self, mulaw_data: bytes):
        """
        Convert mulaw audio to PCM16 and send to LiveKit
        """
        try:
            # Convert mulaw to PCM16
            import audioop
            pcm_data = audioop.ulaw2lin(mulaw_data, 2)
            
            # Create audio frame
            frame = rtc.AudioFrame(
                data=pcm_data,
                sample_rate=self.sample_rate,
                num_channels=self.channels,
                samples_per_channel=len(pcm_data) // (self.channels * self.bytes_per_sample)
            )
            
            # Capture audio to source
            await self.lk_source.capture_frame(frame)
            
        except Exception as e:
            logger.error(f"❌ Error forwarding audio to LiveKit: {e}")
    
    async def _cleanup(self):
        """
        Clean up connections
        """
        try:
            if self.lk_room:
                await self.lk_room.disconnect()
            logger.info(f"🧹 Bridge cleaned up for room: {self.room_name}")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def handle_twilio_websocket(
    websocket: WebSocket,
    test_run_id: str,
    room_name: str
):
    """
    Main entry point for Twilio Media Stream WebSocket connection
    
    Args:
        websocket: FastAPI WebSocket connection from Twilio
        test_run_id: UUID of the test run
        room_name: LiveKit room name for this call
    """
    bridge = TwilioLiveKitBridge(
        websocket=websocket,
        room_name=room_name,
        test_run_id=test_run_id
    )
    
    await bridge.handle_twilio_stream()
