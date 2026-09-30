from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent


async def create_agent(
    session: AsyncSession,
    *,
    user_id: UUID,
    name: str,
    instructions: str,
    objective: str,
    model: str,
    temperature: float,
    enabled_tools: list[str],
) -> Agent:
    agent = Agent(
        user_id=user_id,
        name=name,
        instructions=instructions,
        objective=objective,
        model=model,
        temperature=temperature,
        enabled_tools=enabled_tools,
    )
    session.add(agent)
    await session.flush()
    return agent


async def list_agents_for_user(session: AsyncSession, user_id: UUID) -> list[Agent]:
    result = await session.execute(select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


async def get_agent_for_user(session: AsyncSession, *, agent_id: UUID, user_id: UUID) -> Agent | None:
    result = await session.execute(select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id))
    return result.scalar_one_or_none()


async def delete_agent(session: AsyncSession, agent: Agent) -> None:
    await session.delete(agent)
    await session.flush()
