from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.routine import RoutineCreate, RoutineListResponse, RoutineResponse, RoutineUpdate
from app.schemas.routine_run import RoutineRunListResponse, RoutineRunResponse
from app.schemas.tool_action_log import ToolActionLogListResponse
from app.services.agent_service import AgentNotFoundError
from app.services.routine_service import (
    RoutineNotFoundError,
    create_user_routine,
    delete_user_routine,
    get_user_routine,
    get_user_routine_run,
    list_user_routine_run_tool_logs,
    list_user_routine_runs,
    list_user_routines,
    run_user_routine,
    update_user_routine,
)

router = APIRouter(prefix="/routines", tags=["routines"])


def routine_not_found_error(exc: Exception, *, code: str = "routine_not_found") -> AppHTTPException:
    return AppHTTPException(status_code=404, code=code, message=str(exc))


@router.post("", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED)
async def create_routine(payload: RoutineCreate, session: DbSession, current_user: CurrentUser) -> RoutineResponse:
    try:
        return await create_user_routine(session, user=current_user, payload=payload)
    except AgentNotFoundError as exc:
        raise routine_not_found_error(exc, code="agent_not_found") from exc


@router.get("", response_model=RoutineListResponse)
async def list_routines(session: DbSession, current_user: CurrentUser) -> RoutineListResponse:
    routines = await list_user_routines(session, user=current_user)
    return RoutineListResponse(routines=routines)


@router.get("/{routine_id}", response_model=RoutineResponse)
async def get_routine(routine_id: UUID, session: DbSession, current_user: CurrentUser) -> RoutineResponse:
    try:
        return await get_user_routine(session, user=current_user, routine_id=routine_id)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc) from exc


@router.patch("/{routine_id}", response_model=RoutineResponse)
async def update_routine(
    routine_id: UUID,
    payload: RoutineUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> RoutineResponse:
    try:
        return await update_user_routine(session, user=current_user, routine_id=routine_id, payload=payload)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc) from exc


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(routine_id: UUID, session: DbSession, current_user: CurrentUser) -> None:
    try:
        await delete_user_routine(session, user=current_user, routine_id=routine_id)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc) from exc


@router.post("/{routine_id}/run", response_model=RoutineRunResponse, status_code=status.HTTP_201_CREATED)
async def run_routine(routine_id: UUID, session: DbSession, current_user: CurrentUser) -> RoutineRunResponse:
    try:
        return await run_user_routine(session, user=current_user, routine_id=routine_id)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc) from exc


@router.get("/{routine_id}/runs", response_model=RoutineRunListResponse)
async def list_routine_runs(
    routine_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> RoutineRunListResponse:
    try:
        runs = await list_user_routine_runs(session, user=current_user, routine_id=routine_id)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc) from exc

    return RoutineRunListResponse(runs=runs)


@router.get("/{routine_id}/runs/{run_id}", response_model=RoutineRunResponse)
async def get_routine_run(
    routine_id: UUID,
    run_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> RoutineRunResponse:
    try:
        return await get_user_routine_run(session, user=current_user, routine_id=routine_id, run_id=run_id)
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc, code="routine_run_not_found") from exc


@router.get("/{routine_id}/runs/{run_id}/tool-logs", response_model=ToolActionLogListResponse)
async def list_routine_run_tool_logs(
    routine_id: UUID,
    run_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> ToolActionLogListResponse:
    try:
        logs = await list_user_routine_run_tool_logs(
            session,
            user=current_user,
            routine_id=routine_id,
            run_id=run_id,
        )
    except RoutineNotFoundError as exc:
        raise routine_not_found_error(exc, code="routine_run_not_found") from exc

    return ToolActionLogListResponse(tool_logs=logs)
