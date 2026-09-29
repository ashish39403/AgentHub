from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.tool import AgentToolsResponse, AgentToolsUpdate, ToolListResponse, ToolResponse
from app.services.agent_service import AgentNotFoundError, get_user_agent, normalize_enabled_tools
from app.tools.registry import get_tool_registry


def list_available_tools() -> ToolListResponse:
    registry = get_tool_registry()
    return ToolListResponse(tools=[ToolResponse(**tool.model_dump()) for tool in registry.definitions()])


async def get_agent_tools(session: AsyncSession, *, user: User, agent_id: UUID) -> AgentToolsResponse:
    agent = await get_user_agent(session, user=user, agent_id=agent_id)
    registry = get_tool_registry()
    enabled_tools = agent.enabled_tools or []
    return AgentToolsResponse(
        agent_id=str(agent.id),
        enabled_tools=enabled_tools,
        tools=[ToolResponse(**tool.model_dump()) for tool in registry.definitions(enabled_tools)],
    )


async def update_agent_tools(
    session: AsyncSession,
    *,
    user: User,
    agent_id: UUID,
    payload: AgentToolsUpdate,
) -> AgentToolsResponse:
    agent = await get_user_agent(session, user=user, agent_id=agent_id)
    agent.enabled_tools = normalize_enabled_tools(payload.enabled_tools)
    await session.commit()
    await session.refresh(agent)
    return await get_agent_tools(session, user=user, agent_id=agent_id)


__all__ = ["AgentNotFoundError", "get_agent_tools", "list_available_tools", "update_agent_tools"]
