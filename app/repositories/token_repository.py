"""Refresh token persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.token import RefreshToken
from app.repositories.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    """Data-access methods for refresh-token lifecycle management (rotation, revocation)."""

    model = RefreshToken

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch a refresh token record by its hash (never store/query raw tokens).

        TODO: implement with `select(RefreshToken).where(
        RefreshToken.token_hash == token_hash)`.
        """
        raise NotImplementedError

    async def revoke(self, token_id: UUID) -> None:
        """Mark a single refresh token as revoked.

        TODO: implement as `UPDATE refresh_tokens SET revoked_at = utcnow()
        WHERE id = token_id`.
        """
        raise NotImplementedError

    async def revoke_family(self, family_id: UUID) -> None:
        """Revoke an entire rotation family — used when token reuse is detected,
        as a signal that the family may have been stolen.

        TODO: implement as a bulk UPDATE filtered on RefreshToken.family_id.
        """
        raise NotImplementedError

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user (e.g. on password change).

        TODO: implement as a bulk UPDATE filtered on RefreshToken.user_id.
        """
        raise NotImplementedError

    async def mark_replaced(self, token_id: UUID, replaced_by_id: UUID) -> None:
        """Link an old token to the new token that replaced it (rotation audit trail).

        TODO: implement as a targeted UPDATE statement.
        """
        raise NotImplementedError

    async def purge_expired(self, before: datetime) -> int:
        """Bulk-delete expired token rows older than `before` (housekeeping/cron task).

        TODO: implement as a bulk DELETE filtered on RefreshToken.expires_at < before.
        Returns the number of rows deleted.
        """
        raise NotImplementedError
