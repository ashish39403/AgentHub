from pydantic import BaseModel

from app.schemas.message import MessageCreate, MessageResponse


class AgentRunRequest(MessageCreate):
    pass


class AgentRunResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    tool_messages: list[MessageResponse]
