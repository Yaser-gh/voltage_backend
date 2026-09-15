"""
One-off seed script: creates the default roles and permissions in the database.

Run with:  python -m scripts.seed_roles

NOTE: Per project scope, the actual persistence calls are left as TODOs —
wire them up to your repositories/session once the read/write query bodies
are implemented.
"""
import asyncio

from app.core.logging import get_logger
from app.database.session import get_db_session_ctx
from app.permissions.roles import DEFAULT_ROLE_PERMISSIONS

logger = get_logger("seed_roles")


async def seed() -> None:
    async with get_db_session_ctx() as session:
        for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
            logger.info("seeding_role", role=role_name.value, permission_count=len(permissions))
            # TODO: upsert the Role row, upsert each Permission row, and link
            # them via the role_permissions association table. Example shape:
            #
            #   role = await role_repo.get_or_create(name=role_name.value)
            #   for perm in permissions:
            #       permission = await permission_repo.get_or_create(code=perm.value)
            #       await role_repo.attach_permission(role.id, permission.id)


if __name__ == "__main__":
    asyncio.run(seed())
