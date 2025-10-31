from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


# Course Models
class CourseBase(BaseModel):
    name: str
    description: str
    college_id: str
    subject_id: str
    faculty_id: str
    syllabus: Optional[str] = None
    duration_weeks: Optional[int] = None
    difficulty_level: Optional[str] = None  # beginner, intermediate, advanced


class CourseCreate(CourseBase):
    pass


class CourseInDB(CourseBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CourseResponse(CourseInDB):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[str] = None
    faculty_id: Optional[str] = None
    syllabus: Optional[str] = None
    duration_weeks: Optional[int] = None
    difficulty_level: Optional[str] = None