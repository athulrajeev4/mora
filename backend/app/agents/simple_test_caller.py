"""
SIMPLE Test Caller Agent - Just speaks test cases
No complex conversation handling, just sequential utterances
"""

import asyncio
import logging
import json
from typing import Optional
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import elevenlabs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def simple_test_caller(ctx: JobContext):
    """
    Super simple test caller - just speaks test cases with pauses
    """
    room_name = ctx.room.name
    logger.info(f"🚀 Simple Test Caller starting for room: {room_name}")
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"✅ Connected to room")
    
    # Get test config from metadata
    try:
        metadata = json.loads(ctx.room.metadata or '{}')
        test_cases = metadata.get('test_cases', [])
        logger.info(f"📋 Loaded {len(test_cases)} test cases")
    except Exception as e:
        logger.error(f"❌ Failed to parse metadata: {e}")
        return
    
    # Wait for bot to join
    logger.info("⏳ Waiting for bot to join...")
    participant = await ctx.wait_for_participant()
    logger.info(f"📞 Bot joined: {participant.identity}")
    
    # Create TTS
    tts = elevenlabs.TTS(
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        model="eleven_turbo_v2_5",
    )
    
    # Create audio source for speaking
    source = rtc.AudioSource(24000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("test_caller_audio", source)
    options = rtc.TrackPublishOptions()
    options.source = rtc.TrackSource.SOURCE_MICROPHONE
    
    # Publish track
    publication = await ctx.room.local_participant.publish_track(track, options)
    logger.info("✅ Published audio track")
    
    # Give bot 2 seconds to settle
    await asyncio.sleep(2)
    
    # Speak each test case
    for i, test_case in enumerate(test_cases, 1):
        utterance = test_case['utterance']
        
        logger.info(f"🗣️ Test Case {i}/{len(test_cases)}: {utterance}")
        
        # Generate speech
        async for audio in tts.synthesize(utterance):
            await source.capture_frame(audio.frame)
        
        logger.info(f"✅ Spoke test case {i}")
        
        # Wait 5 seconds for bot to respond
        logger.info("⏳ Waiting 5 seconds for bot response...")
        await asyncio.sleep(5)
    
    logger.info("🏁 All test cases completed")
    
    # Wait 5 more seconds before ending
    await asyncio.sleep(5)
    
    logger.info("✅ Test call complete")


def prewarm(proc: JobProcess):
    """Preload resources"""
    proc.userdata["ready"] = True
    logger.info("🔥 Simple Test Caller ready")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=simple_test_caller,
            prewarm_fnc=prewarm,
            agent_name="mora-test-caller",
        )
    )
