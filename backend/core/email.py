"""
Email sending service for verification and password reset links.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:
    """Sends system emails (verification, reset, notifications)."""

    @staticmethod
    def send_verification_otp(user, otp: str, request=None) -> bool:
        """Send 6-digit OTP verification email to user and log it for developer convenience."""
        subject = f"{otp} is your BizFlow verification code"
        message = (
            f"Hello {user.name},\n\n"
            f"Thank you for registering with BizFlow.\n\n"
            f"Your 6-digit verification code is:\n\n"
            f"    {otp}\n\n"
            f"Enter this code on the verification screen to activate your account and access your dashboard.\n"
            f"This code will expire in 15 minutes.\n\n"
            f"If you did not request this code, you can safely ignore this email.\n\n"
            f"BizFlow Team"
        )
        logger.info("==================================================")
        logger.info(">>> VERIFICATION OTP for %s: %s <<<", user.email, otp)
        logger.info("==================================================")
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Verification OTP email successfully sent via SMTP to %s", user.email)
            return True
        except Exception as exc:
            logger.error("Failed to send verification OTP email to %s: %s", user.email, exc, exc_info=True)
            return False


    @staticmethod
    def send_verification_email(user, token: str, request=None) -> bool:
        """Send account verification email with activation link."""
        host = request.get_host() if request else "localhost:8000"
        scheme = request.scheme if request else "http"
        verify_url = f"{scheme}://{host}/auth/verify-email/{token}/"

        subject = "Verify your BizFlow account"
        message = (
            f"Hello {user.name},\n\n"
            f"Thank you for registering. Please click the link below to verify your email address:\n\n"
            f"{verify_url}\n\n"
            f"This link will expire in 24 hours.\n\n"
            f"BizFlow Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            logger.info("Verification email sent to %s", user.email)
            return True
        except Exception as exc:
            logger.warning("Failed to send verification email to %s: %s", user.email, exc)
            return False

    @staticmethod
    def send_password_reset_email(user, token: str, request=None) -> bool:
        """Send password reset email with reset link."""
        host = request.get_host() if request else "localhost:8000"
        scheme = request.scheme if request else "http"
        reset_url = f"{scheme}://{host}/auth/reset-password/{token}/"

        subject = "Reset your BizFlow password"
        message = (
            f"Hello {user.name},\n\n"
            f"We received a request to reset your password. Click the link below to set a new password:\n\n"
            f"{reset_url}\n\n"
            f"This link will expire in 2 hours.\n\n"
            f"If you did not request a password reset, you can safely ignore this email.\n\n"
            f"BizFlow Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            logger.info("Password reset email sent to %s", user.email)
            return True
        except Exception as exc:
            logger.warning("Failed to send password reset email to %s: %s", user.email, exc)
            return False
