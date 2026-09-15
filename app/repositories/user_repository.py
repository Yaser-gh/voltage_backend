"""User persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserPhoneNumber
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data-access methods for the User aggregate (user + phone numbers + roles)."""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by unique username (used during login).

        TODO: implement with `select(User).where(User.username == username,
        User.deleted_at.is_(None))`, eager-loading roles/permissions via selectin.
        """
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by unique email.

        TODO: implement similarly to get_by_username, filtering on User.email.
        """
        raise NotImplementedError

    async def get_by_phone(self, phone: str) -> User | None:
        """Fetch a user by primary phone number (uniqueness check on create/update).

        TODO: implement with a simple equality filter on User.phone.
        """
        raise NotImplementedError

    async def username_or_email_exists(self, username: str, email: str | None) -> bool:
        """Check uniqueness for username/email prior to user creation.

        TODO: implement with an OR-combined `select(exists().where(...))`.
        """
        raise NotImplementedError

    async def search(
        self, *, query: str | None, is_active: bool | None, offset: int, limit: int,
        sort_by: str | None, sort_order: str,
    ) -> tuple[list[User], int]:
        """Search/filter/paginate users by name, username, or phone.

        TODO: implement with `.ilike()` across first_name/last_name/username/phone,
        combined with an `is_active` equality filter when provided.
        """
        raise NotImplementedError

    async def add_phone_number(self, user_id: UUID, phone: str, label: str | None) -> UserPhoneNumber:
        """Add a secondary phone number to a user.

        TODO: implement as `UserPhoneNumber(user_id=user_id, phone=phone, label=label)`,
        add to session, flush, return instance.
        """
        raise NotImplementedError

    async def delete_phone_number(self, user_id: UUID, phone_id: UUID) -> bool:
        """Remove a secondary phone number, scoped to its owning user.

        TODO: implement as a scoped DELETE ensuring phone.user_id == user_id.
        """
        raise NotImplementedError

    async def update_avatar(self, user_id: UUID, avatar_file_id: UUID | None) -> User | None:
        """Set (or clear, if None) a user's avatar file reference.

        TODO: implement as an UPDATE statement on User.avatar_file_id.
        """
        raise NotImplementedError

    async def update_biography(self, user_id: UUID, biography: str | None) -> User | None:
        """Update only the biography field.

        TODO: implement as a targeted UPDATE statement.
        """
        raise NotImplementedError

    async def update_primary_phone(self, user_id: UUID, phone: str) -> User | None:
        """Update the user's primary phone number.

        TODO: implement as a targeted UPDATE statement on User.phone.
        """
        raise NotImplementedError

    async def get_payment_summary(self, user_id: UUID) -> dict:
        """Aggregate total_payments / last_payment_at for a user across their projects.

        TODO: implement via a JOIN/aggregate query across projects -> payments,
        or read the denormalized User.total_payments / last_payment_at columns.
        """
        raise NotImplementedError

    async def get_projects_count(self, user_id: UUID) -> dict:
        """Count a user's projects, broken down by status.

        TODO: implement via `select(Project.status, func.count()).where(
        Project.owner_id == user_id).group_by(Project.status)`.
        """
        raise NotImplementedError

    async def set_failed_login_attempts(self, user_id: UUID, attempts: int, locked_until=None) -> None:
        """Persist updated brute-force counters after a login attempt.

        TODO: implement as a targeted UPDATE statement.
        """
        raise NotImplementedError

    async def set_last_login(self, user_id: UUID) -> None:
        """Record successful login timestamp and reset failed-attempt counters.

        TODO: implement as a targeted UPDATE statement.
        """
        raise NotImplementedError

    async def set_password_hash(self, user_id: UUID, hashed_password: str) -> None:
        """Persist a new password hash (used by change-password / reset-password flows).

        TODO: implement as a targeted UPDATE statement.
        """
        raise NotImplementedError

    async def assign_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        """Replace a user's role assignments.

        TODO: implement by clearing and re-inserting rows in the `user_roles`
        association table (or mutating `user.roles` on a loaded ORM instance).
        """
        raise NotImplementedError
