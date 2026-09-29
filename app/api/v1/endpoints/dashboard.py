from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import (
    DashboardActionItemsResponse,
    DashboardAgentActivityResponse,
    DashboardRecentRunsResponse,
    DashboardSummaryResponse,
)
from app.services.dashboard_service import (
    get_action_items,
    get_dashboard_summary,
    get_recent_agent_activity,
    get_recent_runs,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(session: DbSession, current_user: CurrentUser) -> DashboardSummaryResponse:
    return await get_dashboard_summary(session, user=current_user)


@router.get("/recent-runs", response_model=DashboardRecentRunsResponse)
async def dashboard_recent_runs(
    session: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
) -> DashboardRecentRunsResponse:
    return await get_recent_runs(session, user=current_user, limit=limit)


@router.get("/recent-activity", response_model=DashboardAgentActivityResponse)
async def dashboard_recent_activity(
    session: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
) -> DashboardAgentActivityResponse:
    return await get_recent_agent_activity(session, user=current_user, limit=limit)


@router.get("/action-items", response_model=DashboardActionItemsResponse)
async def dashboard_action_items(
    session: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
) -> DashboardActionItemsResponse:
    return await get_action_items(session, user=current_user, limit=limit)
