"""
Authentication API endpoints (/api/v1/auth).
Supports Web, Mobile, and Desktop clients.
"""
from datetime import UTC, datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
try:
    from jose import jwt, JWTError, ExpiredSignatureError
    InvalidTokenError = JWTError
except ImportError:
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError as JWTError


from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_revoked,
    revoke_token,
)
from domain.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    TokenInvalidError,
    ValidationError,
)
from domain.services.auth_service import AuthService
from api.deps import get_current_user, security_bearer
from api.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone or "",
        role=user.role_name,
        company_id=user.active_company_id,
        is_active=user.is_active,
        email_verified=user.email_verified,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticate with email and password to receive access & refresh tokens."""
    try:
        user = AuthService.authenticate(email=req.email, password=req.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role_name,
        "company_id": user.active_company_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_out(user),
    )


@router.post("/refresh", response_model=dict)
def refresh_token_endpoint(req: RefreshTokenRequest):
    """Use a valid refresh token to obtain a new access token."""
    try:
        payload = decode_token(req.refresh_token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token.",
        )

    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )

    from apps.accounts.models import User

    user_id = payload.get("sub")
    try:
        user = User.objects.select_related("role").get(id=int(user_id))
    except (User.DoesNotExist, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
        )

    new_access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role_name,
            "company_id": user.active_company_id,
        }
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", response_model=MessageResponse)
def logout_endpoint(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    refresh_data: RefreshTokenRequest | None = None,
):
    """Revoke access token (and optional refresh token) upon logout."""
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
            jti = payload.get("jti")
            exp = payload.get("exp")
            exp_dt = datetime.fromtimestamp(exp, tz=UTC) if exp else None
            if jti:
                revoke_token(jti=jti, token_type="access", expires_at=exp_dt)
        except Exception:
            pass

    if refresh_data and refresh_data.refresh_token:
        try:
            r_payload = decode_token(refresh_data.refresh_token)
            r_jti = r_payload.get("jti")
            r_exp = r_payload.get("exp")
            r_exp_dt = datetime.fromtimestamp(r_exp, tz=UTC) if r_exp else None
            if r_jti:
                revoke_token(jti=r_jti, token_type="refresh", expires_at=r_exp_dt)
        except Exception:
            pass

    return MessageResponse(detail="Successfully logged out.")


@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)):
    """Return profile and permissions for currently authenticated user."""
    return _user_to_out(user)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """Register a new user account."""
    try:
        user, token = AuthService.register(
            name=req.name,
            email=req.email,
            password=req.password,
        )
        from core.email import EmailService
        EmailService.send_verification_email(user, token)
        return MessageResponse(
            detail="Account created successfully. Please verify your email."
        )
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(req: ForgotPasswordRequest):
    """Request a password reset link."""
    result = AuthService.request_password_reset(req.email)
    if result:
        user, token = result
        from core.email import EmailService
        EmailService.send_password_reset_email(user, token)
    return MessageResponse(
        detail="If that email is registered, you will receive a password reset link shortly."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: ResetPasswordRequest):
    """Reset password using token received via email."""
    try:
        AuthService.reset_password(token=req.token, new_password=req.new_password)
        return MessageResponse(detail="Password reset successfully. You can now log in.")
    except TokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/change-password", response_model=MessageResponse)
def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    """Change current logged-in user password."""
    try:
        AuthService.change_password(
            user=user,
            current_password=req.current_password,
            new_password=req.new_password,
        )
        return MessageResponse(detail="Password changed successfully.")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
