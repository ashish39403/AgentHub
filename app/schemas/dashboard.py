from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    agents_count: int
    active_routines_count: int
    total_routine_runs_count: int
    succeeded_routine_runs_count: int
    failed_routine_runs_count: int
    pending_action_items_count: int
    connected_integrations_count: int
    last_run_at: datetime | None


class DashboardRecentRun(BaseModel):
    id: UUID
    routine_id: UUID
    routine_name: str
    agent_id: UUID
    agent_name: str
    status: str
    output_preview: str | None
    error: str | None
    started_at: datetime
    finished_at: datetime | None


class DashboardRecentRunsResponse(BaseModel):
    runs: list[DashboardRecentRun]


class DashboardAgentActivity(BaseModel):
    id: UUID
    agent_id: UUID
    agent_name: str
    conversation_id: UUID
    role: str
    content_preview: str
    created_at: datetime


class DashboardAgentActivityResponse(BaseModel):
    activities: list[DashboardAgentActivity]


class DashboardActionItem(BaseModel):
    id: UUID
    agent_id: UUID
    agent_name: str
    tool_name: str
    title: str
    status: str
    requires_confirmation: bool
    created_at: datetime


class DashboardActionItemsResponse(BaseModel):
    action_items: list[DashboardActionItem]
