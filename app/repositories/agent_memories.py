from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_memory import AgentMemory


async def create_memory(
    session: AsyncSession,
    *,
    user_id: UUID,
    agent_id: UUID,
    title: str,
    content: str,
    metadata: dict | None = None,
) -> AgentMemory:
    memory = AgentMemory(
        user_id=user_id,
        agent_id=agent_id,
        title=title,
        content=content,
        metadata_=metadata or {},
    )
    session.add(memory)
    await session.flush()
    return memory


async def list_memories(session: AsyncSession, *, user_id: UUID, agent_id: UUID, limit: int = 10) -> list[AgentMemory]:
    result = await session.execute(
        select(AgentMemory)
        .where(AgentMemory.user_id == user_id, AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
