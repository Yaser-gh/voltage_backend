"""FastAPI dependencies for authentication: extracting and validating the current user."""
from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TokenType
from app.dependencies.db import get_db_session
from app.dependencies.redis import get_redis
from app.exceptions.custom import (
    AccountLockedException,
    TokenExpiredException,
    TokenInvalidException,
    TokenRevokedException,
    UnauthorizedException,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUser
from app.security.blacklist import TokenBlacklist
from app.security.jwt import InvalidTokenError, decode_token

# tokenUrl is documentation-only here since login is a JSON endpoint, not form-encoded.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> CurrentUser:
    """Resolve and validate the current authenticated user from the Authorization header.

    Pipeline: extract bearer token -> decode/verify JWT -> check blacklist ->
    load user + roles/permissions from DB -> ensure account is active/unlocked.
    """
    if not token:
        raise UnauthorizedException("Missing authentication credentials")

    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise TokenInvalidException(str(exc)) from exc

    blacklist = TokenBlacklist(redis)
    if await blacklist.is_blacklisted(payload.jti):
        raise TokenRevokedException()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(payload.sub)  # TODO: repository method not yet implemented
    if user is None:
        raise UnauthorizedException("User account no longer exists")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive")
    if getattr(user, "locked_until", None):
        raise AccountLockedException()

    request.state.user_id = str(user.u_id)

    permissions: list[str] = []
    for role in getattr(user, "roles", []):
        for perm in getattr(role, "permissions", []):
            permissions.append(perm.code)

    return CurrentUser(
        id=user.u_id,
        username=user.username,
        roles=[r.name for r in getattr(user, "roles", [])],
        permissions=list(set(permissions)),
        is_superuser=user.is_superuser,
        is_active=user.is_active,
    )


async def get_current_active_superuser(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that additionally requires the current user to be a superuser (admin)."""
    if not current_user.is_superuser:
        raise UnauthorizedException("Superuser privileges required")
    return current_user


async def get_optional_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> CurrentUser | None:
    """Like get_current_user, but returns None instead of raising when no/invalid token is present.

    Useful for endpoints with optional personalization but no hard auth requirement.
    """
    if not token:
        return None
    try:
        return await get_current_user(request, token, session, redis)
    except Exception:
        return None
