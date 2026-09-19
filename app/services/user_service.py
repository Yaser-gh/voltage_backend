"""User management business logic."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FileOwnerType
from app.core.logging import get_logger
from app.dependencies.pagination import PaginationParams
from app.exceptions.custom import AlreadyExistsException, NotFoundException
from app.repositories.file_repository import FileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreateRequest, UserUpdateRequest, GetUsersRequest, GetUserInfoRequest
from app.security.password import hash_password
from app.services.file_service import FileService

logger = get_logger("user_service")


class UserService:
    """Business logic for creating, updating, searching, and enriching users."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.file_repo = FileRepository(session)
        self.file_service = FileService(session)

    async def create_user(self, payload: UserCreateRequest) -> object:
        """Create a new user after enforcing username/email/phone uniqueness."""
        if await self.user_repo.username_or_email_exists(payload.username, payload.email):  # TODO
            raise AlreadyExistsException("Username or email is already in use")
        existing_phone = await self.user_repo.get_by_phone(payload.phone)  # TODO
        if existing_phone is not None:
            raise AlreadyExistsException("Phone number is already in use")

        user = await self.user_repo.create(  # TODO
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            email=payload.email,
            phone=payload.phone,
            hashed_password=hash_password(payload.password),
            biography=payload.biography,
            is_active=payload.is_active,
        )
        if payload.role_ids:
            await self.user_repo.assign_roles(user.u_id, payload.role_ids)  # TODO
        logger.info("user_created", user_id=str(getattr(user, "id", None)))
        return user

    async def get_user(self, payload: GetUserInfoRequest) -> object:
        """Fetch a single user by id, raising 404 if not found."""
        user = await self.user_repo.get_by_id(payload.user_id)  # TODO
        if user is None:
            raise NotFoundException("User not found")
        await self.user_repo.session.refresh(user, ["phone_numbers", "roles", "projects", "refresh_tokens"])
        for role in user.roles:
            await self.user_repo.session.refresh(role, ["permissions"])
        return user

    async def list_users(self, paylod: GetUsersRequest, *, is_active: bool | None = None):
        """List/search/paginate users."""
        return await self.user_repo.search(  # TODO
            query=paylod.search_text, is_active=paylod.is_active, offset=paylod.offset, limit=paylod.limit,
            sort_by=paylod.sort_by, sort_order=paylod.sort_order,
        )

    async def update_user(self, user_id: UUID, payload: UserUpdateRequest) -> object:
        """Partially update a user's editable fields."""
        await self.get_user(user_id)
        update_data = payload.model_dump(exclude_unset=True, exclude={"role_ids"})
        user = await self.user_repo.update(user_id, **update_data)  # TODO
        if payload.role_ids is not None:
            await self.user_repo.assign_roles(user_id, payload.role_ids)  # TODO
        logger.info("user_updated", user_id=str(user_id))
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """Soft-delete a user."""
        await self.get_user(user_id)
        await self.user_repo.soft_delete(user_id)  # TODO
        logger.info("user_deleted", user_id=str(user_id))

    async def upload_avatar(self, user_id: UUID, file) -> object:
        """Validate, store, and attach a new avatar image to a user."""
        await self.get_user(user_id)
        file_asset = await self.file_service.upload(
            file, owner_type=FileOwnerType.AVATAR, project_id=None, payment_id=None,
            uploaded_by_id=user_id, max_size_mb=None,
        )
        await self.user_repo.update_avatar(user_id, file_asset.u_id)  # TODO
        logger.info("avatar_uploaded", user_id=str(user_id))
        return file_asset

    async def delete_avatar(self, user_id: UUID) -> None:
        """Remove a user's current avatar (file + reference)."""
        user = await self.get_user(user_id)
        if getattr(user, "avatar_file_id", None):
            await self.file_service.delete(user.avatar_file_id)
        await self.user_repo.update_avatar(user_id, None)  # TODO
        logger.info("avatar_deleted", user_id=str(user_id))

    async def update_biography(self, user_id: UUID, biography: str | None) -> object:
        await self.get_user(user_id)
        return await self.user_repo.update_biography(user_id, biography)  # TODO

    async def update_phone(self, user_id: UUID, phone: str) -> object:
        """Update the primary phone number, enforcing global uniqueness."""
        await self.get_user(user_id)
        existing = await self.user_repo.get_by_phone(phone)  # TODO
        if existing is not None and existing.u_id != user_id:
            raise AlreadyExistsException("Phone number is already in use by another user")
        return await self.user_repo.update_primary_phone(user_id, phone)  # TODO

    async def add_phone(self, user_id: UUID, phone: str, label: str | None) -> object:
        await self.get_user(user_id)
        return await self.user_repo.add_phone_number(user_id, phone, label)  # TODO

    async def delete_phone(self, user_id: UUID, phone_id: UUID) -> None:
        await self.get_user(user_id)
        deleted = await self.user_repo.delete_phone_number(user_id, phone_id)  # TODO
        if not deleted:
            raise NotFoundException("Phone number not found")

    async def get_payment_summary(self, user_id: UUID) -> dict:
        await self.get_user(user_id)
        return await self.user_repo.get_payment_summary(user_id)  # TODO

    async def get_projects_count(self, user_id: UUID) -> dict:
        await self.get_user(user_id)
        return await self.user_repo.get_projects_count(user_id)  # TODO
