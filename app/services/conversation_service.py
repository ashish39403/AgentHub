from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.loop import AgentLoopMaxIterationsError, AgentLoopResult, run_agent_loop
from app.models.conversation import Conversation
from app.models.enums import MessageRole
from app.models.message import Message
from app.models.user import User
from app.repositories import conversations as conversation_repository
from app.schemas.conversation import ConversationCreate
from app.schemas.message import MessageCreate
from app.services.agent_service import AgentNotFoundError, get_user_agent


class ConversationNotFoundError(ValueError):
    pass


async def create_user_conversation(
    session: AsyncSession,
    *,
    user: User,
    agent_id: UUID,
    payload: ConversationCreate,
) -> Conversation:
    await get_user_agent(session, user=user, agent_id=agent_id)
    conversation = await conversation_repository.create_conversation(
        session,
        user_id=user.id,
        agent_id=agent_id,
        title=payload.title.strip() if payload.title else None,
    )
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def list_user_agent_conversations(session: AsyncSession, *, user: User, agent_id: UUID) -> list[Conversation]:
    await get_user_agent(session, user=user, agent_id=agent_id)
    return await conversation_repository.list_conversations_for_agent(session, user_id=user.id, agent_id=agent_id)


async def get_user_conversation(session: AsyncSession, *, user: User, conversation_id: UUID) -> Conversation:
    conversation = await conversation_repository.get_conversation_for_user(
        session,
        conversation_id=conversation_id,
        user_id=user.id,
    )
    if conversation is None:
        raise ConversationNotFoundError("Conversation not found.")
    conversation.messages.sort(key=lambda message: message.created_at)
    return conversation


async def create_user_message(
    session: AsyncSession,
    *,
    user: User,
    conversation_id: UUID,
    payload: MessageCreate,
) -> Message:
    conversation = await get_user_conversation(session, user=user, conversation_id=conversation_id)
    message = await conversation_repository.create_message(
        session,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=payload.content.strip(),
    )
    await session.commit()
    await session.refresh(message)
    return message


async def delete_user_conversation(session: AsyncSession, *, user: User, conversation_id: UUID) -> None:
    conversation = await get_user_conversation(session, user=user, conversation_id=conversation_id)
    await conversation_repository.delete_conversation(session, conversation)
    await session.commit()


async def run_user_conversation_agent(
    session: AsyncSession,
    *,
    user: User,
    conversation_id: UUID,
    payload: MessageCreate,
) -> AgentLoopResult:
    conversation = await get_user_conversation(session, user=user, conversation_id=conversation_id)
    return await run_agent_loop(session, user=user, conversation=conversation, payload=payload)


__all__ = [
    "AgentNotFoundError",
    "AgentLoopMaxIterationsError",
    "ConversationNotFoundError",
    "create_user_conversation",
    "create_user_message",
    "delete_user_conversation",
    "get_user_conversation",
    "list_user_agent_conversations",
    "run_user_conversation_agent",
]
