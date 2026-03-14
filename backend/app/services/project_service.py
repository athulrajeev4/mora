"""
Project Service Layer
Business logic for project and test execution management
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Project, TestSuite, TestRun, TestCase, ProjectStatus, TestRunStatus
from app.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for managing projects and test execution"""
    
    @staticmethod
    def create_project(db: Session, project: ProjectCreate) -> Project:
        """
        Create a new project and attach test suites
        """
        # Create project
        db_project = Project(
            name=project.name,
            bot_phone_number=project.bot_phone_number,
            number_of_calls=project.number_of_calls,
            status=ProjectStatus.PENDING
        )
        
        # Attach test suites (many-to-many)
        if project.test_suite_ids:
            for suite_id in project.test_suite_ids:
                test_suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
                if test_suite:
                    db_project.test_suites.append(test_suite)
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def get_project(db: Session, project_id: UUID) -> Optional[Project]:
        """Get a project by ID with all relationships loaded"""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination"""
        return db.query(Project).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_project(
        db: Session, 
        project_id: UUID, 
        project_update: ProjectUpdate
    ) -> Optional[Project]:
        """Update a project"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        
        if not db_project:
            return None
        
        # Update basic fields
        update_data = project_update.model_dump(exclude_unset=True, exclude={'test_suite_ids'})
        for field, value in update_data.items():
            setattr(db_project, field, value)
        
        # Update test suites if provided
        if project_update.test_suite_ids is not None:
            # Clear existing test suites
            db_project.test_suites = []
            
            # Add new test suites
            for suite_id in project_update.test_suite_ids:
                test_suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
                if test_suite:
                    db_project.test_suites.append(test_suite)
        
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def delete_project(db: Session, project_id: UUID) -> bool:
        """Delete a project and its test runs (cascade)"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        
        if not db_project:
            return False
        
        db.delete(db_project)
        db.commit()
        return True
    
    # ========================================================================
    # Project Activation & Test Run Creation
    # ========================================================================
    
    @staticmethod
    def activate_project(db: Session, project_id: UUID) -> Optional[Project]:
        """
        Activate a project and create test runs for all test cases
        
        For each test suite attached to the project:
            For each test case in the suite:
                Create N test runs (where N = number_of_calls)
        """
        db_project = db.query(Project).filter(Project.id == project_id).first()
        
        if not db_project:
            return None
        
        # Check if already running or completed
        if db_project.status in [ProjectStatus.RUNNING, ProjectStatus.COMPLETED]:
            return db_project
        
        # Update status to running
        db_project.status = ProjectStatus.RUNNING
        
        # Create one test run per test case (all will share a single phone call)
        for test_suite in db_project.test_suites:
            test_cases = db.query(TestCase).filter(
                TestCase.test_suite_id == test_suite.id
            ).all()
            
            for test_case in test_cases:
                test_run = TestRun(
                    project_id=db_project.id,
                    test_case_id=test_case.id,
                    status=TestRunStatus.PENDING,
                )
                db.add(test_run)
        
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def get_project_test_runs(db: Session, project_id: UUID) -> List[TestRun]:
        """Get all test runs for a project"""
        return db.query(TestRun).filter(TestRun.project_id == project_id).all()
    
    @staticmethod
    def update_project_status(
        db: Session, 
        project_id: UUID, 
        status: ProjectStatus
    ) -> Optional[Project]:
        """Update project status"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        
        if not db_project:
            return None
        
        db_project.status = status
        db.commit()
        db.refresh(db_project)
        return db_project
