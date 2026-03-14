"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# Test Suite Schemas
# ============================================================================

class TestCaseBase(BaseModel):
    """Base schema for test case"""
    utterance: str = Field(..., min_length=1, description="What the caller says")
    expected_behavior: str = Field(..., min_length=1, description="Expected bot behavior")
    order: int = Field(default=0, description="Order in test suite")


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case"""
    pass


class TestCaseUpdate(BaseModel):
    """Schema for updating a test case"""
    utterance: Optional[str] = None
    expected_behavior: Optional[str] = None
    order: Optional[int] = None


class TestCaseResponse(TestCaseBase):
    """Schema for test case response"""
    id: UUID
    test_suite_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestSuiteBase(BaseModel):
    """Base schema for test suite"""
    name: str = Field(..., min_length=1, max_length=255)
    scenario: str = Field(..., min_length=1, description="Business context and caller identity")
    prompt: str = Field(..., min_length=1, description="Prompt used by bot under test")


class TestSuiteCreate(TestSuiteBase):
    """Schema for creating a test suite"""
    test_cases: Optional[List[TestCaseCreate]] = Field(default_factory=list)


class TestSuiteUpdate(BaseModel):
    """Schema for updating a test suite"""
    name: Optional[str] = None
    scenario: Optional[str] = None
    prompt: Optional[str] = None


class TestSuiteResponse(TestSuiteBase):
    """Schema for test suite response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    test_cases: List[TestCaseResponse] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Project Schemas
# ============================================================================

class ProjectBase(BaseModel):
    """Base schema for project"""
    name: str = Field(..., min_length=1, max_length=255)
    bot_phone_number: str = Field(..., pattern=r'^\+\d{10,15}$', description="Phone number with country code")
    number_of_calls: int = Field(default=1, ge=1, le=100, description="Number of calls per test case")
    
    @field_validator('bot_phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.startswith('+'):
            raise ValueError('Phone number must start with + and country code')
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    test_suite_ids: List[UUID] = Field(..., min_length=1, description="Test suites to attach")


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    bot_phone_number: Optional[str] = None
    number_of_calls: Optional[int] = None
    test_suite_ids: Optional[List[UUID]] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    test_suites: List[TestSuiteResponse] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Test Run Schemas
# ============================================================================

class TestRunResponse(BaseModel):
    """Schema for test run response"""
    id: UUID
    project_id: UUID
    test_case_id: UUID
    call_sid: Optional[str]
    status: str
    audio_url: Optional[str]
    transcript: Optional[str]
    functional_evaluation: Optional[dict]
    conversational_evaluation: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    @field_validator('functional_evaluation', 'conversational_evaluation', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dictionaries"""
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    class Config:
        from_attributes = True


# ============================================================================
# Evaluation Schemas
# ============================================================================

class FunctionalEvaluation(BaseModel):
    """Functional evaluation result"""
    auth_passed: Optional[bool] = None
    flow_correct: Optional[bool] = None
    call_terminated_properly: Optional[bool] = None
    errors: List[str] = []


class ConversationalEvaluation(BaseModel):
    """Conversational evaluation result"""
    working_well: List[str] = []
    needs_improvement: List[str] = []


class ProjectReport(BaseModel):
    """Aggregated project report"""
    project_id: UUID
    project_name: str
    status: str
    total_runs: int
    completed_runs: int
    success_rate: float
    functional_feedback: FunctionalEvaluation
    conversational_feedback: ConversationalEvaluation


# ============================================================================
# Test Case Generation
# ============================================================================

class GenerateTestCasesRequest(BaseModel):
    """Request to generate test cases via LLM"""
    count: int = Field(default=5, ge=1, le=20, description="Number of test cases to generate")


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    timestamp: datetime
