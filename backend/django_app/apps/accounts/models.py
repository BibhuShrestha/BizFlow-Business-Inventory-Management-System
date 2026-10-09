"""
Accounts models: User, Role, EmailVerificationToken, PasswordResetToken, LoginHistory, RevokedToken.
"""
from datetime import datetime, timedelta, timezone as dt_timezone
import hashlib
import secrets

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class Role(models.Model):
    """System role (Admin, Manager, Staff, Customer)."""

    ROLE_ADMIN = "admin"
    ROLE_MANAGER = "manager"
    ROLE_STAFF = "staff"
    ROLE_CUSTOMER = "customer"

    name = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "roles"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    """Manager for custom User model using email as unique identifier."""

    def create_user(self, email: str, name: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, name: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model migrated from Flask User model.
    Uses email as the unique username field.
    """

    email = models.EmailField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    active_company = models.ForeignKey(
        "companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def check_password(self, raw_password: str) -> bool:
        """
        Verify password against Django hash or legacy Werkzeug hash.
        Automatically upgrades legacy Werkzeug hashes to Django PBKDF2 upon successful check.
        """
        if raw_password is None:
            return False

        # 1. Standard Django check
        try:
            from django.contrib.auth.hashers import check_password as django_check_password

            def setter(pwd):
                self.set_password(pwd)
                self.save(update_fields=["password"])

            if django_check_password(raw_password, self.password, setter):
                return True
        except ValueError:
            pass

        # 2. Legacy Werkzeug check (auto-upgrades if match)
        try:
            from werkzeug.security import check_password_hash

            if check_password_hash(self.password, raw_password):
                self.set_password(raw_password)
                self.save(update_fields=["password"])
                return True
        except Exception:
            pass

        return False

    @property
    def role_name(self) -> str:
        """Returns the lowercased role name, defaulting to customer."""
        return self.role.name.lower() if self.role else "customer"

    @property
    def is_admin(self) -> bool:
        """True if user is an owner, admin, or superuser."""
        return self.is_superuser or self.role_name in ("admin", "owner")

    @property
    def is_manager(self) -> bool:
        """True if user is manager or higher."""
        return self.is_admin or self.role_name == "manager"

    @property
    def is_staff_member(self) -> bool:
        """True if user is staff, cashier, manager, or admin."""
        return self.is_admin or self.is_manager or self.role_name in ("staff", "cashier")

    @property
    def is_customer(self) -> bool:
        """True if user is customer role."""
        return self.role_name == "customer" and not self.is_admin

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles. Admin/Owner always has full access."""
        if self.is_admin:
            return True
        normalized = [r.lower() for r in roles]
        return self.role_name in normalized

    @property
    def is_online(self) -> bool:
        """True if user recorded activity within the configured timeout window (default 15 minutes)."""
        if not self.last_activity:
            return False
        timeout_minutes = getattr(settings, "USER_ONLINE_TIMEOUT_MINUTES", 15)
        return (timezone.now() - self.last_activity).total_seconds() <= (timeout_minutes * 60)

    @property
    def online_status_label(self) -> str:
        """Online presence status label (Online vs Offline)."""
        return "Online" if self.is_online else "Offline"

    @property
    def account_status_label(self) -> str:
        """Account authorization status label (Active, Disabled, or Pending Verification)."""
        if not self.is_active:
            return "Disabled"
        if not self.email_verified:
            return "Pending Verification"
        return "Active"


class EmailVerificationToken(models.Model):
    """Token for email activation link."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "email_verification_tokens"

    def is_valid(self) -> bool:
        return not self.used and timezone.now() <= self.expires_at

    @classmethod
    def create_token(cls, user, expires_hours: int = 24):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(hours=expires_hours)
        obj = cls(user=user, token_hash=token_hash, expires_at=expires_at)
        return obj, raw_token

    @classmethod
    def verify_token(cls, raw_token: str):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        obj = cls.objects.filter(token_hash=token_hash, used=False).first()
        if obj and obj.is_valid():
            return obj
        return None

    def mark_used(self):
        self.used = True
        self.save(update_fields=["used"])


class PasswordResetToken(models.Model):
    """Token for secure password reset link."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"

    def is_valid(self) -> bool:
        return not self.used and timezone.now() <= self.expires_at

    @classmethod
    def create_token(cls, user, expires_hours: int = 2):
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(hours=expires_hours)
        obj = cls(user=user, token_hash=token_hash, expires_at=expires_at)
        return obj, raw_token

    @classmethod
    def verify_token(cls, raw_token: str):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        obj = cls.objects.filter(token_hash=token_hash, used=False).first()
        if obj and obj.is_valid():
            return obj
        return None

    def mark_used(self):
        self.used = True
        self.save(update_fields=["used"])


class LoginHistory(models.Model):
    """Record of user login attempts and sessions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_histories",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")
    method = models.CharField(max_length=64, default="email")
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "login_history"
        ordering = ["-timestamp"]


class RevokedToken(models.Model):
    """Stores revoked / blacklisted JWT IDs (jti) upon API logout."""

    jti = models.CharField(max_length=64, unique=True, db_index=True)
    token_type = models.CharField(max_length=16, default="access")  # access or refresh
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="revoked_tokens",
    )
    revoked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "revoked_tokens"
        ordering = ["-revoked_at"]

    def __str__(self) -> str:
        return f"Revoked {self.token_type} {self.jti}"
