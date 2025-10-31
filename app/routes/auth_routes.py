from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.db.models.user_model import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.db.models.otp_model import OTPRequest, OTPVerifyRequest
from app.db.connection import get_database
from app.utils.helpers import hash_password, verify_password, success_response, error_response, get_timestamp
from app.utils.enhanced_responses import (
    success_response as enhanced_success_response,
    error_response as enhanced_error_response,
    ValidationException,
    NotFoundException,
    ConflictException,
    validate_email,
    validate_object_id,
    sanitize_string
)
from app.utils.jwt_handler import create_access_token
from app.core.auth import get_current_user
from app.services.otp_service import otp_service
from app.services.email_service import email_service
from app.middleware.caching import cached
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel, validator
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class PasswordResetRequest(BaseModel):
    email: str

    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(v)


class PasswordResetConfirm(BaseModel):
    email: str
    otp: str
    new_password: str

    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(v)

    @validator('otp')
    def validate_otp_format(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be 6 digits')
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, request: Request):
    """Register a new user - sends OTP for verification"""
    try:
        logger.info(f"Registration attempt for email: {user.email}")

        # Validate and sanitize inputs
        user.email = validate_email(user.email)
        user.name = sanitize_string(user.name, 100)
        user.institution = sanitize_string(user.institution or "", 200)

        # Validate role
        if user.role not in ["student", "faculty"]:
            raise ValidationException("Role must be either 'student' or 'faculty'")

        db = get_database()

        # Check if user already exists
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            logger.warning(f"Registration failed: Email already exists - {user.email}")
            raise ConflictException("Email already registered")

        # Check for existing temp registration
        existing_temp = await db.temp_registrations.find_one({"email": user.email})
        if existing_temp:
            # Clean up expired temp registration
            if existing_temp.get("expires_at", 0) < get_timestamp():
                await db.temp_registrations.delete_one({"email": user.email})
            else:
                raise ConflictException("Registration already in progress. Please check your email for OTP.")

        # Store registration data temporarily
        temp_user_data = {
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "institution": user.institution,
            "password": user.password,  # Will be hashed after OTP verification
            "created_at": get_timestamp(),
            "ip_address": request.client.host if request.client else None
        }

        # Store temp data in database
        await db.temp_registrations.insert_one({
            "email": user.email,
            "data": temp_user_data,
            "expires_at": get_timestamp() + 600,  # 10 minutes
            "attempts": 0
        })

        # Send OTP
        try:
            await otp_service.create_otp(user.email, "registration")
            logger.info(f"OTP sent successfully for registration: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send OTP for registration: {user.email} - {str(e)}")
            # Clean up temp registration on OTP failure
            await db.temp_registrations.delete_one({"email": user.email})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email. Please try again."
            )

        return enhanced_success_response(
            data={
                "email": user.email,
                "message": "OTP sent to your email. Please verify to complete registration."
            },
            message="Registration initiated. Please check your email for OTP."
        )

    except ValidationException as e:
        logger.warning(f"Validation error during registration: {str(e)}")
        raise
    except ConflictException as e:
        logger.warning(f"Conflict during registration: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/verify-otp", response_model=dict)
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP and complete registration/login"""
    try:
        logger.info(f"OTP verification attempt for {request.email} - purpose: {request.purpose}")

        # Validate email
        request.email = validate_email(request.email)

        # Validate purpose
        if request.purpose not in ["registration", "login", "password_reset"]:
            raise ValidationException("Invalid OTP purpose")

        db = get_database()

        # Verify OTP with rate limiting
        temp_reg = await db.temp_registrations.find_one({"email": request.email})
        if temp_reg and temp_reg.get("attempts", 0) >= 5:
            logger.warning(f"Too many OTP attempts for {request.email}")
            raise ValidationException("Too many failed attempts. Please request a new OTP.")

        is_valid = await otp_service.verify_otp(request.email, request.otp_code, request.purpose)

        if not is_valid:
            # Increment failed attempts
            if temp_reg:
                await db.temp_registrations.update_one(
                    {"email": request.email},
                    {"$inc": {"attempts": 1}}
                )
            logger.warning(f"Invalid OTP for {request.email}")
            raise ValidationException("Invalid or expired OTP")

        # Reset attempts on success
        if temp_reg:
            await db.temp_registrations.update_one(
                {"email": request.email},
                {"$set": {"attempts": 0}}
            )

        if request.purpose == "registration":
            # Complete registration
            temp_registration = await db.temp_registrations.find_one({
                "email": request.email,
                "expires_at": {"$gt": get_timestamp()}
            })

            if not temp_registration:
                logger.warning(f"Registration session expired for {request.email}")
                raise ValidationException("Registration session expired. Please register again.")

            user_data = temp_registration["data"]

            # Check if user already exists (double-check)
            existing_user = await db.users.find_one({"email": request.email})
            if existing_user:
                await db.temp_registrations.delete_one({"email": request.email})
                raise ConflictException("Email already registered")

            # Create user document
            user_doc = {
                "name": user_data["name"],
                "email": user_data["email"],
                "role": user_data["role"],
                "institution": user_data.get("institution"),
                "hashed_password": hash_password(user_data["password"]),
                "verified": user_data["role"] == "student",  # Students are auto-verified
                "email_verified": True,
                "wallet_balance": 0.0,
                "created_at": user_data["created_at"],
                "last_login": get_timestamp()
            }

            # Insert user
            result = await db.users.insert_one(user_doc)

            # Clean up temp registration
            await db.temp_registrations.delete_one({"email": request.email})

            # Create token
            token_data = {
                "user_id": str(result.inserted_id),
                "email": user_data["email"],
                "role": user_data["role"]
            }
            access_token = create_access_token(token_data)

            # Send welcome email (non-blocking)
            try:
                await email_service.send_welcome_email(user_data["email"], user_data["name"])
            except Exception as e:
                logger.error(f"Failed to send welcome email to {user_data['email']}: {str(e)}")

            # Prepare response
            user_response = UserResponse(
                id=str(result.inserted_id),
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                institution=user_data.get("institution"),
                verified=user_doc["verified"],
                wallet_balance=user_doc["wallet_balance"],
                created_at=user_doc["created_at"]
            )

            logger.info(f"Registration completed successfully for {request.email}")
            return enhanced_success_response(
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": user_response.dict()
                },
                message="Registration completed successfully"
            )

        elif request.purpose == "login":
            # Handle login verification
            user = await db.users.find_one({"email": request.email})
            if not user:
                logger.warning(f"Login attempt for non-existent user: {request.email}")
                raise NotFoundException("user", request.email)

            # Update last login
            await db.users.update_one(
                {"email": request.email},
                {"$set": {"last_login": get_timestamp()}}
            )

            # Create token
            token_data = {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "role": user["role"]
            }
            access_token = create_access_token(token_data)

            # Prepare response
            user_response = UserResponse(
                id=str(user["_id"]),
                name=user["name"],
                email=user["email"],
                role=user["role"],
                institution=user.get("institution"),
                verified=user["verified"],
                wallet_balance=user["wallet_balance"],
                created_at=user["created_at"]
            )

            logger.info(f"Login successful for {request.email}")
            return enhanced_success_response(
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": user_response.dict()
                },
                message="Login successful"
            )

        elif request.purpose == "password_reset":
            # Handle password reset verification
            user = await db.users.find_one({"email": request.email})
            if not user:
                raise NotFoundException("user", request.email)

            # Mark OTP as used for password reset
            await otp_service.mark_otp_used(request.email, request.otp_code, "password_reset")

            logger.info(f"Password reset OTP verified for {request.email}")
            return enhanced_success_response(
                data={"email": request.email},
                message="OTP verified. You can now reset your password."
            )

        else:
            raise ValidationException("Invalid OTP purpose")

    except ValidationException as e:
        logger.warning(f"Validation error during OTP verification: {str(e)}")
        raise
    except NotFoundException as e:
        logger.warning(f"Not found error during OTP verification: {str(e)}")
        raise
    except ConflictException as e:
        logger.warning(f"Conflict error during OTP verification: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during OTP verification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed. Please try again."
        )


@router.post("/resend-otp", response_model=dict)
async def resend_otp(request: OTPRequest):
    """Resend OTP for registration or login"""
    db = get_database()
    
    # Check if email exists for login, or allow for registration
    if request.purpose == "login":
        user = await db.users.find_one({"email": request.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    # Resend OTP
    await otp_service.resend_otp(request.email, request.purpose)
    
    return success_response(
        data={"email": request.email},
        message="OTP resent successfully"
    )


@router.post("/login", response_model=dict)
async def login(credentials: LoginRequest):
    """Login user - sends OTP for verification"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Send OTP for login verification
    await otp_service.create_otp(credentials.email, "login")
    
    return success_response(
        data={
            "email": credentials.email,
            "message": "OTP sent to your email. Please verify to complete login."
        },
        message="Login initiated. Please check your email for OTP."
    )


