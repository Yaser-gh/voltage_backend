"""Role and permission persistence repository — RBAC read/write access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.role import Permission, Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Data-access methods for roles, including their permission attachments."""

    model = Role

    async def get_by_name(self, name: str) -> Role | None:
        """Fetch a role by its unique name (e.g. 'admin')."""
        stmt = select(Role).where(Role.name == name)
        return await self.session.scalar(stmt)

    async def get_or_create(self, name: str, description: str | None = None) -> Role:
        """Fetch a role by name, creating it if it doesn't exist yet. Idempotent —
        safe to call repeatedly (e.g. from a seed script run on every deploy)."""
        role = await self.get_by_name(name)
        if role is not None:
            return role
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.flush()
        return role

    async def attach_permission(self, role_id: UUID, permission_id: UUID) -> None:
        """Link a permission to a role (no-op if already linked)."""
        role = await self.get_by_id(role_id)
        if role is None:
            return
        
        await self.session.refresh(role, ["permissions"])
        # `role.permissions` is a selectin-loaded relationship; SQLAlchemy
        # dedupes automatically if the permission is already attached.
        stmt = select(Permission).where(Permission.u_id == permission_id)
        permission = await self.session.scalar(stmt)
        if permission is not None and permission not in role.permissions:
            role.permissions.append(permission)
            await self.session.flush()

    async def detach_permission(self, role_id: UUID, permission_id: UUID) -> None:
        """Remove a permission from a role."""
        role = await self.get_by_id(role_id)
        if role is None:
            return
        role.permissions = [p for p in role.permissions if p.u_id != permission_id]
        await self.session.flush()

    async def list_all(self) -> list[Role]:
        """List every role in the system (small table, no pagination needed)."""
        stmt = select(Role)
        return list((await elf.session.scalars(stmt)).all())
