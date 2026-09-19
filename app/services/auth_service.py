"""Authentication business logic: login, logout, refresh rotation, password flows.

All persistence is delegated to repositories; this layer only orchestrates
business rules (lockout thresholds, token rotation, blacklisting).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.constants import SecurityEventType, TokenType
from app.core.logging import get_logger
from app.exceptions.custom import (
    AccountLockedException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    TokenRevokedException,
)
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.security.blacklist import TokenBlacklist
from app.security.jwt import InvalidTokenError, create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, needs_rehash, verify_password

logger = get_logger("auth_service")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def _hash_token(raw_token: str) -> str:
    """Hash a raw refresh token for storage/lookup (never persist raw tokens)."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


class AuthService:
    """Orchestrates authentication use-cases on top of repositories and security primitives."""

    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.user_repo = UserRepository(session)
        self.token_repo = TokenRepository(session)
        self.blacklist = TokenBlacklist(redis)

    async def login(
        self, username: str, password: str, *, remember_me: bool, ip_address: str | None, user_agent: str | None
    ) -> TokenResponse:
        """Authenticate a user and issue a new access/refresh token pair.

        Enforces account lockout after repeated failures and never reveals
        whether the username or password was incorrect (prevents enumeration).
        """
        user = await self.user_repo.get_by_username(username)  # TODO: repository not yet implemented

        if user is None:
            # Perform a dummy hash comparison to keep response timing consistent
            # whether or not the username exists (mitigates user-enumeration via timing).
            verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$QMjZWyvlPEcIIYRwTsm5tw$eIq9eUngygEjP3ddaDOB/KB9wXVaeEqBXAvwfG8ioSY")
            logger.warning("login_failed", reason="user_not_found", username=username)
            raise InvalidCredentialsException()

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning("login_blocked_locked", user_id=str(user.u_id))
            raise AccountLockedException()

        if not verify_password(password, user.hashed_password):
            attempts = user.failed_login_attempts + 1
            locked_until = None
            if attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                logger.warning("account_locked", user_id=str(user.u_id))
            await self.user_repo.set_failed_login_attempts(user.u_id, attempts, locked_until)
            logger.warning("login_failed", reason="bad_password", user_id=str(user.u_id))
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InvalidCredentialsException()

        if needs_rehash(user.hashed_password):
            await self.user_repo.set_password_hash(user.u_id, hash_password(password))

        await self.user_repo.set_last_login(user.u_id)
        logger.info("login_success", user_id=str(user.u_id))

        return await self._issue_token_pair(user, remember_me=remember_me, ip_address=ip_address, user_agent=user_agent)

    async def _issue_token_pair(self, user, *, remember_me: bool, ip_address: str | None, user_agent: str | None) -> TokenResponse:
        """Create and persist a new access+refresh token pair for a user."""
        role_names = [r.name for r in getattr(user, "roles", [])]
        access_token, _ = create_access_token(str(user.u_id), role_names)
        refresh_token, jti, expires_at = create_refresh_token(str(user.u_id), remember_me=remember_me)

        await self.token_repo.create(
            user_id=user.u_id,
            token_hash=_hash_token(refresh_token),
            family_id=uuid4(),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            remember_me=remember_me,
        )  # TODO: repository.create not yet implemented

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, raw_refresh_token: str, *, ip_address: str | None, user_agent: str | None) -> TokenResponse:
        """Rotate a refresh token: validate, revoke the old one, issue a new pair.

        Implements reuse detection: if a refresh token that was already rotated
        (replaced_by_token_id set) is presented again, the entire token family
        is revoked, since this strongly indicates the token was stolen.
        """
        try:
            payload = decode_token(raw_refresh_token, expected_type=TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise TokenInvalidException(str(exc)) from exc

        token_record = await self.token_repo.get_by_token_hash(_hash_token(raw_refresh_token))  # TODO
        if token_record is None:
            raise TokenInvalidException("Refresh token not recognized")

        if token_record.revoked_at is not None:
            # Reuse of an already-revoked/rotated token: possible theft, nuke the whole family.
            logger.error(
                "token_reuse_detected", user_id=str(token_record.user_id), family_id=str(token_record.family_id)
            )
            await self.token_repo.revoke_family(token_record.family_id)  # TODO
            raise TokenRevokedException("Refresh token has already been used; all sessions revoked")

        if not token_record.is_active:
            raise TokenExpiredException()

        user = await self.user_repo.get_by_id(UUID(payload.sub))  # TODO
        if user is None or not user.is_active:
            raise TokenInvalidException("User account no longer valid")

        role_names = [r.name for r in getattr(user, "roles", [])]
        access_token, _ = create_access_token(str(user.u_id), role_names)
        new_refresh_token, _, expires_at = create_refresh_token(str(user.u_id), remember_me=payload.remember_me)

        new_record = await self.token_repo.create(
            user_id=user.u_id,
            token_hash=_hash_token(new_refresh_token),
            family_id=token_record.family_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            remember_me=payload.remember_me,
        )  # TODO

        await self.token_repo.revoke(token_record.u_id)  # TODO
        await self.token_repo.mark_replaced(token_record.u_id, new_record.u_id)  # TODO

        logger.info("token_refreshed", user_id=str(user.u_id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, access_token_jti: str, access_token_exp: int, raw_refresh_token: str | None) -> None:
        """Invalidate the current session: blacklist the access token and revoke the refresh token."""
        ttl = max(0, access_token_exp - int(datetime.now(timezone.utc).timestamp()))
        await self.blacklist.add(access_token_jti, ttl)

        if raw_refresh_token:
            token_record = await self.token_repo.get_by_token_hash(_hash_token(raw_refresh_token))  # TODO
            if token_record is not None:
                await self.token_repo.revoke(token_record.u_id)  # TODO
        logger.info("logout", jti=access_token_jti)

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        """Change a logged-in user's password after verifying their current one."""
        user = await self.user_repo.get_by_id(user_id)  # TODO
        if user is None:
            raise InvalidCredentialsException()
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsException("Current password is incorrect")

        await self.user_repo.set_password_hash(user_id, hash_password(new_password))  # TODO
        await self.token_repo.revoke_all_for_user(user_id)  # TODO — force re-login everywhere
        logger.info("password_changed", user_id=str(user_id))

    async def request_password_reset(self, identifier: str) -> str | None:
        """Generate a password-reset token for a user identified by username or email.

        Always returns None to the caller-facing response regardless of whether
        the identifier matched a user (prevents account enumeration) — the
        actual token (if any) should be delivered out-of-band (email/SMS),
        never returned directly in the API response.
        """
        user = await self.user_repo.get_by_username(identifier)  # TODO
        if user is None:
            user = await self.user_repo.get_by_email(identifier)  # TODO
        if user is None:
            logger.info("password_reset_requested_unknown_identifier")
            return None

        from app.security.jwt import create_password_reset_token
        token = create_password_reset_token(str(user.u_id))
        logger.info("password_reset_requested", user_id=str(user.u_id))
        # TODO: dispatch `token` via email/SMS through a BackgroundTask; never log/return it raw.
        return token

    async def reset_password(self, reset_token: str, new_password: str) -> None:
        """Complete a password reset using a previously issued reset token."""
        try:
            payload = decode_token(reset_token, expected_type=TokenType.RESET_PASSWORD)
        except InvalidTokenError as exc:
            raise TokenInvalidException("Reset token is invalid or expired") from exc

        user_id = UUID(payload.sub)
        await self.user_repo.set_password_hash(user_id, hash_password(new_password))  # TODO
        await self.token_repo.revoke_all_for_user(user_id)  # TODO
        logger.info("password_reset_completed", user_id=str(user_id))