@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    db = get_database()
    
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_response = UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user["role"],
        institution=user.get("institution"),
        verified=user["verified"],
        wallet_balance=user["wallet_balance"],
        created_at=user["created_at"]
    )
    
    return success_response(
        data=user_response.dict(),
        message="Profile retrieved successfully"
    )


@router.get("/verify/{user_id}", response_model=dict)
async def verify_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Verify a user account (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can verify users"
        )
    
    db = get_database()
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"verified": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return success_response(
        data={"user_id": user_id, "verified": True},
        message="User verified successfully"
    )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: PasswordResetRequest):
    """Send OTP for password reset"""
    try:
        logger.info(f"Password reset request for email: {request.email}")

        # Validate email
        request.email = validate_email(request.email)

        db = get_database()

        # Check if user exists (but don't reveal this in response for security)
        user = await db.users.find_one({"email": request.email})

        if user:
            # Check for rate limiting on password reset attempts
            recent_resets = await db.password_reset_attempts.count_documents({
                "email": request.email,
                "timestamp": {"$gt": get_timestamp() - 3600}  # Last hour
            })

            if recent_resets >= 3:
                logger.warning(f"Too many password reset attempts for {request.email}")
                # Still return success message for security
                return enhanced_success_response(
                    data={"email": request.email},
                    message="If the email exists, an OTP has been sent for password reset"
                )

            # Send OTP for password reset
            try:
                await otp_service.create_otp(request.email, "password_reset")

                # Log the attempt
                await db.password_reset_attempts.insert_one({
                    "email": request.email,
                    "timestamp": get_timestamp(),
                    "ip_address": None  # Could be added from request
                })

                logger.info(f"Password reset OTP sent to {request.email}")
            except Exception as e:
                logger.error(f"Failed to send password reset OTP to {request.email}: {str(e)}")
                # Don't reveal the error to prevent email enumeration
        else:
            logger.info(f"Password reset attempted for non-existent email: {request.email}")

        return enhanced_success_response(
            data={"email": request.email},
            message="If the email exists, an OTP has been sent for password reset"
        )

    except ValidationException as e:
        logger.warning(f"Validation error in forgot password: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in forgot password: {str(e)}", exc_info=True)
        # Return generic success for security
        return enhanced_success_response(
            data={"email": request.email},
            message="If the email exists, an OTP has been sent for password reset"
        )


