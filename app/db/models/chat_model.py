from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


# Chat Models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatConversationBase(BaseModel):
    user_id: str
    title: Optional[str] = None
    subject: Optional[str] = None
    course_id: Optional[str] = None


class ChatConversationCreate(ChatConversationBase):
    pass


class ChatConversationInDB(ChatConversationBase):
    id: str = Field(alias="_id")
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChatConversationResponse(ChatConversationInDB):
    pass


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None  # If None, create new conversation


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)