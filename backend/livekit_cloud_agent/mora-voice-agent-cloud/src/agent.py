import json
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="mora-voice-agent")
async def mora_voice_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    room_metadata = {}
    if ctx.room.metadata:
        try:
            room_metadata = json.loads(ctx.room.metadata)
        except json.JSONDecodeError:
            logger.warning("Failed to parse room metadata")

    is_test_call = room_metadata.get("mode") == "test_call"
    test_cases = room_metadata.get("test_cases", [])

    if is_test_call:
        scenario = room_metadata.get("scenario", "Unknown Test")
        script_lines = "\n".join(
            f"{index + 1}. {tc.get('utterance', '')}"
            for index, tc in enumerate(test_cases)
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
    else:
        instructions = (
            "You are a helpful voice assistant for a phone call. "
            "Be concise, friendly, and conversational."
        )

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Agent(instructions=instructions),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    if is_test_call and test_cases:
        await session.say(test_cases[0].get("utterance", "Hello, starting test"), allow_interruptions=True)
    elif participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        await session.say(
            "Hello. This is Mora test assistant. How can I help you today?",
            allow_interruptions=True,
        )


if __name__ == "__main__":
    cli.run_app(server)
