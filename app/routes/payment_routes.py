"""Payment management endpoints, including receipts."""
# from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.dependencies.db import get_db_session
from app.dependencies.pagination import PaginationParams, pagination_params
from app.permissions.checker import RequirePermission
from app.permissions.roles import Permission
from app.responses.envelope import ErrorResponse, MessageResponse, PaginatedResponse, SuccessResponse, build_pagination_meta
from app.schemas.auth import CurrentUser
from app.schemas.file import FileAssetResponse
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentListItemResponse,
    PaymentResponse,
    PaymentUpdateRequest,
    TotalPaymentsResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "",
    response_model=SuccessResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payment",
    description="Records a payment against a project and refreshes the project's total_paid aggregate.",
    responses={404: {"model": ErrorResponse, "description": "Project not found"}},
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_CREATE))],
)
async def create_payment(payload: PaymentCreateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(session)
    payment = await service.create_payment(payload)
    return SuccessResponse(status=201, message="Payment created", data=payment)


@router.get(
    "",
    response_model=PaginatedResponse[PaymentListItemResponse],
    summary="List / search / filter payments",
    description="Supports free-text search on description, project filtering, and paid-date range filtering.",
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_LIST))],
)
async def list_payments(
    project_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[PaymentListItemResponse]:
    service = PaymentService(session)
    items, total = await service.list_payments(pagination, project_id=project_id, date_from=date_from, date_to=date_to)
    return PaginatedResponse(data=items, meta=build_pagination_meta(pagination.page, pagination.limit, total))


@router.get(
    "/total",
    response_model=SuccessResponse[TotalPaymentsResponse],
    summary="Get total payments amount",
    description="Optionally scoped to a single project via `project_id` query parameter.",
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_LIST))],
)
async def get_total_payments(project_id: UUID | None = None, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[TotalPaymentsResponse]:
    service = PaymentService(session)
    total = await service.get_total_payments(project_id=project_id)
    scope = f"project:{project_id}" if project_id else "system"
    return SuccessResponse(data=TotalPaymentsResponse(total_amount=total, count=0, scope=scope))


@router.get(
    "/recent",
    response_model=SuccessResponse[list[PaymentListItemResponse]],
    summary="Get the most recent payments system-wide",
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_LIST))],
)
async def get_recent_payments(limit: int = 5, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[list[PaymentListItemResponse]]:
    service = PaymentService(session)
    payments = await service.get_last_payments(limit)
    return SuccessResponse(data=payments)


@router.get(
    "/project/{project_id}",
    response_model=PaginatedResponse[PaymentListItemResponse],
    summary="List all payments for a specific project",
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_LIST))],
)
async def get_project_payments(
    project_id: UUID, pagination: PaginationParams = Depends(pagination_params), session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[PaymentListItemResponse]:
    service = PaymentService(session)
    items = await service.list_project_payments(project_id, pagination)
    return PaginatedResponse(data=items, meta=build_pagination_meta(pagination.page, pagination.limit, len(items) if items else 0))


@router.get(
    "/{payment_id}",
    response_model=SuccessResponse[PaymentResponse],
    summary="Get payment details",
    responses={404: {"model": ErrorResponse, "description": "Payment not found"}},
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_READ))],
)
async def get_payment(payment_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(session)
    payment = await service.get_payment(payment_id)
    return SuccessResponse(data=payment)


@router.patch(
    "/{payment_id}",
    response_model=SuccessResponse[PaymentResponse],
    summary="Update a payment",
    responses={404: {"model": ErrorResponse, "description": "Payment not found"}},
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_UPDATE))],
)
async def update_payment(payment_id: UUID, payload: PaymentUpdateRequest, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[PaymentResponse]:
    service = PaymentService(session)
    payment = await service.update_payment(payment_id, payload)
    return SuccessResponse(message="Payment updated", data=payment)


@router.delete(
    "/{payment_id}",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a payment",
    responses={404: {"model": ErrorResponse, "description": "Payment not found"}},
    dependencies=[Depends(RequirePermission(Permission.PAYMENT_DELETE))],
)
async def delete_payment(payment_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = PaymentService(session)
    await service.delete_payment(payment_id)
    return SuccessResponse(message="Payment deleted", data=MessageResponse(message="Payment deleted"))


@router.post(
    "/{payment_id}/receipts",
    response_model=SuccessResponse[FileAssetResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a receipt file for a payment",
    responses={
        404: {"model": ErrorResponse, "description": "Payment not found"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
    },
    dependencies=[Depends(RequirePermission(Permission.FILE_UPLOAD))],
)
async def upload_receipt(
    payment_id: UUID, file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[FileAssetResponse]:
    service = PaymentService(session)
    file_asset = await service.upload_receipt(payment_id, file, current_user.id)
    return SuccessResponse(status=201, message="Receipt uploaded", data=file_asset)


@router.get(
    "/{payment_id}/receipts",
    response_model=SuccessResponse[list[FileAssetResponse]],
    summary="List receipt files for a payment",
    dependencies=[Depends(RequirePermission(Permission.FILE_READ))],
)
async def list_receipts(payment_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[list[FileAssetResponse]]:
    service = PaymentService(session)
    receipts = await service.list_receipts(payment_id)
    return SuccessResponse(data=receipts)


@router.delete(
    "/{payment_id}/receipts/{file_id}",
    response_model=SuccessResponse[MessageResponse],
    summary="Delete a receipt file from a payment",
    dependencies=[Depends(RequirePermission(Permission.FILE_DELETE))],
)
async def delete_receipt(payment_id: UUID, file_id: UUID, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[MessageResponse]:
    service = PaymentService(session)
    await service.delete_receipt(payment_id, file_id)
    return SuccessResponse(message="Receipt deleted", data=MessageResponse(message="Receipt deleted"))
