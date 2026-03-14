"""
Call Execution Service - Manages test run execution via orchestration
"""
import asyncio
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import TestRun, TestCase, Project, TestRunStatus, TestSuite
from app.services.call_orchestration_service import call_orchestration_service
from app.services.twilio_service import twilio_service
from app.core.config import settings


class CallExecutionService:
    """Service for executing test runs and managing call lifecycle"""
    
    @staticmethod
    async def execute_test_run_with_orchestration(
        db: Session,
        test_run_id: UUID
    ) -> bool:
        """
        Execute a single test run using the new call orchestration service
        
        Args:
            db: Database session
            test_run_id: UUID of the test run to execute
            
        Returns:
            True if call executed successfully, False otherwise
        """
        # Get test run with related data
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            print(f"Test run {test_run_id} not found")
            return False
        
        # Get project and test case
        project = db.query(Project).filter(Project.id == test_run.project_id).first()
        test_case = db.query(TestCase).filter(TestCase.id == test_run.test_case_id).first()
        
        if not project or not test_case:
            print(f"Project or test case not found for test run {test_run_id}")
            return False
        
        try:
            # Execute test run with full orchestration
            await call_orchestration_service.execute_test_run(
                db=db,
                project=project,
                test_case=test_case,
                test_run=test_run,
            )
            
            print(f"✓ Test run {test_run_id} completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to execute test run {test_run_id}: {e}")
            return False
    
    @staticmethod
    def execute_test_run(db: Session, test_run_id: UUID, base_url: str) -> bool:
        """
        Execute a single test run by making a Twilio call
        
        Args:
            db: Database session
            test_run_id: UUID of the test run to execute
            base_url: Base URL of the API (for webhook callbacks)
            
        Returns:
            True if call initiated successfully, False otherwise
        """
        # Get test run with related data
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            print(f"Test run {test_run_id} not found")
            return False
        
        # Get project and test case
        project = db.query(Project).filter(Project.id == test_run.project_id).first()
        test_case = db.query(TestCase).filter(TestCase.id == test_run.test_case_id).first()
        
        if not project or not test_case:
            print(f"Project or test case not found for test run {test_run_id}")
            return False
        
        # Check if we should use demo TwiML or custom webhooks
        if settings.USE_DEMO_TWIML or not base_url.startswith('https://'):
            # Use Twilio's demo TwiML (no webhooks needed)
            print(f"⚠️  Using demo TwiML (no custom webhooks) - base_url: {base_url}")
            twiml_url = 'http://demo.twilio.com/docs/voice.xml'
            status_callback_url = None
            recording_callback_url = None
        else:
            # Construct webhook URLs (requires public HTTPS URL)
            twiml_url = f"{base_url}/api/webhooks/twilio/voice/{test_run_id}"
            status_callback_url = f"{base_url}/api/webhooks/twilio/status/{test_run_id}"
            recording_callback_url = f"{base_url}/api/webhooks/twilio/recording/{test_run_id}"
        
        # Make the call
        call_sid = twilio_service.make_call(
            to_phone=project.bot_phone_number,
            twiml_url=twiml_url,
            status_callback_url=status_callback_url,
            recording_status_callback_url=recording_callback_url
        )
        
        if call_sid:
            # Update test run with call SID and status
            test_run.call_sid = call_sid
            test_run.status = TestRunStatus.IN_PROGRESS
            test_run.started_at = datetime.utcnow()
            db.commit()
            
            print(f"✓ Call initiated for test run {test_run_id}: {call_sid}")
            return True
        else:
            # Mark as failed if call couldn't be initiated
            test_run.status = TestRunStatus.FAILURE
            db.commit()
            
            print(f"✗ Failed to initiate call for test run {test_run_id}")
            return False
    
    @staticmethod
    def execute_project_test_runs(db: Session, project_id: UUID, base_url: str) -> dict:
        """
        Execute all pending test runs for a project
        
        Args:
            db: Database session
            project_id: UUID of the project
            base_url: Base URL of the API
            
        Returns:
            Dictionary with execution statistics
        """
        # Get all pending test runs for the project
        pending_runs = db.query(TestRun).filter(
            TestRun.project_id == project_id,
            TestRun.status == TestRunStatus.PENDING
        ).all()
        
        total = len(pending_runs)
        successful = 0
        failed = 0
        
        print(f"Starting execution of {total} test runs for project {project_id}")
        
        for test_run in pending_runs:
            if CallExecutionService.execute_test_run(db, test_run.id, base_url):
                successful += 1
            else:
                failed += 1
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "message": f"Initiated {successful}/{total} calls"
        }
    
    @staticmethod
    def update_call_status(
        db: Session,
        test_run_id: UUID,
        call_status: str,
        call_duration: Optional[int] = None
    ) -> bool:
        """
        Update test run status based on Twilio call status webhook
        
        Args:
            db: Database session
            test_run_id: UUID of the test run
            call_status: Twilio call status (initiated, ringing, answered, completed, etc.)
            call_duration: Call duration in seconds (for completed calls)
            
        Returns:
            True if updated successfully
        """
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            return False
        
        # Map Twilio status to our TestRunStatus
        status_mapping = {
            'initiated': TestRunStatus.IN_PROGRESS,
            'ringing': TestRunStatus.IN_PROGRESS,
            'in-progress': TestRunStatus.IN_PROGRESS,
            'answered': TestRunStatus.IN_PROGRESS,
            'completed': TestRunStatus.SUCCESS,  # Will be updated to FAILURE if evaluation fails
            'failed': TestRunStatus.FAILURE,
            'busy': TestRunStatus.FAILURE,
            'no-answer': TestRunStatus.FAILURE,
            'canceled': TestRunStatus.FAILURE
        }
        
        new_status = status_mapping.get(call_status, TestRunStatus.IN_PROGRESS)
        test_run.status = new_status
        
        # Update completion time for completed calls
        if call_status == 'completed':
            test_run.completed_at = datetime.utcnow()
        
        db.commit()
        print(f"Updated test run {test_run_id} status: {call_status} -> {new_status}")
        return True
    
    @staticmethod
    def store_recording(
        db: Session,
        test_run_id: UUID,
        recording_url: str,
        recording_sid: str
    ) -> bool:
        """
        Store call recording URL in test run
        
        Args:
            db: Database session
            test_run_id: UUID of the test run
            recording_url: URL of the recording
            recording_sid: Twilio Recording SID
            
        Returns:
            True if stored successfully
        """
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            return False
        
        test_run.audio_url = recording_url
        db.commit()
        
        print(f"Stored recording for test run {test_run_id}: {recording_url}")
        return True
    
    @staticmethod
    def store_transcript(
        db: Session,
        test_run_id: UUID,
        transcript: str
    ) -> bool:
        """
        Store call transcript in test run
        
        Args:
            db: Database session
            test_run_id: UUID of the test run
            transcript: Transcription text
            
        Returns:
            True if stored successfully
        """
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            return False
        
        test_run.transcript = transcript
        db.commit()
        
        print(f"Stored transcript for test run {test_run_id}: {len(transcript)} characters")
        return True


# Singleton instance
call_execution_service = CallExecutionService()
