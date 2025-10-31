from passlib.context import CryptContext
from datetime import datetime
from typing import Optional
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()


def ensure_upload_dir(directory: str = "./uploads") -> str:
    """Ensure upload directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def success_response(data: any, message: str = "Success") -> dict:
    """Standard success response format"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str, details: Optional[dict] = None) -> dict:
    """Standard error response format"""
    response = {
        "success": False,
        "message": message
    }
    if details:
        response["details"] = details
    return response
