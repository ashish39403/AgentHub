from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.user import User
from app.repositories import agents as agent_repository
from app.schemas.agent import AgentCreate, AgentUpdate
from app.tools.registry import get_tool_registry

DEFAULT_AGENT_TOOLS = ["datetime"]


class AgentNotFoundError(ValueError):
    pass


async def create_user_agent(session: AsyncSession, *, user: User, payload: AgentCreate) -> Agent:
    enabled_tools = normalize_enabled_tools(payload.enabled_tools)
    agent = await agent_repository.create_agent(
        session,
        user_id=user.id,
        name=payload.name.strip(),
        instructions=payload.instructions.strip(),
        objective=payload.objective.strip(),
        enabled_tools=enabled_tools,
    )
    await session.commit()
    await session.refresh(agent)
    return agent


async def list_user_agents(session: AsyncSession, *, user: User) -> list[Agent]:
    return await agent_repository.list_agents_for_user(session, user.id)


async def get_user_agent(session: AsyncSession, *, user: User, agent_id: UUID) -> Agent:
    agent = await agent_repository.get_agent_for_user(session, agent_id=agent_id, user_id=user.id)
    if agent is None:
        raise AgentNotFoundError("Agent not found.")
    return agent


async def update_user_agent(session: AsyncSession, *, user: User, agent_id: UUID, payload: AgentUpdate) -> Agent:
    agent = await get_user_agent(session, user=user, agent_id=agent_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "enabled_tools":
            value = normalize_enabled_tools(value)
        setattr(agent, field, value)

    await session.commit()
    await session.refresh(agent)
    return agent


async def delete_user_agent(session: AsyncSession, *, user: User, agent_id: UUID) -> None:
    agent = await get_user_agent(session, user=user, agent_id=agent_id)
    await agent_repository.delete_agent(session, agent)
    await session.commit()


def normalize_enabled_tools(enabled_tools: list[str] | None) -> list[str]:
    if enabled_tools is None:
        return DEFAULT_AGENT_TOOLS.copy()

    available_tool_names = {tool.name for tool in get_tool_registry().definitions()}
    normalized: list[str] = []
    for tool_name in enabled_tools:
        clean_tool_name = tool_name.strip()
        if clean_tool_name not in available_tool_names:
            raise ValueError(f"Unknown tool: {clean_tool_name}")
        if clean_tool_name not in normalized:
            normalized.append(clean_tool_name)
    return normalized
