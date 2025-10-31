import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


class EmailService:
    """Email service for sending notifications and OTPs"""

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER or "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL or self.smtp_username

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[list] = None,
        bcc: Optional[list] = None
    ) -> bool:
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # Attach parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)

            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()

            return True

        except Exception as e:
            print(f"Email sending failed: {e}")
            # In production, you might want to log this or use a queue
            return False

    async def send_welcome_email(self, to_email: str, user_name: str):
        """Send welcome email to new users"""
        subject = "Welcome to StudyFriend!"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Welcome to StudyFriend, {user_name}!</h2>
            <p>Thank you for joining StudyFriend, your comprehensive learning platform.</p>
            <p>Here's what you can do:</p>
            <ul>
                <li>Upload and access study materials</li>
                <li>Ask questions to our AI assistant</li>
                <li>Take mock tests and assignments</li>
                <li>Book sessions with faculty members</li>
                <li>Track your learning progress</li>
            </ul>
            <p>Get started by exploring our platform!</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Start Learning</a>
            </div>
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                StudyFriend - Your Learning Companion<br>
                Need help? Contact our support team.
            </p>
        </div>
        """

        text_content = f"""
        Welcome to StudyFriend, {user_name}!

        Thank you for joining StudyFriend, your comprehensive learning platform.

        Here's what you can do:
        - Upload and access study materials
        - Ask questions to our AI assistant
        - Take mock tests and assignments
        - Book sessions with faculty members
        - Track your learning progress

        Get started by exploring our platform!

        StudyFriend - Your Learning Companion
        Need help? Contact our support team.
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset_email(self, to_email: str, reset_token: str):
        """Send password reset email"""
        subject = "Password Reset Request"

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Password Reset Request</h2>
            <p>You requested a password reset for your StudyFriend account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Reset Password</a>
            </div>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                StudyFriend - Your Learning Companion<br>
                This is an automated message, please do not reply.
            </p>
        </div>
        """

        text_content = f"""
        Password Reset Request

        You requested a password reset for your StudyFriend account.

        Reset your password here: {reset_link}

        This link will expire in 1 hour.

        If you didn't request this reset, please ignore this email.

        StudyFriend - Your Learning Companion
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_faculty_verification_email(self, to_email: str, faculty_name: str):
        """Send faculty verification notification"""
        subject = "Faculty Account Verified"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Congratulations, {faculty_name}!</h2>
            <p>Your faculty account has been verified by our administrators.</p>
            <p>You can now:</p>
            <ul>
                <li>Create and manage courses</li>
                <li>Upload educational materials</li>
                <li>Create assignments and tests</li>
                <li>Conduct live sessions with students</li>
                <li>Answer student queries</li>
            </ul>
            <p>Welcome to the StudyFriend faculty community!</p>
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                StudyFriend - Your Learning Companion<br>
                This is an automated message, please do not reply.
            </p>
        </div>
        """

        text_content = f"""
        Congratulations, {faculty_name}!

        Your faculty account has been verified by our administrators.

        You can now:
        - Create and manage courses
        - Upload educational materials
        - Create assignments and tests
        - Conduct live sessions with students
        - Answer student queries

        Welcome to the StudyFriend faculty community!

        StudyFriend - Your Learning Companion
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()