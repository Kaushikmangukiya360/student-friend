from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# OTP Models
class OTPBase(BaseModel):
    email: str
    otp_code: str
    purpose: str  # registration, login, password_reset, email_verification
    expires_at: datetime
    is_used: bool = False


class OTPCreate(OTPBase):
    pass


class OTPInDB(OTPBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class OTPResponse(OTPInDB):
    pass


class OTPRequest(BaseModel):
    email: str
    purpose: str = "registration"


class OTPVerifyRequest(BaseModel):
    email: str
    otp_code: str
    purpose: str = "registration"