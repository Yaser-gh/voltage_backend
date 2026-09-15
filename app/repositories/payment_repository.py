"""Payment persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Data-access methods for the Payment aggregate."""

    model = Payment

    async def get_by_project(self, project_id: UUID, *, offset: int, limit: int) -> tuple[list[Payment], int]:
        """List all payments recorded against a specific project.

        TODO: implement with `select(Payment).where(Payment.project_id == project_id,
        Payment.deleted_at.is_(None)).order_by(Payment.paid_at.desc())`.
        """
        raise NotImplementedError

    async def search(
        self, *, query: str | None, project_id: UUID | None, date_from: date | None,
        date_to: date | None, offset: int, limit: int, sort_by: str | None, sort_order: str,
    ) -> tuple[list[Payment], int]:
        """Search/filter/paginate payments by description, project, or date range.

        TODO: implement with `.ilike()` on description, equality on project_id,
        and `.between()` on paid_at when a date range is supplied.
        """
        raise NotImplementedError

    async def get_total_amount(self, *, project_id: UUID | None = None, owner_id: UUID | None = None) -> float:
        """Sum payment amounts, optionally scoped to a project or a user's projects.

        TODO: implement via `select(func.coalesce(func.sum(Payment.amount), 0))`
        with appropriate joins/filters.
        """
        raise NotImplementedError

    async def get_this_month_total(self) -> float:
        """Sum payment amounts recorded within the current calendar month.

        TODO: implement using app.utils.datetime_utils.month_range() bounds
        applied to Payment.paid_at via `.between()`.
        """
        raise NotImplementedError

    async def get_recent(self, limit: int = 5) -> list[Payment]:
        """Fetch the most recent payments system-wide (for dashboard 'recent' widget).

        TODO: implement with `.order_by(Payment.paid_at.desc()).limit(limit)`.
        """
        raise NotImplementedError

    async def get_last_for_project(self, project_id: UUID) -> Payment | None:
        """Fetch the most recent payment for a given project.

        TODO: implement with `.where(Payment.project_id == project_id)
        .order_by(Payment.paid_at.desc()).limit(1)`.
        """
        raise NotImplementedError
