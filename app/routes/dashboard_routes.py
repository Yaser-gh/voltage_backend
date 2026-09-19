"""Dashboard aggregate statistics endpoints."""
# from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db_session
from app.permissions.checker import RequirePermission
from app.permissions.roles import Permission
from app.responses.envelope import SuccessResponse
from app.schemas.dashboard import DashboardOverviewResponse, DashboardRecentResponse, DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=SuccessResponse[DashboardStatsResponse],
    summary="Get dashboard summary statistics",
    description="Counts of users/projects by status, plus total and this-month payment sums.",
    dependencies=[Depends(RequirePermission(Permission.DASHBOARD_READ))],
)
async def get_dashboard_stats(session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[DashboardStatsResponse]:
    service = DashboardService(session)
    stats = await service.get_stats()
    return SuccessResponse(data=stats)


@router.get(
    "/recent",
    response_model=SuccessResponse[DashboardRecentResponse],
    summary="Get recent activity (users, projects, payments)",
    dependencies=[Depends(RequirePermission(Permission.DASHBOARD_READ))],
)
async def get_dashboard_recent(limit: int = 5, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[DashboardRecentResponse]:
    service = DashboardService(session)
    recent = await service.get_recent(limit)
    return SuccessResponse(data=recent)


@router.post(
    "/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Get combined dashboard stats + recent activity in one call",
    dependencies=[Depends(RequirePermission(Permission.DASHBOARD_READ))],
)
async def get_dashboard_overview(limit: int = 5, session: AsyncSession = Depends(get_db_session)) -> SuccessResponse[DashboardOverviewResponse]:
    service = DashboardService(session)
    overview = await service.get_overview(limit)
    return SuccessResponse(data=overview)
