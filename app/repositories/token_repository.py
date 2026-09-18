"""Refresh token persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update, delete, func

from app.models.token import RefreshToken
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utcnow


class TokenRepository(BaseRepository[RefreshToken]):
    """Data-access methods for refresh-token lifecycle management (rotation, revocation)."""

    model = RefreshToken

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch a refresh token record by its hash (never store/query raw tokens)."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        resp = await self.session.execute(stmt)
        return resp.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        """Mark a single refresh token as revoked."""
        stmt = (
            update(RefreshToken).where(
                RefreshToken.u_id == token_id, RefreshToken.revoked_at.is_(None)
            ).values(revoked_at=utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_family(self, family_id: UUID) -> None:
        """Revoke an entire rotation family — used when token reuse is detected,
        as a signal that the family may have been stolen."""
        stmt = (
            update(RefreshToken).where(
                RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
            ).values(revoked_at=utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user (e.g. on password change)."""
        stmt = (
            update(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            ).values(revoked_at=utcnow())
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_replaced(self, token_id: UUID, replaced_by_id: UUID) -> None:
        """Link an old token to the new token that replaced it (rotation audit trail)."""
        stmt = (
            update(RefreshToken).where(
                RefreshToken.u_id == token_id
            ).values(replaced_by_token_id=replaced_by_id)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def purge_expired(self, before: datetime) -> int:
        """Bulk-delete expired token rows older than `before` (housekeeping/cron task)."""
        cutoff = before or utcnow()
        stmt = delete(self.model).where(self.model.expires_at < cutoff)
        resp = await self.session.execute(stmt)
        await self.session.flush()
        return resp.rowcount or 0
    
    async def count_active_for_user(self, user_id: UUID) -> int:
        """Count active sessions for a user (e.g. to cap concurrent sessions).

        Args:
            user_id (UUID): a user id for get active sessions

        Returns:
            int: count all session active.
        """
        stmt = select(func.count()).select_from(self.model).where(
            self.model.user_id == user_id,
            self.model.revoked_at.is_(None),
            self.model.expires_at > utcnow()
        )
        return await self.session.scalar(stmt)
        
    async def list_active_for_user(self, user_id: UUID)-> list[RefreshToken]:
        stmt = select(self.model).where(
            self.model.revoked_at.is_(None),
            self.model.user_id == user_id,
            self.model.expires_at > utcnow()
        ).order_by(self.model.created_at.desc())
        return list((await self.session.scalars(stmt)).all())