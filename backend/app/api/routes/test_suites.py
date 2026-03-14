"""
Test Suite API Routes
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    TestSuiteCreate, 
    TestSuiteUpdate, 
    TestSuiteResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse
)
from app.services.test_suite_service import TestSuiteService

router = APIRouter()


# ============================================================================
# Test Suite Endpoints
# ============================================================================

@router.post("/", response_model=TestSuiteResponse, status_code=status.HTTP_201_CREATED)
def create_test_suite(
    test_suite: TestSuiteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new test suite with optional test cases
    
    **Request Body:**
    - name: Test suite name
    - scenario: Business context and caller identity
    - prompt: Prompt used by bot under test
    - test_cases: (optional) List of test cases
    """
    return TestSuiteService.create_test_suite(db, test_suite)


@router.get("/", response_model=List[TestSuiteResponse])
def list_test_suites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all test suites with pagination
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    """
    return TestSuiteService.get_test_suites(db, skip=skip, limit=limit)


@router.get("/{test_suite_id}", response_model=TestSuiteResponse)
def get_test_suite(
    test_suite_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific test suite by ID
    """
    test_suite = TestSuiteService.get_test_suite(db, test_suite_id)
    if not test_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite with id {test_suite_id} not found"
        )
    return test_suite


@router.put("/{test_suite_id}", response_model=TestSuiteResponse)
def update_test_suite(
    test_suite_id: UUID,
    test_suite_update: TestSuiteUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a test suite
    
    **Request Body:**
    - name: (optional) Updated name
    - scenario: (optional) Updated scenario
    - prompt: (optional) Updated prompt
    """
    test_suite = TestSuiteService.update_test_suite(db, test_suite_id, test_suite_update)
    if not test_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite with id {test_suite_id} not found"
        )
    return test_suite


@router.delete("/{test_suite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_suite(
    test_suite_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a test suite and all its test cases
    """
    success = TestSuiteService.delete_test_suite(db, test_suite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite with id {test_suite_id} not found"
        )
    return None


# ============================================================================
# Test Case Endpoints
# ============================================================================

@router.post("/{test_suite_id}/cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def add_test_case(
    test_suite_id: UUID,
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """
    Add a test case to a test suite
    
    **Request Body:**
    - utterance: What the caller says
    - expected_behavior: Expected bot behavior
    - order: (optional) Order in the test suite
    """
    test_case_obj = TestSuiteService.add_test_case(db, test_suite_id, test_case)
    if not test_case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite with id {test_suite_id} not found"
        )
    return test_case_obj


@router.put("/{test_suite_id}/cases/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_suite_id: UUID,
    test_case_id: UUID,
    test_case_update: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a test case
    
    **Request Body:**
    - utterance: (optional) Updated utterance
    - expected_behavior: (optional) Updated expected behavior
    - order: (optional) Updated order
    """
    # Verify test case belongs to test suite
    test_case = TestSuiteService.get_test_case(db, test_case_id)
    if not test_case or test_case.test_suite_id != test_suite_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with id {test_case_id} not found in test suite {test_suite_id}"
        )
    
    updated_test_case = TestSuiteService.update_test_case(db, test_case_id, test_case_update)
    return updated_test_case


@router.delete("/{test_suite_id}/cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(
    test_suite_id: UUID,
    test_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a test case from a test suite
    """
    # Verify test case belongs to test suite
    test_case = TestSuiteService.get_test_case(db, test_case_id)
    if not test_case or test_case.test_suite_id != test_suite_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with id {test_case_id} not found in test suite {test_suite_id}"
        )
    
    TestSuiteService.delete_test_case(db, test_case_id)
    return None


# ============================================================================
# AI Test Case Generation
# ============================================================================

@router.post("/generate-test-cases", response_model=List[dict])
def generate_test_cases(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Generate test cases using LLM based on scenario and prompt
    
    **Request Body:**
    - scenario: Business context with auth details, caller identity
    - prompt: Bot system prompt to test against
    - num_cases: (optional) Number of test cases to generate (default 5)
    
    **Response:**
    List of generated test cases with utterance and expected_behavior
    """
    from app.services.llm_service import llm_service
    
    scenario = request.get("scenario", "")
    prompt = request.get("prompt", "")
    num_cases = request.get("num_cases", 5)
    
    if not scenario or not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'scenario' and 'prompt' are required"
        )
    
    if num_cases < 1 or num_cases > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_cases must be between 1 and 20"
        )
    
    try:
        test_cases = llm_service.generate_test_cases(scenario, prompt, num_cases)
        return test_cases
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test cases: {str(e)}"
        )
