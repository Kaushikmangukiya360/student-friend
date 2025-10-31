from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# Subject Models
class SubjectBase(BaseModel):
    name: str
    description: str
    college_id: str
    category: Optional[str] = None  # e.g., "Science", "Arts", "Commerce"


class SubjectCreate(SubjectBase):
    pass


class SubjectInDB(SubjectBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SubjectResponse(SubjectInDB):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None