"""
Evaluation Service - Orchestrates transcription and LLM-based evaluation
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import TestRun, TestCase, TestSuite, TestRunStatus
from app.services.llm_service import llm_service


class EvaluationService:
    """Service for evaluating test runs using LLM"""
    
    @staticmethod
    async def evaluate_test_run(db: Session, test_run_id: UUID) -> bool:
        """
        Complete evaluation workflow for a test run:
        1. Transcribe the call recording
        2. Perform functional evaluation
        3. Perform conversational evaluation
        4. Update database with results
        
        Args:
            db: Database session
            test_run_id: UUID of test run to evaluate
            
        Returns:
            True if evaluation succeeded, False otherwise
        """
        # Get test run with relationships
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        
        if not test_run:
            print(f"Test run {test_run_id} not found")
            return False
        
        # Validate test run is ready for evaluation
        if test_run.status != TestRunStatus.SUCCESS:
            print(f"Test run {test_run_id} status is {test_run.status}, not SUCCESS")
            return False
        
        if not test_run.audio_url:
            print(f"Test run {test_run_id} has no audio recording")
            return False
        
        # Get test case and test suite for context
        test_case = db.query(TestCase).filter(TestCase.id == test_run.test_case_id).first()
        if not test_case:
            print(f"Test case {test_run.test_case_id} not found")
            return False
        
        test_suite = db.query(TestSuite).filter(TestSuite.id == test_case.test_suite_id).first()
        if not test_suite:
            print(f"Test suite {test_case.test_suite_id} not found")
            return False
        
        try:
            # Step 1: Transcribe audio if not already done
            if not test_run.transcript:
                print(f"📝 Transcribing audio for test run {test_run_id}...")
                transcript = await llm_service.transcribe_audio(test_run.audio_url)
                
                if not transcript:
                    print(f"❌ Failed to transcribe audio for test run {test_run_id}")
                    return False
                
                test_run.transcript = transcript
                db.commit()
                print(f"✅ Transcription complete: {len(transcript)} characters")
            else:
                print(f"📝 Using existing transcript ({len(test_run.transcript)} characters)")
                transcript = test_run.transcript
            
            # Step 2: Functional Evaluation
            print(f"🎯 Performing functional evaluation...")
            functional_eval = await llm_service.evaluate_functional(
                transcript=transcript,
                expected_behavior=test_case.expected_behavior,
                test_scenario=test_suite.scenario
            )
            
            test_run.functional_evaluation = functional_eval
            db.commit()
            print(f"✅ Functional evaluation: {'PASSED' if functional_eval.get('passed') else 'FAILED'} (Score: {functional_eval.get('score', 0)})")
            
            # Step 3: Conversational Evaluation
            print(f"💬 Performing conversational evaluation...")
            conversational_eval = await llm_service.evaluate_conversational(
                transcript=transcript,
                test_scenario=test_suite.scenario
            )
            
            test_run.conversational_evaluation = conversational_eval
            db.commit()
            print(f"✅ Conversational score: {conversational_eval.get('overall_score', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error evaluating test run {test_run_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def evaluate_project_test_runs(db: Session, project_id: UUID) -> dict:
        """
        Evaluate all completed test runs for a project
        
        Args:
            db: Database session
            project_id: UUID of project
            
        Returns:
            Dictionary with evaluation statistics
        """
        # Get all successful test runs that need evaluation
        test_runs = db.query(TestRun).filter(
            TestRun.project_id == project_id,
            TestRun.status == TestRunStatus.SUCCESS,
            TestRun.audio_url.isnot(None)
        ).all()
        
        total = len(test_runs)
        evaluated = 0
        failed = 0
        
        print(f"🔍 Evaluating {total} test runs for project {project_id}")
        
        for test_run in test_runs:
            # Skip if already evaluated
            if test_run.functional_evaluation and test_run.conversational_evaluation:
                print(f"⏭️  Test run {test_run.id} already evaluated, skipping")
                evaluated += 1
                continue
            
            success = await EvaluationService.evaluate_test_run(db, test_run.id)
            
            if success:
                evaluated += 1
            else:
                failed += 1
        
        return {
            "total": total,
            "evaluated": evaluated,
            "failed": failed,
            "success_rate": (evaluated / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    def _parse_eval(val) -> dict:
        """Safely parse evaluation data that may be a dict or JSON string."""
        if val is None:
            return {}
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            import json
            try:
                parsed = json.loads(val)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @staticmethod
    def get_evaluation_summary(db: Session, project_id: UUID) -> dict:
        """
        Get summary of evaluations for a project
        
        Args:
            db: Database session
            project_id: UUID of project
            
        Returns:
            Dictionary with evaluation summary
        """
        test_runs = db.query(TestRun).filter(
            TestRun.project_id == project_id
        ).all()
        
        total = len(test_runs)
        
        evaluated = 0
        passed = 0
        functional_scores = []
        conversational_scores = []
        
        for tr in test_runs:
            func_eval = EvaluationService._parse_eval(tr.functional_evaluation)
            conv_eval = EvaluationService._parse_eval(tr.conversational_evaluation)
            
            if func_eval and conv_eval:
                evaluated += 1
                if func_eval.get('passed', False):
                    passed += 1
                functional_scores.append(func_eval.get('score', 0))
                conversational_scores.append(conv_eval.get('overall_score', 0))
        
        avg_functional_score = sum(functional_scores) / len(functional_scores) if functional_scores else 0
        avg_conversational_score = sum(conversational_scores) / len(conversational_scores) if conversational_scores else 0
        
        return {
            "total_test_runs": total,
            "evaluated": evaluated,
            "pending_evaluation": total - evaluated,
            "functional_passed": passed,
            "functional_failed": evaluated - passed,
            "avg_functional_score": round(avg_functional_score, 2),
            "avg_conversational_score": round(avg_conversational_score, 2),
            "completion_percentage": round((evaluated / total * 100) if total > 0 else 0, 2)
        }


# Singleton instance
evaluation_service = EvaluationService()
