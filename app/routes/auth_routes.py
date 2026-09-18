"""Authentication endpoints: login, logout, refresh, password management."""
# from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, oauth2_scheme
from app.core.constants import TokenType
from app.core.limiter import limiter
from app.dependencies.db import get_db_session
from app.dependencies.redis import get_redis
from app.responses.envelope import ErrorResponse, SuccessResponse as MessageResponse, SuccessResponse
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUser,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.security.jwt import decode_token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Authenticate and obtain an access/refresh token pair",
    description="Validates credentials, enforces brute-force lockout, and issues a new "
                "JWT access token and refresh token. Supports 'remember me' for extended "
                "refresh-token lifetime.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid username or password"},
        423: {"model": ErrorResponse, "description": "Account temporarily locked"},
        429: {"model": ErrorResponse, "description": "Too many login attempts"},
    },
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[TokenResponse]:
    """Login endpoint. Rate-limited to mitigate brute-force / credential-stuffing attacks."""
    service = AuthService(session, redis)
    tokens = await service.login(
        payload.username, payload.password, remember_me=payload.remember_me,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SuccessResponse(message="Login successful", data=tokens)


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Exchange a refresh token for a new access/refresh token pair",
    description="Implements refresh-token rotation: the presented refresh token is "
                "revoked and a new one is issued. Reuse of an already-rotated token "
                "revokes the entire session family (theft protection).",
    responses={401: {"model": ErrorResponse, "description": "Refresh token invalid, expired, or revoked"}},
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[TokenResponse]:
    """Rotate the refresh token and issue a fresh access token."""
    service = AuthService(session, redis)
    tokens = await service.refresh(
        payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SuccessResponse(message="Token refreshed", data=tokens)


@router.post(
    "/logout",
    response_model=SuccessResponse[MessageResponse],
    summary="Log out the current session",
    description="Blacklists the current access token (immediate invalidation) and "
                "revokes the associated refresh token.",
)
async def logout(
    payload: LogoutRequest,
    token: str | None = Depends(oauth2_scheme),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[MessageResponse]:
    """Logout endpoint — requires a valid access token plus the refresh token to revoke."""
    service = AuthService(session, redis)
    access_payload = decode_token(token, expected_type=TokenType.ACCESS)
    await service.logout(access_payload.jti, access_payload.exp, payload.refresh_token)
    return SuccessResponse(message="Logged out successfully", data=MessageResponse(message="Logged out"))


@router.get(
    "/me",
    response_model=SuccessResponse[CurrentUser],
    summary="Get the currently authenticated user",
    description="Returns identity, roles, and effective permissions for the caller's access token.",
)
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> SuccessResponse[CurrentUser]:
    """Return the resolved current-user principal."""
    return SuccessResponse(data=current_user)


@router.post(
    "/change-password",
    response_model=SuccessResponse[MessageResponse],
    summary="Change the current user's password",
    description="Requires the current password for verification. Revokes all existing "
                "sessions (refresh tokens) upon success, forcing re-login everywhere else.",
    responses={401: {"model": ErrorResponse, "description": "Current password is incorrect"}},
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[MessageResponse]:
    """Change password for the authenticated user."""
    service = AuthService(session, redis)
    await service.change_password(current_user.id, payload.current_password, payload.new_password)
    return SuccessResponse(message="Password changed successfully", data=MessageResponse(message="Password changed"))


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[MessageResponse],
    summary="Request a password reset",
    description="Always returns a generic success message regardless of whether the "
                "identifier matches an account, to prevent user enumeration. The reset "
                "token itself is delivered out-of-band (email/SMS), never in this response.",
)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    payload: RequestPasswordResetRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[MessageResponse]:
    """Initiate the password-reset flow. TODO: wire up email/SMS dispatch via BackgroundTasks."""
    service = AuthService(session, redis)
    await service.request_password_reset(payload.identifier)
    return SuccessResponse(
        message="If the account exists, a reset link has been sent",
        data=MessageResponse(message="Reset request processed"),
    )


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[MessageResponse],
    summary="Complete a password reset using a reset token",
    responses={401: {"model": ErrorResponse, "description": "Reset token invalid or expired"}},
)
async def confirm_password_reset(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SuccessResponse[MessageResponse]:
    """Finalize password reset given a valid reset token."""
    service = AuthService(session, redis)
    await service.reset_password(payload.reset_token, payload.new_password)
    return SuccessResponse(message="Password reset successfully", data=MessageResponse(message="Password reset"))
