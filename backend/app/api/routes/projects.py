"""
Project API Routes
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    TestRunResponse
)
from app.services.project_service import ProjectService

router = APIRouter()


# ============================================================================
# Project Endpoints
# ============================================================================

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new project
    
    **Request Body:**
    - name: Project name
    - bot_phone_number: Phone number to call (with country code, e.g., +14155552671)
    - number_of_calls: How many times to run each test case (1-100)
    - test_suite_ids: Array of test suite IDs to attach
    
    **Returns:**
    - Created project with attached test suites
    """
    # Validate that at least one test suite exists
    if not project.test_suite_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one test suite must be attached to the project"
        )
    
    return ProjectService.create_project(db, project)


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all projects with pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
    return ProjectService.get_projects(db, skip=skip, limit=limit)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID
    
    **Returns:**
    - Project with attached test suites and current status
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a project
    
    **Request Body:**
    - name: (optional) Updated name
    - bot_phone_number: (optional) Updated phone number
    - number_of_calls: (optional) Updated call count
    - test_suite_ids: (optional) Updated test suite attachments
    
    **Note:** Cannot update a project that is already running
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Prevent updates to running projects
    if project.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a project that is currently running"
        )
    
    updated_project = ProjectService.update_project(db, project_id, project_update)
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a project and all its test runs
    
    **Note:** Cannot delete a project that is currently running
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Prevent deletion of running projects
    if project.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a project that is currently running"
        )
    
    ProjectService.delete_project(db, project_id)
    return None


# ============================================================================
# Project Activation & Execution
# ============================================================================

@router.post("/{project_id}/activate", response_model=ProjectResponse)
async def activate_project(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Activate a project - creates test runs and starts AI-powered test calls
    
    **NEW ARCHITECTURE:**
    1. Changes project status to "running"
    2. Creates test runs for all test cases in attached test suites
    3. Each test case gets N test runs (where N = number_of_calls)
    4. For each test run:
       - Creates LiveKit room with test caller AI agent
       - Agent loads persona from test suite scenario
       - Makes OUTBOUND call to user's bot
       - AI agent executes conversation script
       - Evaluates bot responses in real-time
       - Stores transcript and evaluation results
    
    **Background Process:**
    - Calls are made asynchronously via BackgroundTasks
    - AI agents handle the actual testing conversation
    - Results are stored in database when complete
    
    **Returns:**
    - Project with status "running"
    - Test runs created and ready for execution
    """
    from app.services.call_orchestration_service import call_orchestration_service
    from app.core.config import settings
    import asyncio
    
    project = ProjectService.activate_project(db, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Execute project test runs using NEW orchestration service
    # This runs in background and makes AI-powered test calls
    async def run_project_tests():
        """Background task to execute all test runs"""
        from app.core.database import SessionLocal

        task_db = SessionLocal()
        try:
            fresh_project = ProjectService.get_project(task_db, project_id)
            if not fresh_project:
                print(f"❌ Project {project_id} not found for execution")
                return
            await call_orchestration_service.execute_project(task_db, fresh_project)
        except Exception as e:
            print(f"❌ Error executing project: {e}")
        finally:
            task_db.close()
    
    # Add background task
    background_tasks.add_task(run_project_tests
    )
    
    return project


@router.get("/{project_id}/runs", response_model=List[TestRunResponse])
def get_project_test_runs(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all test runs for a project
    
    **Returns:**
    - Array of test runs with their current status
    - Includes call metadata, transcripts, and evaluation results (when available)
    """
    # Verify project exists
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return ProjectService.get_project_test_runs(db, project_id)
