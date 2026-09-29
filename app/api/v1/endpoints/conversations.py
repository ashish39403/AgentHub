from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.agent_run import AgentRunRequest, AgentRunResponse
from app.schemas.conversation import ConversationCreate, ConversationDetailResponse, ConversationListResponse, ConversationResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.services.conversation_service import AgentLoopMaxIterationsError
from app.services.agent_service import AgentNotFoundError
from app.services.conversation_service import (
    ConversationNotFoundError,
    create_user_conversation,
    create_user_message,
    get_user_conversation,
    list_user_agent_conversations,
    run_user_conversation_agent,
)

router = APIRouter(tags=["conversations"])


def not_found_error(exc: Exception, *, code: str) -> AppHTTPException:
    return AppHTTPException(status_code=404, code=code, message=str(exc))


@router.post("/agents/{agent_id}/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    agent_id: UUID,
    payload: ConversationCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> ConversationResponse:
    try:
        return await create_user_conversation(session, user=current_user, agent_id=agent_id, payload=payload)
    except AgentNotFoundError as exc:
        raise not_found_error(exc, code="agent_not_found") from exc


@router.get("/agents/{agent_id}/conversations", response_model=ConversationListResponse)
async def list_conversations(
    agent_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> ConversationListResponse:
    try:
        conversations = await list_user_agent_conversations(session, user=current_user, agent_id=agent_id)
    except AgentNotFoundError as exc:
        raise not_found_error(exc, code="agent_not_found") from exc

    return ConversationListResponse(conversations=conversations)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> ConversationDetailResponse:
    try:
        return await get_user_conversation(session, user=current_user, conversation_id=conversation_id)
    except ConversationNotFoundError as exc:
        raise not_found_error(exc, code="conversation_not_found") from exc


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: UUID,
    payload: MessageCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> MessageResponse:
    try:
        return await create_user_message(session, user=current_user, conversation_id=conversation_id, payload=payload)
    except ConversationNotFoundError as exc:
        raise not_found_error(exc, code="conversation_not_found") from exc


@router.post("/conversations/{conversation_id}/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def run_agent(
    conversation_id: UUID,
    payload: AgentRunRequest,
    session: DbSession,
    current_user: CurrentUser,
) -> AgentRunResponse:
    try:
        result = await run_user_conversation_agent(
            session,
            user=current_user,
            conversation_id=conversation_id,
            payload=payload,
        )
    except ConversationNotFoundError as exc:
        raise not_found_error(exc, code="conversation_not_found") from exc
    except AgentLoopMaxIterationsError as exc:
        raise AppHTTPException(status_code=409, code="agent_max_iterations", message=str(exc)) from exc

    return AgentRunResponse(
        user_message=result.user_message,
        assistant_message=result.assistant_message,
        tool_messages=result.tool_messages,
    )
