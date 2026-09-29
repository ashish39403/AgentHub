from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.agent import AgentCreate, AgentListResponse, AgentResponse, AgentUpdate
from app.services.agent_service import (
    AgentNotFoundError,
    create_user_agent,
    delete_user_agent,
    get_user_agent,
    list_user_agents,
    update_user_agent,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def agent_not_found_error(exc: AgentNotFoundError) -> AppHTTPException:
    return AppHTTPException(status_code=404, code="agent_not_found", message=str(exc))


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, session: DbSession, current_user: CurrentUser) -> AgentResponse:
    try:
        return await create_user_agent(session, user=current_user, payload=payload)
    except ValueError as exc:
        raise AppHTTPException(status_code=422, code="invalid_tool_config", message=str(exc)) from exc


@router.get("", response_model=AgentListResponse)
async def list_agents(session: DbSession, current_user: CurrentUser) -> AgentListResponse:
    agents = await list_user_agents(session, user=current_user)
    return AgentListResponse(agents=agents)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, session: DbSession, current_user: CurrentUser) -> AgentResponse:
    try:
        return await get_user_agent(session, user=current_user, agent_id=agent_id)
    except AgentNotFoundError as exc:
        raise agent_not_found_error(exc) from exc


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> AgentResponse:
    try:
        return await update_user_agent(session, user=current_user, agent_id=agent_id, payload=payload)
    except AgentNotFoundError as exc:
        raise agent_not_found_error(exc) from exc
    except ValueError as exc:
        raise AppHTTPException(status_code=422, code="invalid_tool_config", message=str(exc)) from exc


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: UUID, session: DbSession, current_user: CurrentUser) -> None:
    try:
        await delete_user_agent(session, user=current_user, agent_id=agent_id)
    except AgentNotFoundError as exc:
        raise agent_not_found_error(exc) from exc
