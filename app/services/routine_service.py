from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.loop import AgentLoopMaxIterationsError, run_agent_loop
from app.models.enums import RoutineRunStatus
from app.models.routine import Routine
from app.models.routine_run import RoutineRun
from app.models.user import User
from app.repositories import conversations as conversation_repository
from app.repositories import routine_runs as routine_run_repository
from app.repositories import routines as routine_repository
from app.schemas.message import MessageCreate
from app.schemas.routine import RoutineCreate, RoutineUpdate
from app.services.agent_service import AgentNotFoundError, get_user_agent


class RoutineNotFoundError(ValueError):
    pass


async def create_user_routine(session: AsyncSession, *, user: User, payload: RoutineCreate) -> Routine:
    await get_user_agent(session, user=user, agent_id=payload.agent_id)
    routine = await routine_repository.create_routine(
        session,
        user_id=user.id,
        agent_id=payload.agent_id,
        name=payload.name.strip(),
        prompt=payload.prompt.strip(),
        schedule=payload.schedule.strip(),
        timezone=payload.timezone.strip(),
        is_active=payload.is_active,
    )
    await session.commit()
    await session.refresh(routine)
    return routine


async def list_user_routines(session: AsyncSession, *, user: User) -> list[Routine]:
    return await routine_repository.list_routines_for_user(session, user.id)


async def get_user_routine(session: AsyncSession, *, user: User, routine_id: UUID) -> Routine:
    routine = await routine_repository.get_routine_for_user(session, routine_id=routine_id, user_id=user.id)
    if routine is None:
        raise RoutineNotFoundError("Routine not found.")
    return routine


async def update_user_routine(
    session: AsyncSession,
    *,
    user: User,
    routine_id: UUID,
    payload: RoutineUpdate,
) -> Routine:
    routine = await get_user_routine(session, user=user, routine_id=routine_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(routine, field, value)
    await session.commit()
    await session.refresh(routine)
    return routine


async def delete_user_routine(session: AsyncSession, *, user: User, routine_id: UUID) -> None:
    routine = await get_user_routine(session, user=user, routine_id=routine_id)
    await routine_repository.delete_routine(session, routine)
    await session.commit()


async def run_user_routine(session: AsyncSession, *, user: User, routine_id: UUID) -> RoutineRun:
    routine = await get_user_routine(session, user=user, routine_id=routine_id)
    routine_run = await routine_run_repository.create_routine_run(
        session,
        user_id=user.id,
        routine_id=routine.id,
        agent_id=routine.agent_id,
        status=RoutineRunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    await session.commit()
    await session.refresh(routine_run)

    try:
        conversation = await conversation_repository.create_conversation(
            session,
            user_id=user.id,
            agent_id=routine.agent_id,
            title=f"Routine: {routine.name}",
        )
        await session.flush()
        conversation.agent = await get_user_agent(session, user=user, agent_id=routine.agent_id)

        result = await run_agent_loop(
            session,
            user=user,
            conversation=conversation,
            payload=MessageCreate(content=routine.prompt),
        )
        routine_run.status = RoutineRunStatus.SUCCEEDED
        routine_run.output = result.assistant_message.content
        routine_run.finished_at = datetime.now(UTC)
        await session.commit()
    except (AgentLoopMaxIterationsError, Exception) as exc:
        routine_run.status = RoutineRunStatus.FAILED
        routine_run.error = str(exc)
        routine_run.finished_at = datetime.now(UTC)
        await session.commit()

    await session.refresh(routine_run)
    return routine_run


async def list_user_routine_runs(session: AsyncSession, *, user: User, routine_id: UUID) -> list[RoutineRun]:
    await get_user_routine(session, user=user, routine_id=routine_id)
    return await routine_run_repository.list_runs_for_routine(session, user_id=user.id, routine_id=routine_id)


__all__ = [
    "AgentNotFoundError",
    "RoutineNotFoundError",
    "create_user_routine",
    "delete_user_routine",
    "get_user_routine",
    "list_user_routine_runs",
    "list_user_routines",
    "run_user_routine",
    "update_user_routine",
]
