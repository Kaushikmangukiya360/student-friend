from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Union
import logging
from pydantic import ValidationError
import traceback

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(AppException):
    """Validation error exception"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )

class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )

class UnauthorizedException(AppException):
    """Unauthorized access exception"""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )

class ForbiddenException(AppException):
    """Forbidden access exception"""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )

class ConflictException(AppException):
    """Resource conflict exception"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details
        )

def handle_app_exception(exc: AppException) -> JSONResponse:
    """Handle application exceptions"""
    logger.error(f"AppException: {exc.message}", extra={
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "details": exc.details
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

def handle_validation_error(exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"ValidationError: {len(errors)} validation errors", extra={
        "errors": errors
    })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": "Validation failed",
            "error_code": "VALIDATION_FAILED",
            "details": {"errors": errors}
        }
    )

def handle_http_exception(exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.error(f"HTTPException: {exc.detail}", extra={
        "status_code": exc.status_code
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": "HTTP_ERROR"
        }
    )

def handle_generic_exception(exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc()
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        }
    )

# Enhanced response helpers
def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

    if data is not None:
        response["data"] = data

    if meta:
        response["meta"] = meta

    return response

def error_response(
    message: str = "An error occurred",
    error_code: str = "ERROR",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response"""
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

    if details:
        response["details"] = details

    return response

def paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
    message: str = "Data retrieved successfully"
) -> Dict[str, Any]:
    """Create a paginated response"""
    return success_response(
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit  # Ceiling division
            }
        },
        message=message,
        meta={
            "total_count": total,
            "current_page": page,
            "per_page": limit
        }
    )

# Input validation helpers
def validate_object_id(id_str: str, field_name: str = "ID") -> str:
    """Validate MongoDB ObjectId format"""
    if not id_str or len(id_str) != 24:
        raise ValidationException(f"Invalid {field_name} format")

    try:
        # Try to create ObjectId to validate format
        from bson import ObjectId
        ObjectId(id_str)
        return id_str
    except:
        raise ValidationException(f"Invalid {field_name} format")

def validate_email(email: str) -> str:
    """Validate email format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        raise ValidationException("Invalid email format")

    return email.lower().strip()

def validate_phone(phone: str) -> str:
    """Validate phone number format"""
    import re
    # Basic international phone validation
    phone_pattern = r'^\+?[1-9]\d{1,14}$'

    # Remove spaces, dashes, etc.
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)

    if not re.match(phone_pattern, clean_phone):
        raise ValidationException("Invalid phone number format")

    return clean_phone

def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not text:
        return ""

    # Remove potentially dangerous characters
    import re
    # Allow alphanumeric, spaces, and basic punctuation
    sanitized = re.sub(r'[^\w\s\.,!?\-\'\"]', '', text)

    # Trim whitespace and limit length
    return sanitized.strip()[:max_length]