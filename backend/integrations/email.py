"""
Email Integration Service.

Wraps transactional email delivery for password resets, email verification,
and invoice PDFs.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:
    """Handles sending transactional emails."""

    @staticmethod
    def send_verification_email(to_email: str, verification_link: str) -> bool:
        """Send account activation email with verification link."""
        subject = "Verify your BizFlow account"
        message = (
            f"Welcome to BizFlow!\n\n"
            f"Please verify your email address by clicking the link below:\n"
            f"{verification_link}\n\n"
            f"This link will expire in 60 minutes.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            logger.info("Verification email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Failed to send verification email to %s: %s", to_email, exc)
            return False

    @staticmethod
    def send_password_reset_email(to_email: str, reset_link: str) -> bool:
        """Send password reset email with secure token link."""
        subject = "Reset your BizFlow password"
        message = (
            f"A password reset was requested for your BizFlow account.\n\n"
            f"Click the link below to set a new password:\n"
            f"{reset_link}\n\n"
            f"This link will expire in 30 minutes. If you did not request this, please ignore.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            logger.info("Password reset email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Failed to send password reset email to %s: %s", to_email, exc)
            return False