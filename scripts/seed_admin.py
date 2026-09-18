"""
One-off bootstrap script: creates the first superuser account.

Solves the chicken-and-egg problem — POST /users requires an authenticated
admin, but on a fresh database no user exists yet to log in as. This script
writes directly through the repository, bypassing the API/permission layer.

Run with:  python -m scripts.seed_admin
Reads credentials from environment variables so no secret is hard-coded:

  ADMIN_USERNAME  (default: admin)
  ADMIN_PASSWORD  (required)
  ADMIN_PHONE     (default: 09120000000)
  ADMIN_EMAIL     (optional)

Safe to re-run — if a user with that username already exists, it exits
without creating a duplicate.
"""
import asyncio
import os
import sys

from app.core.logging import get_logger
from app.database.session import get_db_session_ctx
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.security.password import hash_password

logger = get_logger("seed_admin")


async def seed() -> None:
    username = os.getenv("ADMIN_USERNAME", "YaserDev")
    password = os.getenv("ADMIN_PASSWORD")
    phone = os.getenv("ADMIN_PHONE", "989371850903")
    email = os.getenv("ADMIN_EMAIL")

    if not password:
        logger.error("missing_admin_password")
        print("ERROR: set ADMIN_PASSWORD before running this script.")
        sys.exit(1)

    async with get_db_session_ctx() as session:
        user_repo = UserRepository(session)
        role_repo = RoleRepository(session)

        existing = await user_repo.get_by_username(username)
        if existing is not None:
            logger.info("admin_already_exists", username=username)
            print(f"User '{username}' already exists — nothing to do.")
            return

        admin_role = await role_repo.get_or_create(name="admin")

        user = await user_repo.create(
            first_name="Yaser",
            last_name="",
            username=username,
            email=email,
            phone=phone,
            hashed_password=hash_password(password),
            biography=None,
            is_active=True,
            is_verified=True,
            is_superuser=True,  # bypasses permission checks entirely (see RequirePermission)
        )
        await user_repo.assign_roles(user.u_id, [admin_role.u_id])

        logger.info("admin_created", username=username, user_id=str(user.u_id))
        print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
