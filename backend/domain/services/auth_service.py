"""
AuthService — Authentication business logic shared between Django and FastAPI.

This service does NOT import from Django views or FastAPI routers.
It only uses Django models and the ORM.
"""
import logging

from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password

from domain.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    TokenInvalidError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Handles authentication, registration, and password management."""

    @staticmethod
    def authenticate(email: str, password: str):
        """
        Authenticate a user by email and password.

        Args:
            email: User's email address.
            password: Raw plaintext password.

        Returns:
            User instance if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid or account is inactive.
        """
        from apps.accounts.models import User

        try:
            user = User.objects.select_related("role").get(email=email.lower().strip())
        except User.DoesNotExist:
            logger.info("Login failed: email %s not found", email)
            raise AuthenticationError("Invalid email or password.")

        if not user.check_password(password):
            logger.info("Login failed: wrong password for %s", email)
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            logger.info("Login failed: inactive account %s", email)
            raise AuthenticationError("Your account is inactive. Please contact an administrator.")

        if not user.email_verified:
            raise AuthenticationError(
                "Your email address has not been verified. Please check your inbox."
            )

        logger.info("Login successful: user %s (id=%s)", email, user.id)
        return user

    @staticmethod
    @transaction.atomic
    def register(name: str, email: str, password: str):
        """
        Register a new user account.

        The account is created as inactive with email_verified=False.
        An email verification token is created and must be emailed separately.

        Args:
            name: Full display name.
            email: Email address (lowercased).
            password: Raw plaintext password.

        Returns:
            Tuple of (User, raw_token_string)

        Raises:
            DuplicateEmailError: If email is already registered.
            ValidationError: If password does not meet requirements.
        """
        from apps.accounts.models import User, Role, EmailVerificationToken
        from domain.validators.password import validate_password

        email = email.lower().strip()

        if User.objects.filter(email=email).exists():
            raise DuplicateEmailError(f"An account with email '{email}' already exists.")

        try:
            validate_password(password)
        except ValueError as exc:
            raise ValidationError(str(exc))

        # Assign default 'staff' role
        staff_role, _ = Role.objects.get_or_create(
            name="staff", defaults={"description": "Default staff role"}
        )

        user = User(
            name=name.strip(),
            email=email,
            role=staff_role,
            is_active=False,
            email_verified=False,
        )
        user.set_password(password)
        user.save()

        # Create email verification token
        token_obj, raw_token = EmailVerificationToken.create_token(user)
        token_obj.save()

        logger.info("New user registered: %s (id=%s)", email, user.id)
        return user, raw_token

    @staticmethod
    @transaction.atomic
    def verify_email(token: str):
        """
        Verify a user's email using the given token.

        Args:
            token: Raw token string from the verification email.

        Returns:
            User instance with email_verified=True and is_active=True.

        Raises:
            TokenInvalidError: If token is invalid, expired, or already used.
        """
        from apps.accounts.models import EmailVerificationToken

        token_obj = EmailVerificationToken.verify_token(token)
        if not token_obj:
            raise TokenInvalidError("Verification link is invalid or has expired.")

        user = token_obj.user
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        token_obj.mark_used()

        logger.info("Email verified for user %s (id=%s)", user.email, user.id)
        return user

    @staticmethod
    @transaction.atomic
    def request_password_reset(email: str):
        """
        Initiate a password reset for the given email.

        Returns None silently if email is not registered (prevents user enumeration).

        Args:
            email: Email address to reset password for.

        Returns:
            Tuple of (User, raw_token_string) or None if not found.
        """
        from apps.accounts.models import User, PasswordResetToken

        try:
            user = User.objects.get(email=email.lower().strip())
        except User.DoesNotExist:
            logger.info("Password reset requested for unknown email: %s", email)
            return None

        token_obj, raw_token = PasswordResetToken.create_token(user)
        token_obj.save()

        logger.info("Password reset requested for user %s (id=%s)", email, user.id)
        return user, raw_token

    @staticmethod
    @transaction.atomic
    def reset_password(token: str, new_password: str):
        """
        Reset a user's password using the given token.

        Args:
            token: Raw token from the reset email.
            new_password: New plaintext password.

        Returns:
            User instance.

        Raises:
            TokenInvalidError: If token is invalid or expired.
            ValidationError: If new password does not meet requirements.
        """
        from apps.accounts.models import PasswordResetToken
        from domain.validators.password import validate_password

        token_obj = PasswordResetToken.verify_token(token)
        if not token_obj:
            raise TokenInvalidError("Reset link is invalid or has expired.")

        try:
            validate_password(new_password)
        except ValueError as exc:
            raise ValidationError(str(exc))

        user = token_obj.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        token_obj.mark_used()

        logger.info("Password reset completed for user %s (id=%s)", user.email, user.id)
        return user

    @staticmethod
    def change_password(user, current_password: str, new_password: str):
        """
        Change a logged-in user's password after verifying current password.

        Args:
            user: The authenticated User instance.
            current_password: Current password to verify.
            new_password: New password to set.

        Raises:
            AuthenticationError: If current password is wrong.
            ValidationError: If new password does not meet requirements.
        """
        from domain.validators.password import validate_password

        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect.")

        try:
            validate_password(new_password)
        except ValueError as exc:
            raise ValidationError(str(exc))

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password changed for user %s (id=%s)", user.email, user.id)
        return user
