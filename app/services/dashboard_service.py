from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.enums import RoutineRunStatus, ToolActionStatus
from app.models.message import Message
from app.models.routine import Routine
from app.models.routine_run import RoutineRun
from app.models.tool_action_log import ToolActionLog
from app.models.user import User
from app.schemas.dashboard import (
    DashboardActionItem,
    DashboardActionItemsResponse,
    DashboardAgentActivity,
    DashboardAgentActivityResponse,
    DashboardRecentRun,
    DashboardRecentRunsResponse,
    DashboardSummaryResponse,
)


PREVIEW_LENGTH = 180


async def get_dashboard_summary(session: AsyncSession, *, user: User) -> DashboardSummaryResponse:
    agents_count = await count_rows(session, select(func.count()).select_from(Agent).where(Agent.user_id == user.id))
    active_routines_count = await count_rows(
        session,
        select(func.count()).select_from(Routine).where(Routine.user_id == user.id, Routine.is_active.is_(True)),
    )
    total_runs_count = await count_rows(
        session,
        select(func.count()).select_from(RoutineRun).where(RoutineRun.user_id == user.id),
    )
    succeeded_runs_count = await count_rows(
        session,
        select(func.count())
        .select_from(RoutineRun)
        .where(RoutineRun.user_id == user.id, RoutineRun.status == RoutineRunStatus.SUCCEEDED),
    )
    failed_runs_count = await count_rows(
        session,
        select(func.count())
        .select_from(RoutineRun)
        .where(RoutineRun.user_id == user.id, RoutineRun.status == RoutineRunStatus.FAILED),
    )
    pending_action_items_count = len(await build_action_items(session, user_id=user.id, limit=100))
    last_run_at = await session.scalar(
        select(func.max(RoutineRun.started_at)).where(RoutineRun.user_id == user.id)
    )

    return DashboardSummaryResponse(
        agents_count=agents_count,
        active_routines_count=active_routines_count,
        total_routine_runs_count=total_runs_count,
        succeeded_routine_runs_count=succeeded_runs_count,
        failed_routine_runs_count=failed_runs_count,
        pending_action_items_count=pending_action_items_count,
        last_run_at=last_run_at,
    )


async def get_recent_runs(
    session: AsyncSession,
    *,
    user: User,
    limit: int = 10,
) -> DashboardRecentRunsResponse:
    result = await session.execute(
        select(RoutineRun, Routine, Agent)
        .join(Routine, RoutineRun.routine_id == Routine.id)
        .join(Agent, RoutineRun.agent_id == Agent.id)
        .where(RoutineRun.user_id == user.id)
        .order_by(desc(RoutineRun.started_at))
        .limit(limit)
    )

    runs = [
        DashboardRecentRun(
            id=run.id,
            routine_id=routine.id,
            routine_name=routine.name,
            agent_id=agent.id,
            agent_name=agent.name,
            status=run.status.value,
            output_preview=preview(run.output),
            error=run.error,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run, routine, agent in result.all()
    ]
    return DashboardRecentRunsResponse(runs=runs)


async def get_recent_agent_activity(
    session: AsyncSession,
    *,
    user: User,
    limit: int = 10,
) -> DashboardAgentActivityResponse:
    result = await session.execute(
        select(Message, Conversation, Agent)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(Agent, Conversation.agent_id == Agent.id)
        .where(Conversation.user_id == user.id)
        .order_by(desc(Message.created_at))
        .limit(limit)
    )

    activities = [
        DashboardAgentActivity(
            id=message.id,
            agent_id=agent.id,
            agent_name=agent.name,
            conversation_id=conversation.id,
            role=message.role.value,
            content_preview=preview(message.content) or "",
            created_at=message.created_at,
        )
        for message, conversation, agent in result.all()
    ]
    return DashboardAgentActivityResponse(activities=activities)


async def get_action_items(
    session: AsyncSession,
    *,
    user: User,
    limit: int = 10,
) -> DashboardActionItemsResponse:
    return DashboardActionItemsResponse(action_items=await build_action_items(session, user_id=user.id, limit=limit))


async def count_rows(session: AsyncSession, statement) -> int:
    value = await session.scalar(statement)
    return int(value or 0)


async def build_action_items(session: AsyncSession, *, user_id: UUID, limit: int) -> list[DashboardActionItem]:
    result = await session.execute(
        select(ToolActionLog, Agent)
        .join(Agent, ToolActionLog.agent_id == Agent.id)
        .where(ToolActionLog.user_id == user_id)
        .order_by(desc(ToolActionLog.created_at))
        .limit(limit * 3)
    )

    action_items: list[DashboardActionItem] = []
    for log, agent in result.all():
        output = log.output or {}
        requires_confirmation = bool(output.get("requires_confirmation")) or output.get("status") in {
            "confirmation_required",
            "blocked",
        }
        has_action_items = isinstance(output.get("action_items"), list) and bool(output["action_items"])
        failed = log.status == ToolActionStatus.FAILED
        if not (requires_confirmation or has_action_items or failed):
            continue

        action_items.append(
            DashboardActionItem(
                id=log.id,
                agent_id=agent.id,
                agent_name=agent.name,
                tool_name=log.tool_name,
                title=action_item_title(log.tool_name, output, failed=failed),
                status=str(output.get("status") or log.status.value),
                requires_confirmation=requires_confirmation,
                created_at=log.created_at,
            )
        )
        if len(action_items) >= limit:
            break

    return action_items


def preview(value: str | None) -> str | None:
    if value is None:
        return None
    clean_value = " ".join(value.split())
    if len(clean_value) <= PREVIEW_LENGTH:
        return clean_value
    return f"{clean_value[: PREVIEW_LENGTH - 3]}..."


def action_item_title(tool_name: str, output: dict, *, failed: bool) -> str:
    if failed:
        return f"{tool_name} needs attention"
    if output.get("reason"):
        return str(output["reason"])
    if output.get("message"):
        return str(output["message"])
    action_items = output.get("action_items")
    if isinstance(action_items, list) and action_items:
        return str(action_items[0])
    return f"{tool_name} produced an action item"
