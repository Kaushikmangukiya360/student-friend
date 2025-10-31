import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.db.connection import get_database
from app.db.models.otp_model import OTPCreate, OTPResponse
from app.services.email_service import email_service


class OTPService:
    """OTP service for generating and verifying one-time passwords"""

    def __init__(self):
        self.otp_length = 6
        self.otp_expiry_minutes = 10

    def generate_otp(self) -> str:
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=self.otp_length))

    async def create_otp(self, email: str, purpose: str = "registration") -> str:
        """Create and store a new OTP"""
        db = get_database()

        # Generate OTP
        otp_code = self.generate_otp()

        # Set expiry time
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)

        # Create OTP document
        otp_data = {
            "email": email,
            "otp_code": otp_code,
            "purpose": purpose,
            "expires_at": expires_at,
            "is_used": False,
            "created_at": datetime.utcnow()
        }

        # Store in database
        await db.otps.insert_one(otp_data)

        # Send OTP via email
        await self.send_otp_email(email, otp_code, purpose)

        return otp_code

    async def verify_otp(self, email: str, otp_code: str, purpose: str = "registration") -> bool:
        """Verify an OTP code"""
        db = get_database()

        # Find valid OTP
        otp = await db.otps.find_one({
            "email": email,
            "otp_code": otp_code,
            "purpose": purpose,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not otp:
            return False

        # Mark OTP as used
        await db.otps.update_one(
            {"_id": otp["_id"]},
            {"$set": {"is_used": True}}
        )

        return True

    async def send_otp_email(self, email: str, otp_code: str, purpose: str):
        """Send OTP via email"""
        subject_map = {
            "registration": "Verify Your StudyFriend Account",
            "login": "Login Verification Code",
            "password_reset": "Password Reset Code",
            "email_verification": "Email Verification Code"
        }

        purpose_text_map = {
            "registration": "complete your registration",
            "login": "verify your login",
            "password_reset": "reset your password",
            "email_verification": "verify your email"
        }

        subject = subject_map.get(purpose, "Verification Code")
        purpose_text = purpose_text_map.get(purpose, "verify your account")

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">{subject}</h2>
            <p>Hello,</p>
            <p>Use the following verification code to {purpose_text}:</p>
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="color: #007bff; font-size: 32px; margin: 0; letter-spacing: 5px;">{otp_code}</h1>
            </div>
            <p>This code will expire in {self.otp_expiry_minutes} minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                StudyFriend - Your Learning Companion<br>
                This is an automated message, please do not reply.
            </p>
        </div>
        """

        text_content = f"""
        {subject}

        Hello,

        Use the following verification code to {purpose_text}:

        {otp_code}

        This code will expire in {self.otp_expiry_minutes} minutes.

        If you didn't request this code, please ignore this email.

        StudyFriend - Your Learning Companion
        """

        await email_service.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def cleanup_expired_otps(self):
        """Clean up expired OTPs (can be run as a background task)"""
        db = get_database()

        await db.otps.delete_many({
            "$or": [
                {"expires_at": {"$lt": datetime.utcnow()}},
                {"is_used": True, "created_at": {"$lt": datetime.utcnow() - timedelta(hours=1)}}
            ]
        })

    async def resend_otp(self, email: str, purpose: str = "registration") -> str:
        """Resend OTP for the same purpose"""
        # Invalidate previous OTPs for this email and purpose
        db = get_database()
        await db.otps.update_many(
            {
                "email": email,
                "purpose": purpose,
                "is_used": False
            },
            {"$set": {"is_used": True}}
        )

        # Create new OTP
        return await self.create_otp(email, purpose)


# Singleton instance
otp_service = OTPService()