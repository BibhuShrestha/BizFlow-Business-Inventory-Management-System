"""
Pydantic schemas for authentication and authorization.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str = ""
    role: str
    company_id: Optional[int] = None
    is_active: bool
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    detail: str


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None
