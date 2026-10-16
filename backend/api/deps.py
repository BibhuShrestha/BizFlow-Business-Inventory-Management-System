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
    payload = None

    # 1. Attempt standard internal JWT decode
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # 2. Attempt Supabase Auth JWT decode
        from integrations.supabase_client import SupabaseAuthClient
        try:
            payload = SupabaseAuthClient.verify_jwt(token)
            payload["_source"] = "supabase"
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Check token type (for internal tokens)
    if payload.get("_source") != "supabase" and payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check revocation for internal tokens
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
    """Fetch user instance matching authenticated token (supports internal ID and Supabase UID)."""
    from apps.accounts.models import User

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
        )

    user = None

    # 1. Check by integer ID (standard internal token)
    if str(user_id).isdigit():
        user = User.objects.select_related("role", "active_company").filter(id=int(user_id)).first()

    # 2. Check by supabase_uid
    if not user:
        user = User.objects.select_related("role", "active_company").filter(supabase_uid=str(user_id)).first()

    # 3. Check by email
    if not user and payload.get("email"):
        user = User.objects.select_related("role", "active_company").filter(email=payload.get("email").lower().strip()).first()
        if user and not user.supabase_uid:
            user.supabase_uid = str(user_id)
            user.save(update_fields=["supabase_uid"])

    # 4. If Supabase token is valid but user doesn't exist locally, provision automatically
    if not user and payload.get("_source") == "supabase" and payload.get("email"):
        from integrations.supabase_client import SupabaseAuthClient
        try:
            user = SupabaseAuthClient.sync_to_django_user({
                "id": str(user_id),
                "email": payload.get("email"),
                "user_metadata": payload.get("user_metadata", {}),
            })
        except Exception:
            pass

    if not user:
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
require_staff = require_role("admin", "owner", "manager", "staff", "cashier")


def require_permission(permission: str) -> Callable:
    """Dependency factory verifying user possesses a specific granular permission."""
    def permission_checker(user=Depends(get_current_user)):
        from domain.permissions import has_permission
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted: missing '{permission}' permission.",
            )
        return user

    return permission_checker


def require_any_permission(*permissions: str) -> Callable:
    """Dependency factory verifying user possesses at least one of the specified permissions."""
    def permission_checker(user=Depends(get_current_user)):
        from domain.permissions import has_any_permission
        if not has_any_permission(user, *permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access restricted: insufficient permissions.",
            )
        return user

    return permission_checker

