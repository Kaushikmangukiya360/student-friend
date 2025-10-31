from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
from bson import ObjectId


# Material Models
class MaterialBase(BaseModel):
    title: str
    description: str
    subject: str
    course_id: str
    tags: List[str] = []
    visibility: Literal["public", "private"] = "public"


class MaterialCreate(MaterialBase):
    file_url: str


class MaterialInDB(MaterialBase):
    id: str = Field(alias="_id")
    file_url: str
    uploaded_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MaterialResponse(MaterialInDB):
    pass


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    course_id: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[Literal["public", "private"]] = None
