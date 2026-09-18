"""Payment persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from app.models.payment import Payment
from app.models.project import Project
from app.utils.datetime_utils import month_range
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Data-access methods for the Payment aggregate."""

    model = Payment

    async def get_by_project(self, project_id: UUID, *, offset: int, limit: int) -> tuple[list[Payment], int]:
        """List all payments recorded against a specific project."""
        stmt = select(self.model).where(
            self.model.project_id == project_id,
            self.model.deleted_at.is_(None),
            self.model.paid_at.desc()
        ).offset(offset).limit(limit)
        
        resp = (await self.session.scalars(stmt)).all()
        return resp, len(resp)

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
        """Sum payment amounts, optionally scoped to a project or a user's projects."""
        stmt = select(
            func.coalesce(
                func.sum(self.model.amount), 0)).join(
                    Project, Project.u_id == self.model.project_id).where(
                        self.model.project_id == project_id,
                        Project.owner_id == owner_id
                    )
        
        resp = await self.session.scalar(stmt)
        return float(resp)

    async def get_this_month_total(self) -> float:
        """Sum payment amounts recorded within the current calendar month."""
        start, end = month_range()
        
        stmt = select(func.coalesce(
            func.sum(self.model.amount), 0
        )).where(
            self.model.paid_at.between(start, end)
        )
        return float(await self.session.scalar(stmt))

    async def get_recent(self, limit: int = 5) -> list[Payment]:
        """Fetch the most recent payments system-wide (for dashboard 'recent' widget)."""
        stmt = select(self.model).order_by(self.model.paid_at.desc()).limit(limit)
        return (await self.session.scalars(stmt)).all()

    async def get_last_for_project(self, project_id: UUID) -> Payment | None:
        """Fetch the most recent payment for a given project."""
        stmt = select(self.model).where(self.model.project_id == project_id).order_by(self.model.paid_at.desc()).limit(1)
        return await self.session.scalar(stmt)
