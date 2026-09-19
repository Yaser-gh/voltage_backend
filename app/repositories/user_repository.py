"""User persistence repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, or_, func

from app.models.user import User, UserPhoneNumber
from app.models.project import Project
from app.models.role import Role
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utcnow


class UserRepository(BaseRepository[User]):
    """Data-access methods for the User aggregate (user + phone numbers + roles)."""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_username(self, username: str) -> User | None:
        """Fetch a user by unique username (used during login)."""
        stmt = select(User).where(User.username ==
                                   username, User.deleted_at.is_(None))
        return await self.session.scalar(stmt)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by unique email."""
        stmt = select(User).where(
            User.email == email, User.deleted_at.is_(None))
        return await self.session.scalar(stmt)

    async def get_by_phone(self, phone: str) -> User | None:
        """Fetch a user by primary phone number (uniqueness check on create/update)."""
        stmt = select(User).where(
            User.phone == phone, User.deleted_at.is_(None))
        return await self.session.scalar(stmt)

    async def username_or_email_exists(self, username: str, email: str | None) -> bool:
        """Check uniqueness for username/email prior to user creation."""
        canditions = [User.username == username]
        if email:
            canditions.append(User.email == email)
        stmt = (
            select(User.u_id)
            .where(or_(*canditions), User.deleted_at.is_(None))
            .limit(1)
        )
        resp = await self.session.execute(stmt)
        return resp.first() is not None

    async def search(
        self,
        *,
        query: str | None,
        is_active: bool | None,
        offset: int,
        limit: int,
        sort_by: str | None,
        sort_order: str,
    ) -> tuple[list[User], int]:
        """Search/filter/paginate users by name, username, or phone."""
        return self.list(
            offset=offset,
            limit=limit,
            sort_by=sort_by or "created_at",
            sort_order=sort_order,
            search=query,
            filters={"Is_active": is_active} if is_active is not None else None,
        )
        

    async def add_phone_number(
        self, user_id: UUID, phone: str, label: str | None
    ) -> UserPhoneNumber:
        """Add a secondary phone number to a user."""
        instance = UserPhoneNumber(user_id=user_id, phone=phone, label=label)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete_phone_number(self, user_id: UUID, phone_id: UUID) -> bool:
        """Remove a secondary phone number, scoped to its owning user."""
        stmt = select(UserPhoneNumber).where(
            UserPhoneNumber.user_id == user_id, UserPhoneNumber.u_id == phone_id
        )
        resp = await self.session.execute(stmt)
        instance = resp.scalar_one_or_none()
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def update_avatar(
        self, user_id: UUID, avatar_file_id: UUID | None
    ) -> User | None:
        """Set (or clear, if None) a user's avatar file reference."""
        return await self.update(user_id, avatar_file_id=avatar_file_id)

    async def update_biography(
        self, user_id: UUID, biography: str | None
    ) -> User | None:
        """Update only the biography field."""
        return await self.update(user_id, biography=biography)

    async def update_primary_phone(self, user_id: UUID, phone: str) -> User | None:
        """Update the user's primary phone number."""
        return await self.update(user_id, phone=phone)

    async def get_payment_summary(self, user_id: UUID) -> dict:
        """Aggregate total_payments / last_payment_at for a user across their projects."""
        user = await self.get_by_id(user_id)
        if not user:
            return {"user_id": user_id, "total_payments": 0, "last_payment_at": None}
        return {
            "user_id": user_id,
            "total_payments": user.total_payments,
            "last_payment_at": user.last_payment_at,
        }

    async def get_projects_count(self, user_id: UUID) -> dict:
        """Count a user's projects, broken down by status."""
        stmt = (
            select(Project.status, func.count())
            .where(Project.owner_id == user_id)
            .group_by(Project.status)
        )
        resp = await self.session.execute(stmt)
        counts = {status: count for status, count in resp.all()}
        return {
            "user_id": user_id,
            "projects_count": sum(counts.values()),
            "active_count": counts.get("active", 0),
            "finished_count": counts.get("finished", 0),
            "stopped_count": counts.get("stopped", 0),
            "bad_count": counts.get("bad", 0),
        }

    async def set_failed_login_attempts(
        self, user_id: UUID, attempts: int, locked_until=None
    ) -> None:
        """Persist updated brute-force counters after a login attempt."""
        return await self.update(
            user_id, failed_login_attempts=attempts, locked_until=locked_until
        )

    async def set_last_login(self, user_id: UUID) -> None:
        """Record successful login timestamp and reset failed-attempt counters."""
        return await self.update(
            user_id, last_login_at=utcnow().replace(tzinfo=None), failed_login_attempts=0, locked_until=None
        )

    async def set_password_hash(self, user_id: UUID, hashed_password: str) -> None:
        """Persist a new password hash (used by change-password / reset-password flows)."""
        return await self.update(user_id, hash_password=hashed_password)

    async def assign_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        """Replace a user's role assignments."""
        user = await self.get_by_id(user_id)
        if not user:
            return

        if not role_ids:
            user.roles = []
            await self.session.flush()
            return

        stmt = select(Role).where(Role.u_id.in_(role_ids))
        user.roles = list((await self.session.scalars(stmt)).all())
        await self.session.flush()
