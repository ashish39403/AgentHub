from app.repositories.agent_memories import create_memory, list_memories
from app.tools.context import ToolContext


async def save_memory(context: ToolContext, arguments: dict) -> dict:
    title = str(arguments.get("title", "")).strip()
    content = str(arguments.get("content", "")).strip()
    metadata = arguments.get("metadata") if isinstance(arguments.get("metadata"), dict) else {}
    if not title or not content:
        raise ValueError("title and content are required")

    memory = await create_memory(
        context.session,
        user_id=context.user_id,
        agent_id=context.agent_id,
        title=title,
        content=content,
        metadata=metadata,
    )
    return {
        "id": str(memory.id),
        "title": memory.title,
        "content": memory.content,
        "metadata": memory.metadata_,
    }


async def get_memory(context: ToolContext, arguments: dict) -> dict:
    limit = int(arguments.get("limit", 10))
    memories = await list_memories(context.session, user_id=context.user_id, agent_id=context.agent_id, limit=limit)
    return {
        "memories": [
            {
                "id": str(memory.id),
                "title": memory.title,
                "content": memory.content,
                "metadata": memory.metadata_,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
            }
            for memory in memories
        ]
    }
