"""User management endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.dependencies.db import get_db_session
from app.dependencies.pagination import PaginationParams, pagination_params
from app.permissions.checker import RequirePermission
from app.permissions.roles import Permission
from app.responses.envelope import (
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    SuccessResponse,
    build_pagination_meta,
)
from app.schemas.auth import CurrentUser
from app.schemas.file import FileAssetResponse
from app.schemas.user import (
    PhoneNumberCreate,
    PhoneNumberResponse,
    UpdateBiographyRequest,
    UpdatePhoneRequest,
    UserCreateRequest,
    UserListItemResponse,
    UserPaymentSummaryResponse,
    UserProjectsCountResponse,
    UserResponse,
    UserUpdateRequest,
    GetUsersRequest,
    GetUserInfoRequest
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/createUser",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a user account with hashed password and optional role assignments.",
    responses={409: {"model": ErrorResponse, "description": "Username, email, or phone already in use"}},
    dependencies=[Depends(RequirePermission(Permission.USER_CREATE))],
)
async def create_user(payload: UserCreateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[UserResponse]:
    service = UserService(session)
    user = await service.create_user(payload)
    return SuccessResponse(status=201, message="User created", data=user)


@router.post(
    "/getUsers",
    response_model=PaginatedResponse[UserListItemResponse],
    summary="List / search users",
    description="Returns a paginated, sortable, searchable list of users. Supports "
                "filtering by active status.",
    dependencies=[Depends(RequirePermission(Permission.USER_LIST))],
)
async def list_users(
    payload: GetUsersRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[UserListItemResponse]:
    service = UserService(session)
    items, total = await service.list_users(payload, is_active=is_active)
    return PaginatedResponse(data=items, meta=build_pagination_meta(pagination.page, pagination.limit, total))


@router.post(
    "/getUserInfo",
    response_model=SuccessResponse[UserResponse],
    summary="Get a user by id",
    responses={404: {"model": ErrorResponse, "description": "User not found"}},
    dependencies=[Depends(RequirePermission(Permission.USER_READ))],
)
async def get_user(payload: GetUserInfoRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[UserResponse]:
    service = UserService(session)
    user = await service.get_user(payload)
    return SuccessResponse(data=user)


@router.post(
    "/updateUser",
    response_model=SuccessResponse[UserResponse],
    summary="Update a user",
    description="Partial update — only supplied fields are changed.",
    responses={404: {"model": ErrorResponse, "description": "User not found"}},
    dependencies=[Depends(RequirePermission(Permission.USER_UPDATE))],
)
async def update_user(payload: UserUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[UserResponse]:
    service = UserService(session)
    user = await service.update_user(user_id, payload)
    return SuccessResponse(message="User updated.", data=user)


@router.post(
    "/deleteUser",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a user",
    description="Soft-deletes the user; the record is retained for audit purposes.",
    responses={404: {"model": ErrorResponse, "description": "User not found"}},
    dependencies=[Depends(RequirePermission(Permission.USER_DELETE))],
)
async def delete_user(payload: GetUserInfoRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = UserService(session)
    await service.delete_user(payload.user_id)
    return SuccessResponse(message="User deleted", data=MessageResponse(message="User deleted"))


@router.post(
    "/{user_id}/avatar",
    response_model=SuccessResponse[FileAssetResponse],
    summary="Upload / replace a user's avatar image",
    description="Accepts image uploads only (jpg/png/webp/gif). Validates extension, "
                "MIME type, and size before persisting under a UUID filename.",
    responses={415: {"model": ErrorResponse, "description": "Unsupported file type"}},
    dependencies=[Depends(RequirePermission(Permission.USER_UPDATE))],
)
async def upload_avatar(
    user_id: UUID, file: UploadFile = File(...), session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[FileAssetResponse]:
    service = UserService(session)
    file_asset = await service.upload_avatar(user_id, file)
    return SuccessResponse(message="Avatar uploaded", data=file_asset)


@router.post(
    "/deleteAvatar",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a user's avatar",
    dependencies=[Depends(RequirePermission(Permission.USER_UPDATE))],
)
async def delete_avatar(payload: GetUserInfoRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = UserService(session)
    await service.delete_avatar(payload.user_id)
    return SuccessResponse(message="Avatar deleted", data=MessageResponse(message="Avatar deleted"))

@router.post(
    "/{user_id}/phones",
    response_model=SuccessResponse[PhoneNumberResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a secondary phone number",
    dependencies=[Depends(RequirePermission(Permission.USER_UPDATE))],
)
async def add_phone(user_id: UUID, payload: PhoneNumberCreate, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[PhoneNumberResponse]:
    service = UserService(session)
    phone = await service.add_phone(user_id, payload.phone, payload.label)
    return SuccessResponse(status=201, message="Phone number added", data=phone)


@router.delete(
    "/{user_id}/phones/{phone_id}",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a secondary phone number",
    responses={404: {"model": ErrorResponse, "description": "Phone number not found"}},
    dependencies=[Depends(RequirePermission(Permission.USER_UPDATE))],
)
async def delete_phone(user_id: UUID, phone_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = UserService(session)
    await service.delete_phone(user_id, phone_id)
    return SuccessResponse(message="Phone number deleted", data=MessageResponse(message="Phone number deleted"))


@router.get(
    "/{user_id}/payments/last",
    response_model=SuccessResponse[UserPaymentSummaryResponse],
    summary="Get a user's last payment and total payments",
    dependencies=[Depends(RequirePermission(Permission.USER_READ))],
)
async def get_user_payment_summary(user_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[UserPaymentSummaryResponse]:
    service = UserService(session)
    summary = await service.get_payment_summary(user_id)
    return SuccessResponse(data=summary)


@router.get(
    "/{user_id}/projects/count",
    response_model=SuccessResponse[UserProjectsCountResponse],
    summary="Get a user's project count broken down by status",
    dependencies=[Depends(RequirePermission(Permission.USER_READ))],
)
async def get_user_projects_count(user_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[UserProjectsCountResponse]:
    service = UserService(session)
    counts = await service.get_projects_count(user_id)
    return SuccessResponse(data=counts)
