"""JWT access/refresh token creation and verification (python-jose)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config.settings import settings
from app.core.constants import TokenType


class TokenPayload(BaseModel):
    """Decoded/validated JWT claims."""
    sub: str  # user id
    type: TokenType
    jti: str  # unique token id, used for blacklisting
    exp: int
    iat: int
    roles: list[str] = []
    remember_me: bool = False


class InvalidTokenError(Exception):
    """Raised when a token is malformed, expired, or fails signature verification."""


def _encode(claims: dict[str, Any], secret: str) -> str:
    return jwt.encode(claims, secret, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, roles: list[str]) -> tuple[str, str]:
    """Create a short-lived access token. Returns (token, jti)."""
    now = datetime.now(timezone.utc)
    jti = str(uuid4())
    claims = {
        "sub": user_id,
        "type": TokenType.ACCESS.value,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "roles": roles,
    }
    return _encode(claims, settings.SECRET_KEY), jti


def create_refresh_token(user_id: str, remember_me: bool = False) -> tuple[str, str, datetime]:
    """Create a long-lived refresh token. Returns (token, jti, expires_at)."""
    now = datetime.now(timezone.utc)
    days = settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = now + timedelta(days=days)
    jti = str(uuid4())
    claims = {
        "sub": user_id,
        "type": TokenType.REFRESH.value,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "remember_me": remember_me,
    }
    return _encode(claims, settings.REFRESH_SECRET_KEY), jti, expires_at


def create_password_reset_token(user_id: str) -> str:
    """Create a short-lived, single-purpose password-reset token."""
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,
        "type": TokenType.RESET_PASSWORD.value,
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return _encode(claims, settings.SECRET_KEY)


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    """Decode and validate a JWT, enforcing the expected token type.

    Raises InvalidTokenError on any failure (bad signature, expiry, wrong type).
    Deliberately generic error messages are surfaced to callers/clients.
    """
    secret = settings.REFRESH_SECRET_KEY if expected_type == TokenType.REFRESH else settings.SECRET_KEY
    try:
        raw = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
        payload = TokenPayload(**raw)
    except (JWTError, ValueError) as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.type != expected_type:
        raise InvalidTokenError("Unexpected token type")
    return payload
