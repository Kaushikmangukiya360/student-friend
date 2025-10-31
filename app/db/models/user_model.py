from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# User Models
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Literal["student", "faculty", "admin"]
    institution: Optional[str] = None
    college_id: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    verified: bool = False
    wallet_balance: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    id: str
    verified: bool
    wallet_balance: float
    created_at: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = None
    institution: Optional[str] = None
    college_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
