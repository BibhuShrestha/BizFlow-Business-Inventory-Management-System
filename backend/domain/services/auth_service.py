"""
AuthService — Authentication business logic shared between Django and FastAPI.

This service does NOT import from Django views or FastAPI routers.
It only uses Django models and the ORM.
"""
import hashlib
import logging
from typing import Any

from django.db import transaction, IntegrityError
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
        from integrations.supabase_client import SupabaseAuthClient

        # 1. Attempt Supabase Auth if configured
        if SupabaseAuthClient.is_configured():
            try:
                session_data = SupabaseAuthClient.sign_in_with_password(email, password)
                supabase_user = session_data.get("user") or {}
                user = SupabaseAuthClient.sync_to_django_user(supabase_user)
                user._supabase_session = session_data
                logger.info("Supabase authentication successful for %s (id=%s)", email, user.id)
                return user
            except AuthenticationError as exc:
                logger.info("Supabase Auth rejected %s (%s). Checking local database fallback...", email, exc)

        # 2. Local database authentication fallback
        try:
            user = User.objects.select_related("role", "active_company").get(email__iexact=email.strip())
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

        if User.objects.filter(email__iexact=email).exists():
            raise DuplicateEmailError(email)

        try:
            validate_password(password)
        except ValueError as exc:
            raise ValidationError(str(exc))

        # Assign default 'staff' role
        staff_role, _ = Role.objects.get_or_create(
            name="staff", defaults={"description": "Default staff role"}
        )

        from integrations.supabase_client import SupabaseAuthClient
        supabase_uid = None
        if SupabaseAuthClient.is_configured():
            try:
                supa_res = SupabaseAuthClient.sign_up(email=email, password=password, name=name)
                supabase_uid = (supa_res.get("user") or {}).get("id")
            except Exception as exc:
                logger.warning("Supabase Auth sign-up error for %s: %s", email, exc)

        user = User(
            name=name.strip(),
            email=email,
            supabase_uid=supabase_uid,
            role=staff_role,
            is_active=False,
            email_verified=False,
        )
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            logger.warning("IntegrityError on user registration for email %s (likely duplicate concurrent insert)", email)
            raise DuplicateEmailError(email)

        # Create 6-digit email verification OTP
        token_obj, raw_token = EmailVerificationToken.create_otp(user)

        logger.info("New user registered: %s (id=%s), verification OTP generated", email, user.id)
        return user, raw_token

    @staticmethod
    @transaction.atomic
    def verify_otp(email_or_user, otp: str):
        """
        Verify a user's 6-digit OTP code and activate their account.

        Args:
            email_or_user: Email string or User instance.
            otp: 6-digit verification code entered by the user.

        Returns:
            Activated User instance.

        Raises:
            TokenInvalidError: If OTP is invalid or expired.
        """
        from apps.accounts.models import User, EmailVerificationToken, Role
        from apps.companies.models import Company

        if isinstance(email_or_user, str):
            user = User.objects.filter(email__iexact=email_or_user.strip()).first()
        else:
            user = email_or_user

        if not user:
            raise TokenInvalidError("User account not found.")

        token_obj = EmailVerificationToken.verify_otp(user, otp)
        if not token_obj:
            raise TokenInvalidError("Invalid or expired 6-digit verification code. Please request a new code.")

        token_obj.mark_used()
        user.email_verified = True
        user.is_active = True

        # Ensure active company and role are configured upon first activation
        first_co = Company.objects.first()
        if first_co and not user.active_company:
            user.active_company = first_co
        elif not user.active_company:
            first_co = Company.objects.create(
                company_name=f"{user.name}'s Business",
                company_phone="",
                vat_pan_number="",
                address="",
            )
            user.active_company = first_co

        admin_role = Role.objects.filter(name="admin").first()
        if admin_role and (not user.role or user.role.name == "staff"):
            user.role = admin_role
            user.is_staff = True

        user.save()
        logger.info("Email verified via OTP for user %s (id=%s)", user.email, user.id)
        return user

    @staticmethod
    def resend_otp(email: str):
        """
        Generate and return a new 6-digit OTP for an unverified user.

        Args:
            email: User's email address.

        Returns:
            Tuple of (User, raw_otp_string).

        Raises:
            ValidationError: If user is not found or already verified.
        """
        from apps.accounts.models import User, EmailVerificationToken

        user = User.objects.filter(email__iexact=email.strip()).first()
        if not user:
            raise ValidationError("No registered account found with that email address.")
        if user.email_verified and user.is_active:
            raise ValidationError("This account is already verified. Please sign in.")

        token_obj, raw_otp = EmailVerificationToken.create_otp(user)
        logger.info("Resent new verification OTP for %s", user.email)
        return user, raw_otp

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
            # Check if token was an OTP
            token_obj = EmailVerificationToken.objects.filter(
                token_hash=hashlib.sha256(token.strip().encode()).hexdigest(),
                used=False
            ).first()
            if not token_obj or not token_obj.is_valid():
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

    @staticmethod
    @transaction.atomic
    def login_or_register_via_google(user_info: dict[str, Any]):
        """
        Authenticate or provision a user from verified Google OAuth2 userinfo.

        Args:
            user_info: Dictionary containing 'sub', 'email', 'email_verified', 'name', 'picture'.

        Returns:
            Tuple of (User, created: bool)

        Raises:
            AuthenticationError: If email is missing, unverified by Google, or account is disabled.
        """
        from apps.accounts.models import User, Role
        from apps.companies.models import Company

        email = str(user_info.get("email", "")).lower().strip()
        if not email:
            raise AuthenticationError("Google profile did not provide a valid email address.")

        email_verified = bool(user_info.get("email_verified", False))
        if not email_verified:
            raise AuthenticationError("Google account email is not verified.")

        sub = str(user_info.get("sub", "")).strip() or None
        name = str(user_info.get("name", "")).strip() or email.split("@")[0].title()

        user = None
        if sub:
            user = User.objects.select_related("role", "active_company").filter(google_id=sub).first()

        if user is None:
            user = User.objects.select_related("role", "active_company").filter(email=email).first()

        created = False
        if user is None:
            staff_role, _ = Role.objects.get_or_create(
                name="staff", defaults={"description": "Default staff role"}
            )
            user = User(
                name=name,
                email=email,
                role=staff_role,
                is_active=True,
                email_verified=True,
                google_id=sub,
            )
            user.set_unusable_password()
            default_company = Company.objects.first()
            if default_company:
                user.active_company = default_company
            user.save()
            created = True
            logger.info("New user provisioned via Google OAuth: %s (id=%s)", email, user.id)
        else:
            if not user.is_active:
                logger.info("Google OAuth login rejected for inactive account: %s", email)
                raise AuthenticationError("Your account is inactive. Please contact an administrator.")

            dirty_fields = []
            if sub and not user.google_id:
                user.google_id = sub
                dirty_fields.append("google_id")
            if not user.email_verified:
                user.email_verified = True
                dirty_fields.append("email_verified")
            if not user.name and name:
                user.name = name
                dirty_fields.append("name")

            if dirty_fields:
                user.save(update_fields=dirty_fields)

            logger.info("User authenticated via Google OAuth: %s (id=%s)", email, user.id)

        return user, created