@router.post("/reset-password", response_model=dict)
async def reset_password(request: PasswordResetConfirm):
    """Reset password using OTP"""
    try:
        logger.info(f"Password reset attempt for {request.email}")

        # Validate email
        request.email = validate_email(request.email)

        db = get_database()

        # Verify OTP
        otp_valid = await otp_service.verify_otp(request.email, request.otp, "password_reset")
        if not otp_valid:
            logger.warning(f"Invalid OTP for password reset: {request.email}")
            raise ValidationException("Invalid or expired OTP")

        # Check if user exists
        user = await db.users.find_one({"email": request.email})
        if not user:
            logger.warning(f"Password reset for non-existent user: {request.email}")
            raise NotFoundException("user", request.email)

        # Hash new password
        hashed_password = hash_password(request.new_password)

        # Update password
        result = await db.users.update_one(
            {"email": request.email},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "password_reset_at": get_timestamp()
                }
            }
        )

        if result.modified_count == 0:
            logger.error(f"Failed to update password for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )

        # Mark OTP as used
        await otp_service.mark_otp_used(request.email, request.otp, "password_reset")

        # Clean up old reset attempts
        await db.password_reset_attempts.delete_many({
            "email": request.email,
            "timestamp": {"$lt": get_timestamp() - 86400}  # Older than 24 hours
        })

        logger.info(f"Password reset successful for {request.email}")
        return enhanced_success_response(
            data={"email": request.email},
            message="Password reset successfully"
        )

    except ValidationException as e:
        logger.warning(f"Validation error in reset password: {str(e)}")
        raise
    except NotFoundException as e:
        logger.warning(f"Not found error in reset password: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in reset password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change password for authenticated user"""
    try:
        logger.info(f"Password change attempt for user: {current_user['user_id']}")

        # Validate user ID
        user_id = validate_object_id(current_user["user_id"])

        db = get_database()

        # Get user
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            logger.warning(f"Password change for non-existent user: {user_id}")
            raise NotFoundException("user", user_id)

        # Verify current password
        if not verify_password(request.current_password, user.get("hashed_password", user.get("password", ""))):
            logger.warning(f"Invalid current password for user: {user_id}")
            raise ValidationException("Current password is incorrect")

        # Check if new password is different from current
        if verify_password(request.new_password, user.get("hashed_password", user.get("password", ""))):
            raise ValidationException("New password must be different from current password")

        # Hash new password
        hashed_password = hash_password(request.new_password)

        # Update password
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "password_changed_at": get_timestamp()
                }
            }
        )

        if result.modified_count == 0:
            logger.error(f"Failed to update password for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )

        logger.info(f"Password changed successfully for user: {user_id}")
        return enhanced_success_response(
            data={"user_id": user_id},
            message="Password changed successfully"
        )

    except ValidationException as e:
        logger.warning(f"Validation error in change password: {str(e)}")
        raise
    except NotFoundException as e:
        logger.warning(f"Not found error in change password: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in change password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )
