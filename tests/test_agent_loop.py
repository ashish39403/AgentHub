import asyncio
from uuid import uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.agents.loop import AgentLoopMaxIterationsError, run_agent_loop
from app.agents.types import AgentRuntimeMessage, LLMResponse, ToolCall, ToolDefinition, ToolExecutionResult
from app.db.base import Base
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.message import MessageCreate


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Agent Loop User",
            "email": email,
            "password": "secure-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "General Assistant",
            "instructions": "Answer clearly and use tools when useful.",
            "objective": "Help the student with productivity tasks.",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client: TestClient, headers: dict[str, str], agent_id: str) -> dict:
    response = client.post(
        f"/api/v1/agents/{agent_id}/conversations",
        json={"title": "Agent loop test"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_agent_run_returns_direct_assistant_message(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="agent-loop-direct@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "Help me plan my application tasks."},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["content"] == "Help me plan my application tasks."
    assert body["tool_messages"] == []


def test_agent_run_executes_tool_and_saves_history(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="agent-loop-tool@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "What is the date and time right now?"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assistant_message"]["role"] == "assistant"
    assert len(body["tool_messages"]) == 1
    assert body["tool_messages"][0]["role"] == "tool"
    assert body["tool_messages"][0]["tool_calls"]["name"] == "datetime"
    assert "datetime" in body["assistant_message"]["content"]

    detail_response = auth_client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers)
    roles = [message["role"] for message in detail_response.json()["messages"]]

    assert roles == ["user", "tool", "assistant"]


class LoopingLLMClient:
    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        return LLMResponse(tool_call=ToolCall(name="datetime", arguments={}))


class SearchAwareFinalLLMClient:
    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        if messages[-1].role == "tool":
            return LLMResponse(content="Here is a fresh summary based on web_search.")
        return LLMResponse(content="I cannot access latest news.")


class ToolOnceThenFinalLLMClient:
    def __init__(self) -> None:
        self.tool_counts: list[int] = []

    async def complete(
        self,
        *,
        messages: list[AgentRuntimeMessage],
        tools: list[ToolDefinition],
    ) -> LLMResponse:
        self.tool_counts.append(len(tools))
        if tools:
            return LLMResponse(tool_call=ToolCall(name="datetime", arguments={}))
        return LLMResponse(content=f"Final answer from {messages[-1].role} output.")


class FakeSearchRegistry:
    def definitions(self, enabled_tools: list[str] | None = None) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="web_search",
                description="Search the web.",
                category="search",
                safety_level="read_only",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            )
        ]

    async def execute(self, name: str, arguments: dict, *, context, enabled_tools: list[str]) -> ToolExecutionResult:
        return ToolExecutionResult(
            name=name,
            input=arguments,
            output={
                "status": "succeeded",
                "headline": "Fresh news headline",
                "results": [{"title": "Fresh news", "url": "https://example.com/news"}],
            },
        )


