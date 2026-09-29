from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoutineRunStatus
from app.models.routine_run import RoutineRun


async def create_routine_run(
    session: AsyncSession,
    *,
    user_id: UUID,
    routine_id: UUID,
    agent_id: UUID,
    status: RoutineRunStatus,
    started_at: datetime,
) -> RoutineRun:
    routine_run = RoutineRun(
        user_id=user_id,
        routine_id=routine_id,
        agent_id=agent_id,
        status=status,
        started_at=started_at,
    )
    session.add(routine_run)
    await session.flush()
    return routine_run


async def list_runs_for_routine(
    session: AsyncSession,
    *,
    user_id: UUID,
    routine_id: UUID,
) -> list[RoutineRun]:
    result = await session.execute(
        select(RoutineRun)
        .where(RoutineRun.user_id == user_id, RoutineRun.routine_id == routine_id)
        .order_by(RoutineRun.started_at.desc())
    )
    return list(result.scalars().all())
