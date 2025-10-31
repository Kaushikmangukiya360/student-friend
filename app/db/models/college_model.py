from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# College Models
class CollegeBase(BaseModel):
    name: str
    description: str
    location: Optional[str] = None
    website: Optional[str] = None


class CollegeCreate(CollegeBase):
    pass


class CollegeInDB(CollegeBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CollegeResponse(CollegeInDB):
    pass


class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None