@pytest.mark.parametrize("max_iterations", [1])
def test_agent_loop_stops_at_max_iterations(max_iterations: int) -> None:
    async def scenario() -> None:
        database_name = f"agenthub_loop_test_{uuid4().hex}"
        admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
        await admin.execute(f'CREATE DATABASE "{database_name}"')
        await admin.close()

        engine = create_async_engine(
            f"postgresql+asyncpg://agenthub:agenthub@127.0.0.1:5433/{database_name}",
            poolclass=NullPool,
        )
        Session = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with Session() as session:
                user = User(name="Loop User", email="loop@example.com", hashed_password="hashed")
                session.add(user)
                await session.flush()
                agent = Agent(
                    user_id=user.id,
                    name="Loop Agent",
                    instructions="Keep helping.",
                    objective="Test loop safety.",
                )
                session.add(agent)
                await session.flush()
                conversation = Conversation(user_id=user.id, agent_id=agent.id, title="Loop")
                conversation.agent = agent
                session.add(conversation)
                await session.flush()

                with pytest.raises(AgentLoopMaxIterationsError):
                    await run_agent_loop(
                        session,
                        user=user,
                        conversation=conversation,
                        payload=MessageCreate(content="What time is it?"),
                        llm_client=LoopingLLMClient(),
                        max_iterations=max_iterations,
                    )
        finally:
            await engine.dispose()
            admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
            await admin.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1 AND pid <> pg_backend_pid()
                """,
                database_name,
            )
            await admin.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            await admin.close()

    asyncio.run(scenario())


def test_agent_loop_disables_tools_after_tool_result_for_final_answer() -> None:
    async def scenario() -> None:
        database_name = f"agenthub_final_after_tool_test_{uuid4().hex}"
        admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
        await admin.execute(f'CREATE DATABASE "{database_name}"')
        await admin.close()

        engine = create_async_engine(
            f"postgresql+asyncpg://agenthub:agenthub@127.0.0.1:5433/{database_name}",
            poolclass=NullPool,
        )
        Session = async_sessionmaker(engine, expire_on_commit=False)
        llm_client = ToolOnceThenFinalLLMClient()

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with Session() as session:
                user = User(name="Tool Final User", email="tool-final@example.com", hashed_password="hashed")
                session.add(user)
                await session.flush()
                agent = Agent(
                    user_id=user.id,
                    name="Tool Final Agent",
                    instructions="Use tools when useful, then answer.",
                    objective="Test final answer after tool output.",
                    enabled_tools=["datetime"],
                )
                session.add(agent)
                await session.flush()
                conversation = Conversation(user_id=user.id, agent_id=agent.id, title="Tool Final")
                conversation.agent = agent
                session.add(conversation)
                await session.flush()

                result = await run_agent_loop(
                    session,
                    user=user,
                    conversation=conversation,
                    payload=MessageCreate(content="What date is it?"),
                    llm_client=llm_client,
                    max_iterations=3,
                )

                assert len(result.tool_messages) == 1
                assert llm_client.tool_counts[0] > 0
                assert llm_client.tool_counts[1] == 0
                assert result.assistant_message.content == "Final answer from tool output."
        finally:
            await engine.dispose()
            admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
            await admin.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1 AND pid <> pg_backend_pid()
                """,
                database_name,
            )
            await admin.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            await admin.close()

    asyncio.run(scenario())


def test_agent_loop_forces_web_search_for_latest_queries() -> None:
    async def scenario() -> None:
        database_name = f"agenthub_forced_search_test_{uuid4().hex}"
        admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
        await admin.execute(f'CREATE DATABASE "{database_name}"')
        await admin.close()

        engine = create_async_engine(
            f"postgresql+asyncpg://agenthub:agenthub@127.0.0.1:5433/{database_name}",
            poolclass=NullPool,
        )
        Session = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with Session() as session:
                user = User(name="Search User", email="search@example.com", hashed_password="hashed")
                session.add(user)
                await session.flush()
                agent = Agent(
                    user_id=user.id,
                    name="Search Agent",
                    instructions="Use search for latest information.",
                    objective="Test search routing.",
                    enabled_tools=["web_search"],
                )
                session.add(agent)
                await session.flush()
                conversation = Conversation(user_id=user.id, agent_id=agent.id, title="Search")
                conversation.agent = agent
                session.add(conversation)
                await session.flush()

                result = await run_agent_loop(
                    session,
                    user=user,
                    conversation=conversation,
                    payload=MessageCreate(content="Give me today's latest general news."),
                    llm_client=SearchAwareFinalLLMClient(),
                    tool_registry=FakeSearchRegistry(),
                )

                assert result.tool_messages[0].tool_calls["name"] == "web_search"
                assert "today's latest general news" in result.tool_results[0].input["query"].lower()
                assert result.assistant_message.content == "Here is a fresh summary based on web_search."
        finally:
            await engine.dispose()
            admin = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
            await admin.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1 AND pid <> pg_backend_pid()
                """,
                database_name,
            )
            await admin.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
            await admin.close()

    asyncio.run(scenario())
