from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.tool import AgentToolsResponse, AgentToolsUpdate, ToolListResponse
from app.services.agent_service import AgentNotFoundError
from app.services.tool_service import get_agent_tools, list_available_tools, update_agent_tools

router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(_: CurrentUser) -> ToolListResponse:
    return list_available_tools()


@router.get("/agents/{agent_id}/tools", response_model=AgentToolsResponse)
async def get_tools_for_agent(agent_id: UUID, session: DbSession, current_user: CurrentUser) -> AgentToolsResponse:
    try:
        return await get_agent_tools(session, user=current_user, agent_id=agent_id)
    except AgentNotFoundError as exc:
        raise AppHTTPException(status_code=404, code="agent_not_found", message=str(exc)) from exc


@router.put("/agents/{agent_id}/tools", response_model=AgentToolsResponse)
async def update_tools_for_agent(
    agent_id: UUID,
    payload: AgentToolsUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> AgentToolsResponse:
    try:
        return await update_agent_tools(session, user=current_user, agent_id=agent_id, payload=payload)
    except AgentNotFoundError as exc:
        raise AppHTTPException(status_code=404, code="agent_not_found", message=str(exc)) from exc
    except ValueError as exc:
        raise AppHTTPException(status_code=422, code="invalid_tool_config", message=str(exc)) from exc
