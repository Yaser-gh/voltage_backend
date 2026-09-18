"""
One-off seed script: creates the default roles and permissions in the database.

Run with:  python -m scripts.seed_roles

Idempotent — safe to re-run on every deploy; get_or_create() skips rows
that already exist instead of erroring or duplicating them.
"""
import asyncio

from app.core.logging import get_logger
from app.database.session import get_db_session_ctx
from app.permissions.roles import DEFAULT_ROLE_PERMISSIONS
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository

logger = get_logger("seed_roles")


async def seed() -> None:
    async with get_db_session_ctx() as session:
        role_repo = RoleRepository(session)
        permission_repo = PermissionRepository(session)

        for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
            role = await role_repo.get_or_create(name=role_name.value)
            logger.info("seeding_role", role=role_name.value, permission_count=len(permissions))

            for perm in permissions:
                permission = await permission_repo.get_or_create(code=perm.value)
                await role_repo.attach_permission(role.u_id, permission.u_id)

        logger.info("seed_complete")


if __name__ == "__main__":
    asyncio.run(seed())
