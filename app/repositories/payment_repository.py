"""Payment persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.payment import Payment
from app.models.project import Project
from app.utils.datetime_utils import month_range
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Data-access methods for the Payment aggregate."""

    model = Payment

    async def get_by_project(self, project_id: UUID, *, offset: int, limit: int) -> tuple[list[Payment], int]:
        """List all payments recorded against a specific project."""
        stmt = select(
            self.model).where(self.model.project_id == project_id, self.model.deleted_at.is_(None))\
            .options(selectinload(self.model.project)).order_by(
                self.model.paid_at.desc()
            )
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt)
        
        stmt = stmt.offset(offset).limit(limit)
        return list((await self.session.scalars(stmt)).all()), total

    async def search(
        self, *, query: str | None, project_id: UUID | None, date_from: date | None,
        date_to: date | None, offset: int, limit: int, sort_by: str | None, sort_order: str,
    ) -> tuple[list[Payment], int]:
        """Search/filter/paginate payments by description, project, or date range."""
        stmt = select(self.model).where(self.model.deleted_at.is_(None)).options(selectinload(self.model.project))
        canditions = []
        if project_id is not None:
            canditions.append(self.model.project_id == project_id)
        if date_from is not None and date_to is not None:
            canditions.append(self.model.paid_at.between(date_from, date_to))
        elif date_from is not None:
            canditions.append(self.model.paid_at >= date_from)
        elif date_to is not None:
            canditions.append(self.model.paid_at <= date_to)
        
        if query:
            like = f"%{query}%"
            canditions.extend([or_(self.model.description.ilike(like), self.model.bank_name.ilike(like))])
        
        stmt = stmt.where(*canditions)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(stmt)
        
        sort_column = getattr(self.model, sort_by, self.model.paid_at) if sort_by else self.model.paid_at
        stmt = stmt.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        stmt = stmt.offset(offset).limit(limit)
        
        resp = await self.session.execute(stmt)
        return list(resp.scalars().all()), total

    async def get_total_amount(self, *, project_id: UUID | None = None, owner_id: UUID | None = None) -> float:
        """Sum payment amounts, optionally scoped to a project or a user's projects."""
        stmt = select(func.coalesce(func.sum(self.model.amount), 0)).where(
            self.model.deleted_at.is_(None)
        )
        if project_id is not None:
            stmt = stmt.where(self.model.project_id == project_id)
        
        elif owner_id is not None: 
            stmt = stmt.join(
                    Project, Project.u_id == self.model.project_id).where(Project.owner_id == owner_id)
            
        
        resp = await self.session.scalar(stmt)
        return float(resp)

    async def get_this_month_total(self) -> float:
        """Sum payment amounts recorded within the current calendar month."""
        start, end = month_range()
        
        stmt = select(func.coalesce(
            func.sum(self.model.amount), 0
        )).where(
            self.model.paid_at.between(start, end),
            self.model.deleted_at.is_(None)
        )
        return float(await self.session.scalar(stmt))

    async def get_recent(self, limit: int = 5) -> list[Payment]:
        """Fetch the most recent payments system-wide (for dashboard 'recent' widget)."""
        stmt = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .options(selectinload(self.model.project))
            .order_by(self.model.paid_at.desc())
            .limit(limit)
        )
        return (await self.session.scalars(stmt)).all()

    async def get_last_for_project(self, project_id: UUID) -> Payment | None:
        """Fetch the most recent payment for a given project."""
        stmt = select(self.model).where(
            self.model.project_id == project_id,
            self.model.deleted_at.is_(None)
            ).order_by(self.model.paid_at.desc()).limit(1)
        return await self.session.scalar(stmt)
