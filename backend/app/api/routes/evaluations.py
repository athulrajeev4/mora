"""
Evaluation API Routes - Trigger LLM evaluation of test runs
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models import TestRun, Project, TestRunStatus
from app.services.evaluation_service import evaluation_service


router = APIRouter()


# ============================================================================
# Single Test Run Evaluation
# ============================================================================

@router.post("/test-runs/{test_run_id}/evaluate", status_code=status.HTTP_202_ACCEPTED)
async def evaluate_test_run(
    test_run_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluate a single test run
    
    **Process:**
    1. Transcribe call recording (if not already done)
    2. Perform functional evaluation (compare to expected behavior)
    3. Perform conversational evaluation (quality assessment)
    4. Update test_run with results
    
    **Requirements:**
    - Test run must have status SUCCESS
    - Audio recording must be available
    
    **Returns:**
    - Acknowledgment that evaluation started
    - Evaluation runs in background
    """
    # Validate test run exists
    test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run with id {test_run_id} not found"
        )
    
    # Validate test run is ready for evaluation
    if test_run.status != TestRunStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test run status is {test_run.status}, must be SUCCESS to evaluate"
        )
    
    if not test_run.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test run has no audio recording"
        )
    
    # Start evaluation in background
    background_tasks.add_task(
        evaluation_service.evaluate_test_run,
        db,
        test_run_id
    )
    
    return {
        "message": "Evaluation started",
        "test_run_id": str(test_run_id),
        "status": "processing"
    }


@router.get("/test-runs/{test_run_id}/evaluation")
def get_test_run_evaluation(
    test_run_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get evaluation results for a test run
    
    **Returns:**
    - Transcript
    - Functional evaluation (passed/failed, score, reasoning)
    - Conversational evaluation (scores, feedback)
    """
    test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
    
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test run with id {test_run_id} not found"
        )
    
    status_val = test_run.status.value if hasattr(test_run.status, 'value') else str(test_run.status)
    
    return {
        "test_run_id": str(test_run.id),
        "status": status_val,
        "transcript": test_run.transcript,
        "functional_evaluation": test_run.functional_evaluation,
        "conversational_evaluation": test_run.conversational_evaluation,
        "audio_url": test_run.audio_url,
        "evaluated_at": test_run.completed_at
    }


# ============================================================================
# Project-wide Evaluation
# ============================================================================

@router.post("/projects/{project_id}/evaluate", status_code=status.HTTP_202_ACCEPTED)
async def evaluate_project(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluate all test runs for a project
    
    **Process:**
    - Finds all completed test runs with recordings
    - Evaluates each run (transcription + functional + conversational)
    - Runs in background (can take several minutes)
    
    **Returns:**
    - Acknowledgment that evaluation started
    - Count of test runs to be evaluated
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Count eligible test runs
    eligible_runs = db.query(TestRun).filter(
        TestRun.project_id == project_id,
        TestRun.status == TestRunStatus.SUCCESS,
        TestRun.audio_url.isnot(None)
    ).count()
    
    if eligible_runs == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed test runs with recordings found for this project"
        )
    
    # Start evaluation in background
    background_tasks.add_task(
        evaluation_service.evaluate_project_test_runs,
        db,
        project_id
    )
    
    return {
        "message": "Project evaluation started",
        "project_id": str(project_id),
        "test_runs_to_evaluate": eligible_runs,
        "status": "processing"
    }


@router.get("/projects/{project_id}/evaluation-summary")
def get_project_evaluation_summary(
    project_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get evaluation summary for a project
    
    **Returns:**
    - Total test runs
    - Evaluated count
    - Pass/fail counts
    - Average scores (functional & conversational)
    - Completion percentage
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    summary = evaluation_service.get_evaluation_summary(db, project_id)
    
    return {
        "project_id": str(project_id),
        "project_name": project.name,
        **summary
    }
