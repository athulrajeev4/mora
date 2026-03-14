"""
Twilio Webhook Routes - Handle Twilio callbacks
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, WebSocket
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.call_execution_service import call_execution_service
from app.services.twilio_service import twilio_service
from app.core.config import settings

router = APIRouter()


# ============================================================================
# TwiML Voice Response - Provide call instructions
# ============================================================================

@router.post("/voice/{test_run_id}")
async def handle_voice_webhook(
    test_run_id: UUID,
    db: Session = Depends(get_db)
):
    """
    TwiML endpoint that provides voice instructions for the call
    
    This is called when the call is answered. It returns TwiML that tells
    Twilio what to do (play message, record, etc.)
    """
    from app.models import TestRun, TestCase
    
    # Get test run and test case
    test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    test_case = db.query(TestCase).filter(TestCase.id == test_run.test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    # Generate TwiML response
    # Speak the utterance and record the full conversation
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{test_case.utterance}</Say>
    <Pause length="5"/>
    <Hangup/>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


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
    Handle call status updates from Twilio
    
    Twilio sends POST requests here as the call progresses:
    - initiated: Call has been created
    - ringing: Phone is ringing
    - answered: Call was answered
    - completed: Call ended
    - failed/busy/no-answer: Call failed
    
    **Form Data from Twilio:**
    - CallSid: Unique identifier for the call
    - CallStatus: Current status (initiated, ringing, answered, completed, etc.)
    - CallDuration: Duration in seconds (only for completed calls)
    """
    print(f"Status webhook: {test_run_id} - {CallStatus}")
    
    # Parse duration
    duration = int(CallDuration) if CallDuration else None
    
    # Update test run status
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
    Handle recording completion webhook from Twilio
    
    Called when the call recording is ready. We store the recording URL
    and optionally trigger transcription.
    
    **Form Data from Twilio:**
    - RecordingSid: Unique identifier for the recording
    - RecordingUrl: URL to access the recording
    - RecordingDuration: Duration in seconds
    """
    print(f"Recording webhook: {test_run_id} - {RecordingSid}")
    
    # Convert recording URL to MP3 format
    recording_url = RecordingUrl.replace('.json', '.mp3')
    
    # Store recording URL
    call_execution_service.store_recording(
        db=db,
        test_run_id=test_run_id,
        recording_url=recording_url,
        recording_sid=RecordingSid
    )
    
    # TODO: In Stage 5, trigger transcription here
    # For now, we can try to get Twilio's built-in transcription
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
    """
    Manually store a transcript for a test run
    
    This is useful for testing or when using external transcription services.
    """
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
