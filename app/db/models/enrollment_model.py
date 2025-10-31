from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# Enrollment Models
class EnrollmentBase(BaseModel):
    student_id: str
    course_id: str
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, completed, dropped


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentInDB(EnrollmentBase):
    id: str = Field(alias="_id")
    progress_percentage: float = 0.0
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class EnrollmentResponse(EnrollmentInDB):
    pass


class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[float] = None