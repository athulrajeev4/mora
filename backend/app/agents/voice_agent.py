"""
LiveKit Voice Agent for Mora Platform
Implements STT -> LLM -> TTS conversational agent for inbound calls
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, elevenlabs

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def prewarm(proc: JobProcess):
    """Preload resources when agent worker starts (before calls arrive)"""
    proc.userdata["ready"] = True
    logger.info("Agent worker prewarmed and ready for calls")


async def entrypoint(ctx: JobContext):
    """
    LiveKit worker entrypoint.
    Called when a new participant joins a room (including SIP phone calls).

    Supports two modes:
    1. Inbound calls: Regular voice assistant
    2. Test calling: Follows test script and executes test cases
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    room_metadata = {}
    if ctx.room.metadata:
        try:
            room_metadata = json.loads(ctx.room.metadata)
            logger.info(f"Room metadata: {room_metadata}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse room metadata")

    is_test_call = room_metadata.get("mode") == "test_call"

    participant = await ctx.wait_for_participant()

    is_sip_call = participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP

    if is_sip_call:
        logger.info(f"SIP call in room: {ctx.room.name}")

    if is_test_call:
        logger.info("Test calling mode enabled")

    stt = deepgram.STT(
        model="nova-2-general",
        language="en",
    )

    llm_model = openai.LLM(
        model="gpt-4o",
    )

    tts = elevenlabs.TTS(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model="eleven_turbo_v2_5",
    )

    if is_test_call:
        scenario = room_metadata.get("scenario", "Unknown Test")
        test_cases = room_metadata.get("test_cases", [])

        script_lines = "\n".join(
            [f"{i+1}. {tc.get('utterance', '')}"
             for i, tc in enumerate(test_cases)]
        )

        instructions = f"""You are conducting a test call for: {scenario}

Your role: Execute the following test script by speaking each line clearly and waiting for responses.

Test Script:
{script_lines}

Instructions:
- Speak each test case phrase clearly
- Wait 3-5 seconds after each phrase for a response
- Keep your tone natural and conversational
- Do not deviate from the script
- After completing all test cases, say "Thank you, test complete" and end the call

Begin with test case #1."""

        logger.info(f"Test script loaded: {len(test_cases)} test cases")
    else:
        instructions = """You are a helpful voice assistant.
You are receiving a phone call. Be friendly, helpful, and conversational.
Keep your responses concise (1-2 sentences).
Greet the caller and ask how you can help them today."""

    agent = Agent(
        instructions=instructions,
        stt=stt,
        llm=llm_model,
        tts=tts,
    )

    logger.info("Voice agent created with STT, LLM, TTS")

    session = AgentSession()

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    if is_test_call:
        test_cases = room_metadata.get("test_cases", [])
        if test_cases:
            first_utterance = test_cases[0].get("utterance", "Hello, starting test")
            await session.say(first_utterance, allow_interruptions=True)
            logger.info(f"Spoke first test case: {first_utterance[:50]}...")
    elif is_sip_call:
        await session.say(
            "Hello! Thank you for calling. How can I help you today?",
            allow_interruptions=True,
        )

    logger.info(f"Voice agent started for room: {ctx.room.name}, participant: {participant.identity}")
    logger.info("Agent listening and ready to respond...")

    try:
        await participant.wait_for_disconnection()
        logger.info(f"Participant disconnected from room: {ctx.room.name}")
    except Exception as e:
        logger.error(f"Error waiting for disconnection: {e}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
