from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.enums import MessageRole
from app.models.message import Message


async def create_conversation(
    session: AsyncSession,
    *,
    user_id: UUID,
    agent_id: UUID,
    title: str | None,
) -> Conversation:
    conversation = Conversation(user_id=user_id, agent_id=agent_id, title=title)
    session.add(conversation)
    await session.flush()
    return conversation


async def list_conversations_for_agent(
    session: AsyncSession,
    *,
    user_id: UUID,
    agent_id: UUID,
) -> list[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.agent_id == agent_id)
        .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation_for_user(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    user_id: UUID,
) -> Conversation | None:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.agent))
    )
    return result.scalar_one_or_none()


async def create_message(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    tool_calls: dict | None = None,
) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content, tool_calls=tool_calls)
    session.add(message)
    await session.flush()
    return message
