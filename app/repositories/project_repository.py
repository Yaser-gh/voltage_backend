"""Project persistence repository. Query bodies are TODO per project scope."""
from __future__ import annotations

from uuid import UUID

from app.core.constants import ProjectStatus
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Data-access methods for the Project aggregate."""

    model = Project

    async def get_by_owner(self, owner_id: UUID, *, offset: int, limit: int) -> tuple[list[Project], int]:
        """List all projects owned by a specific user.

        TODO: implement with `select(Project).where(Project.owner_id == owner_id,
        Project.deleted_at.is_(None))`.
        """
        raise NotImplementedError

    async def search(
        self, *, query: str | None, status: ProjectStatus | None, owner_id: UUID | None,
        offset: int, limit: int, sort_by: str | None, sort_order: str,
    ) -> tuple[list[Project], int]:
        """Search/filter/paginate projects by name, address, status, or owner.

        TODO: implement with `.ilike()` across name/address, equality filters
        for status/owner_id, joined with the owner for eager loading.
        """
        raise NotImplementedError

    async def update_status(self, project_id: UUID, status: ProjectStatus, reason: str | None = None) -> Project | None:
        """Transition a project's status (start/stop/finish/mark-bad/restore).

        TODO: implement as a targeted UPDATE statement on Project.status, and
        optionally persist `reason` to an audit/history table.
        """
        raise NotImplementedError

    async def recalculate_total_paid(self, project_id: UUID) -> Project | None:
        """Recompute and persist `total_paid` from the sum of related payments.

        TODO: implement via `select(func.sum(Payment.amount)).where(
        Payment.project_id == project_id)` followed by an UPDATE.
        """
        raise NotImplementedError

    async def count_by_status(self) -> dict[str, int]:
        """Count all projects grouped by status (for dashboard widgets).

        TODO: implement via `select(Project.status, func.count()).group_by(Project.status)`.
        """
        raise NotImplementedError

    async def get_recent(self, limit: int = 5) -> list[Project]:
        """Fetch the most recently created projects (for dashboard 'recent' widget).

        TODO: implement with `.order_by(Project.created_at.desc()).limit(limit)`.
        """
        raise NotImplementedError
