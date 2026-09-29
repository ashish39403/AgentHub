from uuid import UUID

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
    error: str | None = None,
) -> ToolActionLog:
    log = ToolActionLog(
        user_id=user_id,
        agent_id=agent_id,
        tool_name=tool_name,
        input=input,
        output=output,
        status=status,
        error=error,
    )
    session.add(log)
    await session.flush()
    return log
