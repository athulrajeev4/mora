"""
Test Suite Service Layer
Business logic for test suite and test case management
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import TestSuite, TestCase
from app.schemas import (
    TestSuiteCreate, 
    TestSuiteUpdate, 
    TestCaseCreate, 
    TestCaseUpdate
)


class TestSuiteService:
    """Service for managing test suites and test cases"""
    
    @staticmethod
    def create_test_suite(db: Session, test_suite: TestSuiteCreate) -> TestSuite:
        """
        Create a new test suite with optional test cases
        """
        # Create test suite
        db_test_suite = TestSuite(
            name=test_suite.name,
            scenario=test_suite.scenario,
            prompt=test_suite.prompt
        )
        
        # Add test cases if provided
        if test_suite.test_cases:
            for idx, test_case_data in enumerate(test_suite.test_cases):
                test_case = TestCase(
                    utterance=test_case_data.utterance,
                    expected_behavior=test_case_data.expected_behavior,
                    order=test_case_data.order if test_case_data.order else idx
                )
                db_test_suite.test_cases.append(test_case)
        
        db.add(db_test_suite)
        db.commit()
        db.refresh(db_test_suite)
        return db_test_suite
    
    @staticmethod
    def get_test_suite(db: Session, test_suite_id: UUID) -> Optional[TestSuite]:
        """Get a test suite by ID"""
        return db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()
    
    @staticmethod
    def get_test_suites(db: Session, skip: int = 0, limit: int = 100) -> List[TestSuite]:
        """Get all test suites with pagination"""
        return db.query(TestSuite).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_test_suite(
        db: Session, 
        test_suite_id: UUID, 
        test_suite_update: TestSuiteUpdate
    ) -> Optional[TestSuite]:
        """Update a test suite"""
        db_test_suite = db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()
        
        if not db_test_suite:
            return None
        
        # Update only provided fields
        update_data = test_suite_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_test_suite, field, value)
        
        db.commit()
        db.refresh(db_test_suite)
        return db_test_suite
    
    @staticmethod
    def delete_test_suite(db: Session, test_suite_id: UUID) -> bool:
        """Delete a test suite and its test cases (cascade)"""
        db_test_suite = db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()
        
        if not db_test_suite:
            return False
        
        db.delete(db_test_suite)
        db.commit()
        return True
    
    # ========================================================================
    # Test Case Management
    # ========================================================================
    
    @staticmethod
    def add_test_case(
        db: Session, 
        test_suite_id: UUID, 
        test_case: TestCaseCreate
    ) -> Optional[TestCase]:
        """Add a test case to a test suite"""
        db_test_suite = db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()
        
        if not db_test_suite:
            return None
        
        db_test_case = TestCase(
            test_suite_id=test_suite_id,
            utterance=test_case.utterance,
            expected_behavior=test_case.expected_behavior,
            order=test_case.order
        )
        
        db.add(db_test_case)
        db.commit()
        db.refresh(db_test_case)
        return db_test_case
    
    @staticmethod
    def get_test_case(db: Session, test_case_id: UUID) -> Optional[TestCase]:
        """Get a specific test case"""
        return db.query(TestCase).filter(TestCase.id == test_case_id).first()
    
    @staticmethod
    def update_test_case(
        db: Session, 
        test_case_id: UUID, 
        test_case_update: TestCaseUpdate
    ) -> Optional[TestCase]:
        """Update a test case"""
        db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        
        if not db_test_case:
            return None
        
        # Update only provided fields
        update_data = test_case_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_test_case, field, value)
        
        db.commit()
        db.refresh(db_test_case)
        return db_test_case
    
    @staticmethod
    def delete_test_case(db: Session, test_case_id: UUID) -> bool:
        """Delete a test case"""
        db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        
        if not db_test_case:
            return False
        
        db.delete(db_test_case)
        db.commit()
        return True
