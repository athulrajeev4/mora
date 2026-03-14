"""
Call Orchestration Service
Orchestrates outbound test calls with LiveKit rooms and AI test callers
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project, TestCase, TestRun, TestSuite, TestRunStatus, ProjectStatus
from app.services.twilio_service import twilio_service
from app.services.livekit_service import livekit_service

logger = logging.getLogger(__name__)


class CallOrchestrationService:
    """
    Orchestrates the complete flow of a test call:
    1. Create LiveKit room with metadata
    2. Start AI test caller agent in room
    3. Make Twilio outbound call to user's bot
    4. Connect call to LiveKit room via SIP
    5. Monitor call progress
    6. Collect results when complete
    """
    
    def __init__(self):
        self.active_calls: Dict[str, Dict[str, Any]] = {}
    
    async def execute_test_run(
        self,
        db: Session,
        project: Project,
        test_case: TestCase,
        test_run: TestRun,
    ) -> Dict[str, Any]:
        """
        Execute a single test run
        
        Args:
            db: Database session
            project: Project being tested
            test_case: Test case to execute
            test_run: TestRun record to update
            
        Returns:
            Results dictionary with transcript and evaluation
        """
        logger.info(f"🎬 Starting test run for test case: {test_case.id}")
        logger.info(f"   Project: {project.name}")
        logger.info(f"   Bot Phone: {project.bot_phone_number}")
        logger.info(f"   Test Case: {test_case.utterance}")
        
        call_sid = None
        try:
            # Update test run status
            test_run.status = TestRunStatus.IN_PROGRESS
            test_run.started_at = datetime.utcnow()
            db.commit()
            
            # Get test suite for scenario
            test_suite = test_case.test_suite
            
            # 1. Create LiveKit room with test configuration
            room_name = f"test-{project.id}-{test_case.id}-{uuid.uuid4()}"
            logger.info(f"📦 Creating LiveKit room: {room_name}")
            
            room_metadata = {
                'scenario': test_suite.scenario,
                'test_cases': [{
                    'id': str(test_case.id),
                    'utterance': test_case.utterance,
                    'expected_behavior': test_case.expected_behavior,
                    'order': test_case.order,
                }],
                'test_run_id': str(test_run.id),
                'project_id': str(project.id),
                'bot_phone': project.bot_phone_number,
            }
            
            room_info = await livekit_service.create_test_room(
                room_name=room_name,
                metadata=room_metadata,
            )
            
            logger.info(f"✅ Room created: {room_name}")
            
            # 2. Start AI test caller agent in room (runs in background)
            logger.info("🤖 Starting AI test caller agent...")
            agent_task = asyncio.create_task(
                self._wait_for_agent_ready(room_name)
            )
            
            # Wait a moment for agent to join
            await asyncio.sleep(2)
            
            # 3. Make outbound call to user's bot
            logger.info(f"📞 Making outbound call to {project.bot_phone_number}...")
            
            call_sid = await twilio_service.make_outbound_test_call(
                to_phone=project.bot_phone_number,
                room_name=room_name,
                sip_uri=room_info['sip_uri'],
                test_run_id=str(test_run.id),
            )
            
            if not call_sid:
                raise Exception("Failed to initiate Twilio call")
            
            logger.info(f"✅ Call initiated: {call_sid}")
            
            # Update test run with call SID
            test_run.call_sid = call_sid
            db.commit()
            
            # 4. Track active call
            self.active_calls[call_sid] = {
                'room_name': room_name,
                'test_run_id': str(test_run.id),
                'started_at': datetime.utcnow(),
                'status': 'in_progress',
            }
            
            # 5. Wait for call to complete (with timeout)
            logger.info("⏳ Waiting for call to complete...")
            
            try:
                results = await asyncio.wait_for(
                    self._wait_for_call_completion(call_sid, room_name),
                    timeout=300  # 5 minutes max
                )
                
                logger.info("✅ Call completed successfully")
                
                # Update test run status
                test_run.status = TestRunStatus.SUCCESS
                test_run.completed_at = datetime.utcnow()
                
                # Store results (transcript, evaluations will be added later)
                # For now, we'll update via webhook when results are available
                
                db.commit()
                
                return results
                
            except asyncio.TimeoutError:
                logger.error("⏰ Call timeout - exceeded 5 minutes")
                test_run.status = TestRunStatus.FAILURE
                test_run.completed_at = datetime.utcnow()
                db.commit()
                
                raise Exception("Call timeout")
            
        except Exception as e:
            logger.error(f"❌ Error executing test run: {e}", exc_info=True)
            
            # Update test run as failed
            test_run.status = TestRunStatus.FAILURE
            test_run.completed_at = datetime.utcnow()
            db.commit()
            
            # Cleanup
            if call_sid:
                self.active_calls.pop(call_sid, None)
            
            raise
    
    async def _wait_for_agent_ready(self, room_name: str):
        """Wait for AI agent to join the room"""
        # The agent will join automatically when the room is created
        # This is handled by LiveKit's agent dispatch
        logger.info(f"⏳ Waiting for agent to join room: {room_name}")
        await asyncio.sleep(3)
        logger.info("✅ Agent should be ready in room")
    
    async def _wait_for_call_completion(
        self,
        call_sid: str,
        room_name: str
    ) -> Dict[str, Any]:
        """
        Wait for call to complete and return results
        
        In practice, this would:
        1. Poll Twilio for call status
        2. Poll LiveKit for room participants
        3. Wait for room to be empty
        4. Fetch results from agent
        """
        # For now, simulate waiting for call completion
        # In real implementation, we'd monitor the room and call status
        
        while True:
            await asyncio.sleep(5)
            
            # Check if call is still active
            call_info = self.active_calls.get(call_sid)
            if not call_info:
                break
            
            # Check Twilio call status
            call_status = twilio_service.get_call_status(call_sid)
            
            if call_status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                logger.info(f"📞 Call ended with status: {call_status}")
                self.active_calls.pop(call_sid, None)
                break
        
        # Return placeholder results
        # Real results will come from the agent via API callback
        return {
            'call_sid': call_sid,
            'room_name': room_name,
            'status': 'completed',
            'message': 'Call completed, results will be available shortly',
        }
    
    async def execute_project(
        self,
        db: Session,
        project: Project,
    ) -> Dict[str, Any]:
        """
        Execute all test runs for a project
        
        Args:
            db: Database session
            project: Project to execute
            
        Returns:
            Summary of results
        """
        logger.info(f"🚀 Executing project: {project.name}")
        logger.info(f"   Test Suites: {len(project.test_suites)}")
        logger.info(f"   Calls per suite: {project.number_of_calls}")
        
        total_runs = 0
        successful_runs = 0
        failed_runs = 0
        
        try:
            # Get all test runs for this project that are pending
            test_runs = db.query(TestRun).filter(
                TestRun.project_id == project.id,
                TestRun.status == TestRunStatus.PENDING
            ).all()
            
            logger.info(f"📋 Found {len(test_runs)} pending test runs")
            
            # Execute test runs sequentially (could be parallelized later)
            for test_run in test_runs:
                total_runs += 1
                
                try:
                    # Get test case
                    test_case = test_run.test_case
                    
                    logger.info(f"\n{'='*70}")
                    logger.info(f"Executing test run {total_runs}/{len(test_runs)}")
                    logger.info(f"Test Case: {test_case.utterance}")
                    logger.info(f"{'='*70}\n")
                    
                    # Execute the test run
                    await self.execute_test_run(
                        db=db,
                        project=project,
                        test_case=test_case,
                        test_run=test_run,
                    )
                    
                    successful_runs += 1
                    
                    # Brief pause between calls to avoid overwhelming systems
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ Test run failed: {e}")
                    failed_runs += 1
                    # Continue with next test run
            
            # Update project status based on run outcomes
            project.status = ProjectStatus.FAILED if failed_runs > 0 else ProjectStatus.COMPLETED
            db.commit()
            
            logger.info(f"\n🏁 Project execution completed!")
            logger.info(f"   Total: {total_runs}")
            logger.info(f"   Successful: {successful_runs}")
            logger.info(f"   Failed: {failed_runs}")
            
            return {
                'total': total_runs,
                'successful': successful_runs,
                'failed': failed_runs,
                'status': project.status,
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing project: {e}", exc_info=True)
            
            # Update project status
            project.status = ProjectStatus.FAILED
            db.commit()
            
            raise
    
    def get_call_status(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get status of an active call"""
        return self.active_calls.get(call_sid)


# Global instance
call_orchestration_service = CallOrchestrationService()
