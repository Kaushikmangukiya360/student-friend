from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId


# Mock Test Models
class Question(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: int  # Index of correct option
    marks: int = 1


class TestBase(BaseModel):
    test_title: str
    description: Optional[str] = None
    subject: str
    course_id: str
    duration_minutes: int = 30
    total_marks: int


class TestCreate(TestBase):
    questions: List[Question]


class TestInDB(TestBase):
    id: str = Field(alias="_id")
    questions: List[Question]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TestResponse(TestInDB):
    pass


class TestAttempt(BaseModel):
    test_id: str
    student_id: str
    answers: List[int]  # List of selected option indices
    score: int
    total_marks: int
    percentage: float
    started_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class TestSubmission(BaseModel):
    answers: List[int]


class TestResult(BaseModel):
    test_id: str
    test_title: str
    score: int
    total_marks: int
    percentage: float
    answers: List[Dict[str, Any]]
    submitted_at: datetime


# Assignment Models
class AssignmentBase(BaseModel):
    title: str
    description: str
    subject: str
    course_id: str
    total_marks: int


class AssignmentCreate(AssignmentBase):
    assigned_to: List[str]  # List of student IDs
    due_date: datetime


class SubmissionData(BaseModel):
    student_id: str
    submission_text: Optional[str] = None
    file_url: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    marks_obtained: Optional[int] = None
    feedback: Optional[str] = None


class AssignmentInDB(AssignmentBase):
    id: str = Field(alias="_id")
    created_by: str
    assigned_to: List[str]
    due_date: datetime
    submissions: List[SubmissionData] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AssignmentResponse(AssignmentInDB):
    pass


class AssignmentSubmit(BaseModel):
    submission_text: Optional[str] = None
    file_url: Optional[str] = None


class TestUpdate(BaseModel):
    test_title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    course_id: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    questions: Optional[List[Question]] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    course_id: Optional[str] = None
    total_marks: Optional[int] = None
    assigned_to: Optional[List[str]] = None
    due_date: Optional[datetime] = None
