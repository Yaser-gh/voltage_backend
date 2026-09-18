"""Permission persistence repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.role import Permission
from app.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """Data-access methods for individual permission codes."""

    model = Permission

    async def get_by_code(self, code: str) -> Permission | None:
        """Fetch a permission by its unique code (e.g. 'project:create')."""
        stmt = select(Permission).where(Permission.code == code)
        return await self.session.scalar(stmt)

    async def get_or_create(self, code: str, description: str | None = None) -> Permission:
        """Fetch a permission by code, creating it if it doesn't exist yet. Idempotent."""
        permission = await self.get_by_code(code)
        if permission is not None:
            return permission
        permission = Permission(code=code, description=description)
        self.session.add(permission)
        await self.session.flush()
        return permission

    async def list_all(self) -> list[Permission]:
        """List every permission in the system."""
        stmt = select(Permission)
        return list((await self.session.scalars(stmt)).all())
