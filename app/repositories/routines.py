from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.routine import Routine


async def create_routine(
    session: AsyncSession,
    *,
    user_id: UUID,
    agent_id: UUID,
    name: str,
    prompt: str,
    schedule: str,
    timezone: str,
    is_active: bool,
) -> Routine:
    routine = Routine(
        user_id=user_id,
        agent_id=agent_id,
        name=name,
        prompt=prompt,
        schedule=schedule,
        timezone=timezone,
        is_active=is_active,
    )
    session.add(routine)
    await session.flush()
    return routine


async def list_routines_for_user(session: AsyncSession, user_id: UUID) -> list[Routine]:
    result = await session.execute(select(Routine).where(Routine.user_id == user_id).order_by(Routine.created_at.desc()))
    return list(result.scalars().all())


async def get_routine_for_user(session: AsyncSession, *, routine_id: UUID, user_id: UUID) -> Routine | None:
    result = await session.execute(select(Routine).where(Routine.id == routine_id, Routine.user_id == user_id))
    return result.scalar_one_or_none()


async def delete_routine(session: AsyncSession, routine: Routine) -> None:
    await session.delete(routine)
    await session.flush()
