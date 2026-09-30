from collections.abc import Generator
import asyncio
from uuid import uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agents.types import AgentRuntimeMessage, LLMResponse, ToolCall, ToolDefinition
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app


class TestLLMClient:
    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        last_message = messages[-1]
        if last_message.role == "tool":
            return LLMResponse(content=f"I used {last_message.name} and found this result: {last_message.content}")

        latest_user_message = next((message for message in reversed(messages) if message.role == "user"), None)
        if latest_user_message is None:
            return LLMResponse(content="I need a user message before I can help.")

        content = latest_user_message.content.lower()
        available_tool_names = {tool.name for tool in tools}

        if ("web search" in content or "search" in content) and "web_search" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="web_search", arguments={"query": latest_user_message.content}))
        if ("summarize" in content or "summary" in content) and "summarize_text" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="summarize_text", arguments={"text": latest_user_message.content}))
        if ("save" in content or "remember" in content) and "save_memory" in available_tool_names:
            return LLMResponse(
                tool_call=ToolCall(
                    name="save_memory",
                    arguments={"title": "Saved note", "content": latest_user_message.content},
                )
            )
        if ("saved" in content or "memory" in content) and "get_memory" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="get_memory", arguments={"limit": 10}))
        if ("gmail" in content or "email" in content) and "gmail_summary" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="gmail_summary", arguments={"max_emails": 5}))
        if ("slack" in content and "send" in content) and "send_slack_message" in available_tool_names:
            return LLMResponse(
                tool_call=ToolCall(
                    name="send_slack_message",
                    arguments={"channel": "#general", "message": latest_user_message.content},
                )
            )
        if ("draft" in content or "message" in content or "remind" in content) and "draft_message" in available_tool_names:
            return LLMResponse(
                tool_call=ToolCall(
                    name="draft_message",
                    arguments={"recipient": "there", "purpose": latest_user_message.content, "tone": "professional"},
                )
            )
        if ("time" in content or "date" in content) and "datetime" in available_tool_names:
            return LLMResponse(tool_call=ToolCall(name="datetime", arguments={}))

        return LLMResponse(content=latest_user_message.content)


@pytest.fixture(autouse=True)
def use_test_llm_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agents.loop.get_llm_client", lambda **_: TestLLMClient())


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


async def _create_test_database(database_name: str) -> None:
    conn = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
    await conn.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = $1 AND pid <> pg_backend_pid()
        """,
        database_name,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
    await conn.execute(f'CREATE DATABASE "{database_name}"')
    await conn.close()


async def _drop_test_database(database_name: str) -> None:
    conn = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
    await conn.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = $1 AND pid <> pg_backend_pid()
        """,
        database_name,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
    await conn.close()


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    database_name = f"agenthub_test_{uuid4().hex}"
    database_url = f"postgresql+asyncpg://agenthub:agenthub@127.0.0.1:5433/{database_name}"

    asyncio.run(_create_test_database(database_name))

    engine = create_async_engine(database_url, poolclass=NullPool)
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose_engine() -> None:
        await engine.dispose()

    asyncio.run(create_schema())

    async def override_get_db_session():
        async with TestingSessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        asyncio.run(dispose_engine())
        asyncio.run(_drop_test_database(database_name))
