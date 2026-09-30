from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ToolActionStatus
from app.models.tool_action_log import ToolActionLog


async def create_tool_action_log(
    session: AsyncSession,
    *,
    user_id: UUID,
    agent_id: UUID,
    tool_name: str,
    input: dict,
    output: dict | None,
    status: ToolActionStatus,
    routine_run_id: UUID | None = None,
    error: str | None = None,
) -> ToolActionLog:
    log = ToolActionLog(
        user_id=user_id,
        agent_id=agent_id,
        routine_run_id=routine_run_id,
        tool_name=tool_name,
        input=input,
        output=output,
        status=status,
        error=error,
    )
    session.add(log)
    await session.flush()
    return log


async def list_logs_for_routine_run(
    session: AsyncSession,
    *,
    user_id: UUID,
    routine_run_id: UUID,
) -> list[ToolActionLog]:
    result = await session.execute(
        select(ToolActionLog)
        .where(ToolActionLog.user_id == user_id, ToolActionLog.routine_run_id == routine_run_id)
        .order_by(ToolActionLog.created_at.asc())
    )
    return list(result.scalars().all())
