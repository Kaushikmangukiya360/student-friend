from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


# Session Models
class SessionBase(BaseModel):
    faculty_id: str
    course_id: str
    scheduled_time: datetime
    duration_minutes: int = 60
    topic: str
    amount: float


class SessionCreate(SessionBase):
    pass


class SessionInDB(SessionBase):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    session_id: str
    student_id: str
    status: Literal["pending", "accepted", "rejected", "completed", "cancelled"] = "pending"
    payment_status: Literal["pending", "completed", "refunded"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    meeting_link: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SessionResponse(SessionInDB):
    pass


class SessionUpdate(BaseModel):
    status: Optional[Literal["accepted", "rejected", "completed", "cancelled"]] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


# Transaction Models
class TransactionBase(BaseModel):
    amount: float
    type: Literal["credit", "debit"]
    purpose: str


class TransactionCreate(TransactionBase):
    user_id: str


class TransactionInDB(TransactionBase):
    id: str = Field(alias="_id")
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reference_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TransactionResponse(TransactionInDB):
    pass


# Notification Models
class NotificationBase(BaseModel):
    message: str
    type: Literal["info", "success", "warning", "error"] = "info"


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationInDB(NotificationBase):
    id: str = Field(alias="_id")
    user_id: str
    read_status: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class NotificationResponse(NotificationInDB):
    pass
