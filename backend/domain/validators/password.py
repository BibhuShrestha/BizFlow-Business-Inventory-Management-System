"""
Password strength validator.

Pure-Python; no framework dependency. Used by:
  - Django: apps/accounts/forms.py (custom validator)
  - FastAPI: api/schemas/auth.py (pydantic validator)

Migrated from: app/auth/forms.py::validate_password_rules() in the Flask project.
"""
import re
from dataclasses import dataclass, field


@dataclass
class PasswordStrengthResult:
    """Result of a password strength check."""

    valid: bool
    errors: list[str] = field(default_factory=list)

    @property
    def error_message(self) -> str:
        """Human-readable combined error message."""
        if not self.errors:
            return ""
        return "Password must " + ", ".join(self.errors) + "."


def check_password_strength(password: str) -> PasswordStrengthResult:
    """
    Validate password against business strength requirements.

    Rules (identical to the Flask project):
      - At least 8 characters
      - At least one uppercase letter (A-Z)
      - At least one lowercase letter (a-z)
      - At least one digit (0-9)
      - At least one special character (!@#$%^&*...)

    Args:
        password: Plain-text password to validate.

    Returns:
        PasswordStrengthResult with valid=True or a list of failure reasons.
    """
    errors: list[str] = []

    if len(password) < 8:
        errors.append("be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        errors.append("include at least one uppercase letter (A-Z)")
    if not re.search(r"[a-z]", password):
        errors.append("include at least one lowercase letter (a-z)")
    if not re.search(r"\d", password):
        errors.append("include at least one number (0-9)")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/~`]', password):
        errors.append("include at least one special character (!@#$%^&*)")

    return PasswordStrengthResult(valid=len(errors) == 0, errors=errors)


def validate_password(password: str) -> str:
    """
    Validate and return the password if valid, or raise ValueError.

    Convenience wrapper for use as a Pydantic field validator:

        @field_validator("password")
        @classmethod
        def password_strength(cls, v: str) -> str:
            return validate_password(v)
    """
    result = check_password_strength(password)
    if not result.valid:
        raise ValueError(result.error_message)
    return password
