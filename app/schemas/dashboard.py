"""Dashboard aggregate statistics response schemas."""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.payment import PaymentListItemResponse
from app.schemas.project import ProjectListItemResponse
from app.schemas.user import UserListItemResponse


class DashboardStatsResponse(BaseModel):
    """Top-level counters shown on the dashboard's stat cards."""
    users_count: int
    projects_count: int
    active_projects_count: int
    finished_projects_count: int
    stopped_projects_count: int
    bad_projects_count: int
    total_payments_amount: float
    this_month_payments_amount: float


class DashboardRecentResponse(BaseModel):
    """Recent-activity lists shown on the dashboard."""
    recent_users: list[UserListItemResponse]
    recent_projects: list[ProjectListItemResponse]
    recent_payments: list[PaymentListItemResponse]


class DashboardOverviewResponse(BaseModel):
    """Combined dashboard payload: stats + recent activity in a single call."""
    stats: DashboardStatsResponse
    recent: DashboardRecentResponse
