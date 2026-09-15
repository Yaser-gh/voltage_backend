"""Dashboard aggregate statistics business logic."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProjectStatus
from app.core.logging import get_logger
from app.repositories.payment_repository import PaymentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dashboard import DashboardOverviewResponse, DashboardRecentResponse, DashboardStatsResponse

logger = get_logger("dashboard_service")


class DashboardService:
    """Aggregates statistics and recent-activity feeds for the dashboard endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.project_repo = ProjectRepository(session)
        self.payment_repo = PaymentRepository(session)

    async def get_stats(self) -> DashboardStatsResponse:
        """Compute the top-level counters shown on the dashboard's stat cards."""
        users_count = await self.user_repo.count()  # TODO
        status_counts = await self.project_repo.count_by_status()  # TODO
        total_payments = await self.payment_repo.get_total_amount()  # TODO
        this_month_payments = await self.payment_repo.get_this_month_total()  # TODO

        return DashboardStatsResponse(
            users_count=users_count,
            projects_count=sum(status_counts.values()) if status_counts else 0,
            active_projects_count=status_counts.get(ProjectStatus.ACTIVE.value, 0) if status_counts else 0,
            finished_projects_count=status_counts.get(ProjectStatus.FINISHED.value, 0) if status_counts else 0,
            stopped_projects_count=status_counts.get(ProjectStatus.STOPPED.value, 0) if status_counts else 0,
            bad_projects_count=status_counts.get(ProjectStatus.BAD.value, 0) if status_counts else 0,
            total_payments_amount=total_payments,
            this_month_payments_amount=this_month_payments,
        )

    async def get_recent(self, limit: int = 5) -> DashboardRecentResponse:
        """Fetch the 'recent users / recent projects / recent payments' widgets."""
        recent_users, _ = await self.user_repo.list(offset=0, limit=limit, sort_by="created_at", sort_order="desc")  # TODO
        recent_projects = await self.project_repo.get_recent(limit)  # TODO
        recent_payments = await self.payment_repo.get_recent(limit)  # TODO

        return DashboardRecentResponse(
            recent_users=recent_users, recent_projects=recent_projects, recent_payments=recent_payments,
        )

    async def get_overview(self, limit: int = 5) -> DashboardOverviewResponse:
        """Combined stats + recent-activity payload for a single dashboard call."""
        stats = await self.get_stats()
        recent = await self.get_recent(limit)
        return DashboardOverviewResponse(stats=stats, recent=recent)
