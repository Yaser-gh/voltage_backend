"""Payment management business logic."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FileOwnerType
from app.core.logging import get_logger
from app.dependencies.pagination import PaginationParams
from app.exceptions.custom import NotFoundException
from app.repositories.file_repository import FileRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.payment import PaymentCreateRequest, PaymentUpdateRequest
from app.services.file_service import FileService
from app.utils.datetime_utils import utcnow

logger = get_logger("payment_service")


class PaymentService:
    """Business logic for recording and managing project payments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.project_repo = ProjectRepository(session)
        self.file_repo = FileRepository(session)
        self.file_service = FileService(session)

    async def create_payment(self, payload: PaymentCreateRequest) -> object:
        """Record a new payment and refresh the parent project's total_paid aggregate."""
        project = await self.project_repo.get_by_id(payload.project_id)  # TODO
        if project is None:
            raise NotFoundException("Project not found")

        payment = await self.payment_repo.create(  # TODO
            project_id=payload.project_id, amount=payload.amount, bank_name=payload.bank_name,
            account_number=payload.account_number, description=payload.description,
            receipt_created_at=utcnow().date(), paid_at=payload.paid_at,
        )
        await self.project_repo.recalculate_total_paid(payload.project_id)  # TODO
        logger.info("payment_created", payment_id=str(getattr(payment, "id", None)), project_id=str(payload.project_id))
        return payment

    async def get_payment(self, payment_id: UUID) -> object:
        payment = await self.payment_repo.get_by_id(payment_id)  # TODO
        if payment is None:
            raise NotFoundException("Payment not found")
        return payment

    async def list_payments(self, pagination: PaginationParams, *, project_id: UUID | None = None,
                              date_from: date | None = None, date_to: date | None = None):
        return await self.payment_repo.search(  # TODO
            query=pagination.search, project_id=project_id, date_from=date_from, date_to=date_to,
            offset=pagination.offset, limit=pagination.limit,
            sort_by=pagination.sort_by, sort_order=pagination.sort_order,
        )

    async def list_project_payments(self, project_id: UUID, pagination: PaginationParams):
        return await self.payment_repo.get_by_project(project_id, offset=pagination.offset, limit=pagination.limit)  # TODO

    async def update_payment(self, payment_id: UUID, payload: PaymentUpdateRequest) -> object:
        existing = await self.get_payment(payment_id)
        update_data = payload.model_dump(exclude_unset=True)
        payment = await self.payment_repo.update(payment_id, **update_data)  # TODO
        await self.project_repo.recalculate_total_paid(existing.project_id)  # TODO
        logger.info("payment_updated", payment_id=str(payment_id))
        return payment

    async def delete_payment(self, payment_id: UUID) -> None:
        existing = await self.get_payment(payment_id)
        await self.payment_repo.soft_delete(payment_id)  # TODO
        await self.project_repo.recalculate_total_paid(existing.project_id)  # TODO
        logger.info("payment_deleted", payment_id=str(payment_id))

    async def get_total_payments(self, *, project_id: UUID | None = None, owner_id: UUID | None = None) -> float:
        return await self.payment_repo.get_total_amount(project_id=project_id, owner_id=owner_id)  # TODO

    async def get_last_payments(self, limit: int = 5) -> list:
        return await self.payment_repo.get_recent(limit)  # TODO

    async def upload_receipt(self, payment_id: UUID, file, uploaded_by_id: UUID) -> object:
        await self.get_payment(payment_id)
        return await self.file_service.upload(
            file, owner_type=FileOwnerType.PAYMENT, project_id=None, payment_id=payment_id,
            uploaded_by_id=uploaded_by_id, max_size_mb=None,
        )

    async def delete_receipt(self, payment_id: UUID, file_id: UUID) -> None:
        await self.get_payment(payment_id)
        await self.file_service.delete(file_id)

    async def list_receipts(self, payment_id: UUID) -> list:
        await self.get_payment(payment_id)
        return await self.file_repo.get_by_payment(payment_id)  # TODO
