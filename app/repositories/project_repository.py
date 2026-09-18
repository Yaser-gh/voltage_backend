"""Project persistence repository — full implementation."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.constants import ProjectStatus
from app.models.project import Project
from app.models.user import User
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utcnow


class ProjectRepository(BaseRepository[Project]):
    """Data-access methods for the Project aggregate."""

    model = Project

    async def get_by_id(self, entity_id: UUID) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.u_id == entity_id, Project.deleted_at.is_(None))
            .options(selectinload(Project.owner))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: UUID, *, offset: int, limit: int) -> tuple[list[Project], int]:
        """List all projects owned by a specific user."""
        return await self.list(offset=offset, limit=limit, filters={"owner_id": owner_id}, sort_by="created_at")

    async def search(
        self, *, query: str | None, status: ProjectStatus | None, owner_id: UUID | None,
        offset: int, limit: int, sort_by: str | None, sort_order: str,
    ) -> tuple[list[Project], int]:
        """Search/filter/paginate projects by name, address, status, or owner."""
        stmt = select(Project).where(Project.deleted_at.is_(None)).options(selectinload(Project.owner))

        if status is not None:
            stmt = stmt.where(Project.status == status)
        if owner_id is not None:
            stmt = stmt.where(Project.owner_id == owner_id)
        if query:
            like = f"%{query}%"
            from sqlalchemy import or_
            stmt = stmt.where(or_(Project.name.ilike(like), Project.address.ilike(like)))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        sort_column = getattr(Project, sort_by, Project.created_at) if sort_by else Project.created_at
        stmt = stmt.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def update_status(self, project_id: UUID, status: ProjectStatus, reason: str | None = None) -> Project | None:
        """Transition a project's status. `reason` is accepted for future audit-log
        wiring but not yet persisted — add a ProjectStatusHistory table if/when needed."""
        return await self.update(project_id, status=status)

    async def recalculate_total_paid(self, project_id: UUID) -> Project | None:
        """Recompute and persist `total_paid` from the sum of related (non-deleted) payments."""
        from app.models.payment import Payment

        sum_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.project_id == project_id, Payment.deleted_at.is_(None)
        )
        total = (await self.session.execute(sum_stmt)).scalar_one()
        return await self.update(project_id, total_paid=total)

    async def count_by_status(self) -> dict[str, int]:
        """Count all non-deleted projects grouped by status (for dashboard widgets)."""
        stmt = (
            select(Project.status, func.count())
            .where(Project.deleted_at.is_(None))
            .group_by(Project.status)
        )
        result = await self.session.execute(stmt)
        return {status: count for status, count in result.all()}

    async def get_recent(self, limit: int = 5) -> list[Project]:
        """Fetch the most recently created projects (for dashboard 'recent' widget)."""
        stmt = (
            select(Project)
            .where(Project.deleted_at.is_(None))
            .options(selectinload(Project.owner))
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
