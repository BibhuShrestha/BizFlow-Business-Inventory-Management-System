"""
FastAPI dependency injection utilities for authentication and authorization.
"""
import logging
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
try:
    from jose import jwt, JWTError, ExpiredSignatureError
    InvalidTokenError = JWTError
except ImportError:
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError as JWTError


from core.security import decode_token, is_token_revoked

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)


def get_current_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
) -> dict:
    """Validate Bearer JWT token and check revocation."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check revocation
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_user(
    payload: Annotated[dict, Depends(get_current_token_payload)],
):
    """Fetch user instance matching authenticated token."""
    from apps.accounts.models import User

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
        )

    try:
        user = User.objects.select_related("role", "active_company").get(id=int(user_id))
    except (User.DoesNotExist, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account.",
        )

    return user


def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory checking user roles. Owner/Admin has unrestricted access."""
    normalized_allowed = [r.lower() for r in allowed_roles]

    def role_checker(user=Depends(get_current_user)):
        if user.is_admin:
            return user
        if user.role_name not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted: insufficient permissions.",
            )
        return user

    return role_checker


# Convenient role dependencies
require_admin = require_role("admin", "owner")
require_manager = require_role("admin", "owner", "manager")
require_staff = require_role("admin", "owner", "manager", "staff")
