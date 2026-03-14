"""
Twilio Media Stream to LiveKit Bridge
Handles bidirectional audio: Twilio caller <-> LiveKit AI agent
"""

import asyncio
import audioop
import base64
import json
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from livekit import api, rtc
from app.core.config import settings

logger = logging.getLogger(__name__)

TWILIO_SAMPLE_RATE = 8000
NUM_CHANNELS = 1
BYTES_PER_SAMPLE = 2


class TwilioLiveKitBridge:
    """
    Bridges Twilio Media Stream (WebSocket) to a LiveKit Room.

    Inbound (Twilio -> LiveKit):
        mulaw 8kHz -> PCM16 8kHz -> publish as audio track

    Outbound (LiveKit -> Twilio):
        Subscribe to agent audio track -> PCM16 -> mulaw -> base64 -> Twilio WS
    """

    def __init__(self, websocket: WebSocket, room_name: str, test_run_id: str):
        self.websocket = websocket
        self.room_name = room_name
        self.test_run_id = test_run_id

        self.lk_room: Optional[rtc.Room] = None
        self.lk_source: Optional[rtc.AudioSource] = None
        self.stream_sid: Optional[str] = None
        self._running = True

    async def connect_to_livekit(self) -> bool:
        try:
            token = api.AccessToken(
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
            )
            token.with_identity(f"twilio-bridge-{self.test_run_id}")
            token.with_name("Twilio Caller")
            token.with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )

            self.lk_room = rtc.Room()

            # Wire up track subscription handler before connecting
            self.lk_room.on("track_subscribed", self._on_track_subscribed)

            await self.lk_room.connect(
                url=settings.LIVEKIT_URL,
                token=token.to_jwt(),
            )

            # Create audio source to publish Twilio caller audio into the room
            self.lk_source = rtc.AudioSource(
                sample_rate=TWILIO_SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
            )
            track = rtc.LocalAudioTrack.create_audio_track(
                "caller-audio", self.lk_source
            )
            options = rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_MICROPHONE
            )
            await self.lk_room.local_participant.publish_track(track, options)

            logger.info(f"✅ Bridge connected to LiveKit room: {self.room_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect bridge to LiveKit: {e}", exc_info=True)
            return False

    def _on_track_subscribed(
        self,
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Called when a remote track (e.g. the agent's TTS audio) is subscribed."""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(
                f"🔊 Subscribed to audio from {participant.identity} – "
                f"forwarding to Twilio"
            )
            audio_stream = rtc.AudioStream(
                track,
                sample_rate=TWILIO_SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
            )
            asyncio.ensure_future(self._forward_livekit_to_twilio(audio_stream))

    async def _forward_livekit_to_twilio(self, audio_stream: rtc.AudioStream):
        """Read PCM frames from LiveKit agent, convert to mulaw, send to Twilio."""
        try:
            async for frame_event in audio_stream:
                if not self._running or not self.stream_sid:
                    continue

                frame: rtc.AudioFrame = frame_event.frame
                pcm_data = bytes(frame.data)

                # AudioStream already resamples to 8kHz mono; just convert to mulaw
                mulaw_data = audioop.lin2ulaw(pcm_data, BYTES_PER_SAMPLE)

                payload = base64.b64encode(mulaw_data).decode("ascii")

                msg = json.dumps(
                    {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {"payload": payload},
                    }
                )

                try:
                    await self.websocket.send_text(msg)
                except Exception:
                    break

        except Exception as e:
            logger.error(f"❌ Error forwarding LiveKit->Twilio: {e}", exc_info=True)

    async def handle_twilio_stream(self):
        """Main handler – reads Twilio WS messages and forwards audio to LiveKit."""
        try:
            await self.websocket.accept()
            logger.info(f"📞 Twilio WebSocket accepted for test run: {self.test_run_id}")

            if not await self.connect_to_livekit():
                await self.websocket.close()
                return

            while self._running:
                try:
                    data = await self.websocket.receive_text()
                    message = json.loads(data)
                    event = message.get("event")

                    if event == "start":
                        self.stream_sid = message["start"]["streamSid"]
                        logger.info(f"🎬 Twilio stream started: {self.stream_sid}")

                    elif event == "media":
                        payload = message["media"]["payload"]
                        audio_data = base64.b64decode(payload)
                        await self._forward_audio_to_livekit(audio_data)

                    elif event == "stop":
                        logger.info(f"🛑 Twilio stream stopped: {self.stream_sid}")
                        break

                except WebSocketDisconnect:
                    logger.info("📵 Twilio WebSocket disconnected")
                    break

        except Exception as e:
            logger.error(f"❌ Error in Twilio stream handler: {e}", exc_info=True)

        finally:
            self._running = False
            await self._cleanup()

    async def _forward_audio_to_livekit(self, mulaw_data: bytes):
        """Convert mulaw -> PCM16 and publish into the LiveKit room."""
        try:
            pcm_data = audioop.ulaw2lin(mulaw_data, BYTES_PER_SAMPLE)
            frame = rtc.AudioFrame(
                data=pcm_data,
                sample_rate=TWILIO_SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
                samples_per_channel=len(pcm_data) // (NUM_CHANNELS * BYTES_PER_SAMPLE),
            )
            await self.lk_source.capture_frame(frame)
        except Exception as e:
            logger.error(f"❌ Error forwarding Twilio->LiveKit: {e}")

    async def _cleanup(self):
        try:
            if self.lk_room:
                await self.lk_room.disconnect()
            logger.info(f"🧹 Bridge cleaned up for room: {self.room_name}")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def handle_twilio_websocket(
    websocket: WebSocket,
    test_run_id: str,
    room_name: str,
):
    """Entry point called from the webhooks router."""
    bridge = TwilioLiveKitBridge(
        websocket=websocket,
        room_name=room_name,
        test_run_id=test_run_id,
    )
    await bridge.handle_twilio_stream()
