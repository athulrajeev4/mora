"""
SQLAlchemy Database Models for Mora
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


# Association table for many-to-many relationship between Project and TestSuite
project_test_suites = Table(
    'project_test_suites',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE')),
    Column('test_suite_id', UUID(as_uuid=True), ForeignKey('test_suites.id', ondelete='CASCADE'))
)


class ProjectStatus(str, enum.Enum):
    """Project execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestRunStatus(str, enum.Enum):
    """Individual test run status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


class TestSuite(Base):
    """Test Suite containing multiple test cases"""
    __tablename__ = "test_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    scenario = Column(Text, nullable=False)  # Business context, auth details, caller identity
    prompt = Column(Text, nullable=False)  # Prompt used by the bot under test
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_cases = relationship("TestCase", back_populates="test_suite", cascade="all, delete-orphan")
    projects = relationship("Project", secondary=project_test_suites, back_populates="test_suites")


class TestCase(Base):
    """Individual test case within a test suite"""
    __tablename__ = "test_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_suite_id = Column(UUID(as_uuid=True), ForeignKey('test_suites.id', ondelete='CASCADE'), nullable=False)
    utterance = Column(Text, nullable=False)  # What the caller says
    expected_behavior = Column(Text, nullable=False)  # What the bot should do
    order = Column(Integer, default=0)  # Order in the test suite
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_suite = relationship("TestSuite", back_populates="test_cases")
    test_runs = relationship(
        "TestRun",
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Project(Base):
    """Project represents a test execution configuration"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    bot_phone_number = Column(String(20), nullable=False)  # Phone number to call
    number_of_calls = Column(Integer, nullable=False, default=1)  # How many times to run each test
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_suites = relationship("TestSuite", secondary=project_test_suites, back_populates="projects")
    test_runs = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")


class TestRun(Base):
    """Individual execution of a test case"""
    __tablename__ = "test_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey('test_cases.id', ondelete='CASCADE'), nullable=False)
    
    # Call metadata
    call_sid = Column(String(255), nullable=True)  # Twilio call SID
    status = Column(Enum(TestRunStatus), default=TestRunStatus.PENDING)
    
    # Artifacts
    audio_url = Column(String(500), nullable=True)  # URL to recording
    transcript = Column(Text, nullable=True)  # Full conversation transcript
    
    # Evaluation results
    functional_evaluation = Column(JSON, nullable=True)  # Rule-based evaluation
    conversational_evaluation = Column(JSON, nullable=True)  # LLM-based evaluation
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="test_runs")
    test_case = relationship("TestCase", back_populates="test_runs", passive_deletes=True)
