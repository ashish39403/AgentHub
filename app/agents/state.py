from uuid import UUID

from app.agents.types import AgentRunState, AgentRuntimeMessage
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.message import MessageCreate


def create_agent_run_state(
    *,
    user: User,
    conversation: Conversation,
    payload: MessageCreate,
    runtime_messages: list[AgentRuntimeMessage],
    selected_model: str,
    routine_run_id: UUID | None,
) -> AgentRunState:
    input_message = payload.content.strip()
    runtime_messages.append(AgentRuntimeMessage(role="user", content=input_message))
    return AgentRunState(
        user_id=user.id,
        agent_id=conversation.agent_id,
        conversation_id=conversation.id,
        routine_run_id=routine_run_id,
        input_message=input_message,
        selected_model=selected_model,
        enabled_tools=conversation.agent.enabled_tools or [],
        runtime_messages=runtime_messages,
    )
