"""Authentication & authorization related request/response schemas."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.validators.common import validate_password_strength, validate_username


class LoginRequest(BaseModel):
    """Login credentials payload."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False


class TokenResponse(BaseModel):
    """Access + refresh token pair returned on successful login/refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds until access token expiry


class RefreshTokenRequest(BaseModel):
    """Payload for exchanging a refresh token for a new token pair."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload for logout; revokes the given refresh token (and blacklists the access token)."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Payload for an authenticated user changing their own password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class RequestPasswordResetRequest(BaseModel):
    """Payload to initiate a password reset (by username or email)."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Username or email")


class ResetPasswordRequest(BaseModel):
    """Payload to complete a password reset using a one-time reset token."""
    reset_token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class CurrentUser(BaseModel):
    """Lightweight representation of the authenticated principal, attached to each request."""
    id: UUID
    username: str
    roles: list[str] = []
    permissions: list[str] = []
    is_superuser: bool = False
    is_active: bool = True
