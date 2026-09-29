from sqlalchemy.schema import CreateTable

from app.db.base import Base
from app.models import Agent, AgentMemory, Conversation, Message, RefreshToken, Routine, RoutineRun, ToolActionLog, User


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "agents",
        "agent_memories",
        "conversations",
        "messages",
        "refresh_tokens",
        "routines",
        "routine_runs",
        "tool_action_logs",
    }


def test_user_owned_tables_have_user_id() -> None:
    for model in [Agent, Conversation, Routine, RoutineRun, ToolActionLog, RefreshToken, AgentMemory]:
        assert "user_id" in model.__table__.columns


def test_core_tables_compile_to_postgresql() -> None:
    for model in [User, Agent, Conversation, Message, Routine, RoutineRun, ToolActionLog, RefreshToken, AgentMemory]:
        ddl = str(CreateTable(model.__table__).compile(dialect=None))
        assert f"CREATE TABLE {model.__tablename__}" in ddl
