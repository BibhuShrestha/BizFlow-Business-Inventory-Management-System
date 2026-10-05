"""
Shared security utilities.

Provides JWT creation, verification, and revocation used by the FastAPI authentication layer.
Django session auth uses Django's own mechanisms (django.contrib.auth).

This module is framework-agnostic - it does not import Django or FastAPI directly,
except when revoking/checking tokens in database.
"""
from datetime import UTC, datetime, timedelta
from typing import Any
import uuid

try:
    from jose import jwt, JWTError, ExpiredSignatureError
    InvalidTokenError = JWTError
except ImportError:
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError as JWTError


from core.config import settings


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload to encode (typically sub, email, role, company_id).
        expires_delta: Token lifetime. Defaults to JWT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    payload = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    payload["iat"] = now
    payload["type"] = "access"
    payload.setdefault("jti", uuid.uuid4().hex)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token with a longer expiry."""
    payload = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload["exp"] = expire
    payload["iat"] = now
    payload["type"] = "refresh"
    payload.setdefault("jti", uuid.uuid4().hex)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Raises:
        ExpiredSignatureError: If the token has expired.
        InvalidTokenError:    If the token is invalid.

    Returns:
        Decoded payload dict.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def is_token_revoked(jti: str) -> bool:
    """Check if a token has been revoked / blacklisted."""
    try:
        from apps.accounts.models import RevokedToken
        return RevokedToken.objects.filter(jti=jti).exists()
    except Exception:
        return False


def revoke_token(jti: str, token_type: str = "access", user=None, expires_at: datetime | None = None) -> bool:
    """Revoke a token by jti."""
    try:
        from apps.accounts.models import RevokedToken
        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        RevokedToken.objects.get_or_create(
            jti=jti,
            defaults={
                "token_type": token_type,
                "user": user,
                "expires_at": expires_at,
            },
        )
        return True
    except Exception:
        return False
