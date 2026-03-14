"""
Twilio Webhook Routes - Handle Twilio callbacks and media stream bridge
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, WebSocket
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.call_execution_service import call_execution_service
from app.services.call_orchestration_service import call_orchestration_service
from app.services.twilio_service import twilio_service
from app.services.livekit_bridge import handle_twilio_websocket
from app.core.config import settings

router = APIRouter()


# ============================================================================
# TwiML Voice Response - Set up media stream to LiveKit bridge
# ============================================================================

@router.post("/voice/{test_run_id}")
async def handle_voice_webhook(
    test_run_id: UUID,
    db: Session = Depends(get_db)
):
    """
    TwiML endpoint called when the outbound call is answered.
    
    Returns TwiML that opens a bidirectional media stream (WebSocket)
    to our backend, which bridges the audio to a LiveKit room
    where the AI test caller agent is waiting.
    """
    from app.models import TestRun, TestCase

    test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    room_name = call_orchestration_service.get_room_for_test_run(str(test_run_id))

    if room_name and settings.PUBLIC_URL:
        ws_url = settings.PUBLIC_URL.replace("https://", "wss://").replace("http://", "ws://")
        stream_url = f"{ws_url}/api/webhooks/twilio/stream/{test_run_id}"

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="test_run_id" value="{test_run_id}"/>
            <Parameter name="room_name" value="{room_name}"/>
        </Stream>
    </Connect>
</Response>"""
    else:
        test_case = db.query(TestCase).filter(TestCase.id == test_run.test_case_id).first()
        utterance = test_case.utterance if test_case else "Hello, this is a test call."

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{utterance}</Say>
    <Pause length="10"/>
    <Say voice="Polly.Joanna">Thank you, goodbye.</Say>
    <Hangup/>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


# ============================================================================
# WebSocket Media Stream - Twilio <-> LiveKit Bridge
# ============================================================================

@router.websocket("/stream/{test_run_id}")
async def handle_media_stream(
    websocket: WebSocket,
    test_run_id: str,
):
    """
    WebSocket endpoint for Twilio bidirectional media stream.
    
    Twilio sends audio frames here after <Connect><Stream> TwiML.
    We bridge the audio to the LiveKit room where the AI agent lives.
    """
    room_name = call_orchestration_service.get_room_for_test_run(test_run_id)

    if not room_name:
        print(f"⚠️ No room found for test run {test_run_id}, rejecting WebSocket")
        await websocket.close(code=1008)
        return

    print(f"🌉 Starting media stream bridge: test_run={test_run_id}, room={room_name}")

    await handle_twilio_websocket(
        websocket=websocket,
        test_run_id=test_run_id,
        room_name=room_name,
    )


# ============================================================================
# Call Status Webhook - Track call lifecycle
# ============================================================================

@router.post("/status/{test_run_id}")
async def handle_status_webhook(
    test_run_id: UUID,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle call status updates from Twilio.
    """
    print(f"📞 Status webhook: {test_run_id} - {CallStatus}")

    duration = int(CallDuration) if CallDuration else None

    call_execution_service.update_call_status(
        db=db,
        test_run_id=test_run_id,
        call_status=CallStatus,
        call_duration=duration
    )

    return {"status": "received"}


# ============================================================================
# Recording Webhook - Handle call recordings
# ============================================================================

@router.post("/recording/{test_run_id}")
async def handle_recording_webhook(
    test_run_id: UUID,
    RecordingSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingDuration: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle recording completion webhook from Twilio.
    """
    print(f"🎙️ Recording webhook: {test_run_id} - {RecordingSid}")

    recording_url = RecordingUrl.replace('.json', '.mp3')

    call_execution_service.store_recording(
        db=db,
        test_run_id=test_run_id,
        recording_url=recording_url,
        recording_sid=RecordingSid
    )

    try:
        transcript = twilio_service.get_transcription(RecordingSid)
        if transcript:
            call_execution_service.store_transcript(
                db=db,
                test_run_id=test_run_id,
                transcript=transcript
            )
    except Exception as e:
        print(f"Error fetching transcription: {e}")

    return {"status": "received"}


# ============================================================================
# Manual Transcription Endpoint (for testing)
# ============================================================================

@router.post("/transcript/{test_run_id}")
async def store_transcript(
    test_run_id: UUID,
    transcript: str = Form(...),
    db: Session = Depends(get_db)
):
    """Manually store a transcript for a test run."""
    success = call_execution_service.store_transcript(
        db=db,
        test_run_id=test_run_id,
        transcript=transcript
    )

    if success:
        return {"status": "stored", "test_run_id": str(test_run_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run {test_run_id} not found"
        )
