from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


# Query Models
class QueryBase(BaseModel):
    question_text: str
    subject: Optional[str] = None


class QueryCreate(QueryBase):
    pass


class QueryInDB(QueryBase):
    id: str = Field(alias="_id")
    asked_by: str
    answered_by: Optional[str] = None
    answer_text: Optional[str] = None
    answered_by_type: Optional[Literal["faculty", "ai"]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class QueryResponse(QueryInDB):
    pass


class AnswerQuery(BaseModel):
    answer_text: str
