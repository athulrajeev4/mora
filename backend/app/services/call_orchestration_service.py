"""
Call Orchestration Service
Orchestrates outbound test calls with LiveKit rooms and AI test callers.

Key design: ONE phone call per project activation covering ALL test cases.
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project, TestCase, TestRun, TestSuite, TestRunStatus, ProjectStatus
from app.services.twilio_service import twilio_service
from app.services.livekit_service import livekit_service

logger = logging.getLogger(__name__)


class CallOrchestrationService:
    """
    Orchestrates the complete flow of a project test:
    1. Collect ALL test cases across attached suites
    2. Create ONE LiveKit room with full test plan in metadata
    3. Dispatch AI agent into the room
    4. Make ONE Twilio outbound call to the user's bot
    5. Bridge call audio into the room (handled by webhooks/bridge)
    6. Agent executes all test cases sequentially in a single conversation
    7. When call ends, mark all test runs complete
    """

    def __init__(self):
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.test_run_rooms: Dict[str, str] = {}  # test_run_id -> room_name

    async def execute_project(
        self,
        db: Session,
        project: Project,
    ) -> Dict[str, Any]:
        """
        Execute all test cases for a project in a SINGLE phone call.
        """
        logger.info(f"🚀 Executing project: {project.name}")
        logger.info(f"   Test Suites: {len(project.test_suites)}")
        logger.info(f"   Bot Phone: {project.bot_phone_number}")

        try:
            # Gather all pending test runs and their test cases
            test_runs: List[TestRun] = (
                db.query(TestRun)
                .filter(
                    TestRun.project_id == project.id,
                    TestRun.status == TestRunStatus.PENDING,
                )
                .all()
            )

            if not test_runs:
                logger.warning("⚠️ No pending test runs found")
                project.status = ProjectStatus.COMPLETED
                db.commit()
                return {"total": 0, "status": "no_pending_runs"}

            logger.info(f"📋 Found {len(test_runs)} pending test runs")

            # Build the combined test plan from all test cases
            test_plan = []
            test_run_map: Dict[str, TestRun] = {}  # test_case_id -> test_run

            for tr in test_runs:
                tc: TestCase = tr.test_case
                test_plan.append(
                    {
                        "id": str(tc.id),
                        "test_run_id": str(tr.id),
                        "utterance": tc.utterance,
                        "expected_behavior": tc.expected_behavior,
                        "order": tc.order,
                    }
                )
                test_run_map[str(tc.id)] = tr

            # Sort by order so the agent follows the intended sequence
            test_plan.sort(key=lambda x: x.get("order", 0))

            # Get scenario from first test suite
            scenario = (
                project.test_suites[0].scenario
                if project.test_suites
                else "Voice bot test"
            )

            # ── 1. Create ONE LiveKit room ─────────────────────────────
            room_name = f"test-{project.id}-{uuid.uuid4()}"
            logger.info(f"📦 Creating LiveKit room: {room_name}")

            room_metadata = {
                "mode": "test_call",
                "scenario": scenario,
                "test_cases": test_plan,
                "project_id": str(project.id),
                "bot_phone": project.bot_phone_number,
            }

            await livekit_service.create_test_room(
                room_name=room_name,
                metadata=room_metadata,
            )
            logger.info(f"✅ Room created: {room_name}")

            # Register room for EVERY test run so any webhook lookup succeeds
            master_run_id = str(test_runs[0].id)
            for tr in test_runs:
                self.test_run_rooms[str(tr.id)] = room_name

            # Mark all runs as IN_PROGRESS
            for tr in test_runs:
                tr.status = TestRunStatus.IN_PROGRESS
                tr.started_at = datetime.utcnow()
            db.commit()

            # ── 2. Wait for agent to be ready ──────────────────────────
            logger.info("🤖 Waiting for agent to join room...")
            await asyncio.sleep(3)

            # ── 3. Make ONE outbound call ──────────────────────────────
            logger.info(f"📞 Making outbound call to {project.bot_phone_number}...")

            call_sid = await twilio_service.make_outbound_test_call(
                to_phone=project.bot_phone_number,
                room_name=room_name,
                test_run_id=master_run_id,
            )

            if not call_sid:
                raise Exception("Failed to initiate Twilio call")

            logger.info(f"✅ Call initiated: {call_sid}")

            # Store call_sid on ALL test runs
            for tr in test_runs:
                tr.call_sid = call_sid
            db.commit()

            self.active_calls[call_sid] = {
                "room_name": room_name,
                "project_id": str(project.id),
                "test_run_ids": [str(tr.id) for tr in test_runs],
                "started_at": datetime.utcnow(),
                "status": "in_progress",
            }

            # ── 4. Wait for the single call to finish ──────────────────
            logger.info("⏳ Waiting for call to complete...")

            try:
                await asyncio.wait_for(
                    self._wait_for_call_completion(call_sid, room_name),
                    timeout=300,
                )
                logger.info("✅ Call completed")

                for tr in test_runs:
                    tr.status = TestRunStatus.SUCCESS
                    tr.completed_at = datetime.utcnow()
                db.commit()

            except asyncio.TimeoutError:
                logger.error("⏰ Call timeout – exceeded 5 minutes")
                for tr in test_runs:
                    tr.status = TestRunStatus.FAILURE
                    tr.completed_at = datetime.utcnow()
                db.commit()

            # ── 5. Finalize project ────────────────────────────────────
            failed = any(tr.status == TestRunStatus.FAILURE for tr in test_runs)
            project.status = ProjectStatus.FAILED if failed else ProjectStatus.COMPLETED
            db.commit()

            logger.info(f"🏁 Project execution finished – status: {project.status}")
            return {
                "total": len(test_runs),
                "call_sid": call_sid,
                "status": str(project.status),
            }

        except Exception as e:
            logger.error(f"❌ Error executing project: {e}", exc_info=True)
            project.status = ProjectStatus.FAILED
            db.commit()
            raise

    # ────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ────────────────────────────────────────────────────────────────────

    async def _wait_for_call_completion(
        self, call_sid: str, room_name: str
    ) -> Dict[str, Any]:
        terminal_statuses = {"completed", "failed", "busy", "no-answer", "canceled"}
        max_call_seconds = 120

        while True:
            await asyncio.sleep(5)

            if call_sid not in self.active_calls:
                break

            try:
                call_data = twilio_service.get_call_status(call_sid)
                if call_data and call_data.get("status") in terminal_statuses:
                    logger.info(f"📞 Call ended: {call_data['status']}")
                    self.active_calls.pop(call_sid, None)
                    break

                # Safety cutoff: prevent stale calls from lingering forever.
                call_info = self.active_calls.get(call_sid)
                if call_info:
                    started_at = call_info.get("started_at")
                    if started_at and (datetime.utcnow() - started_at).total_seconds() > max_call_seconds:
                        logger.warning(f"⏱️ Max call duration reached ({max_call_seconds}s), hanging up")
                        twilio_service.hangup_call(call_sid)
            except Exception as e:
                logger.warning(f"⚠️ Error polling call status: {e}")

        # Clean up room mappings
        for trid, rname in list(self.test_run_rooms.items()):
            if rname == room_name:
                self.test_run_rooms.pop(trid, None)

        return {"call_sid": call_sid, "room_name": room_name, "status": "completed"}

    def get_room_for_test_run(self, test_run_id: str) -> Optional[str]:
        """Get the LiveKit room name associated with a test run."""
        return self.test_run_rooms.get(test_run_id)


# Global singleton
call_orchestration_service = CallOrchestrationService()
