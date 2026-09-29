from pathlib import Path


def test_initial_migration_exists() -> None:
    migration = Path("alembic/versions/20260929_0001_initial_schema.py")

    assert migration.exists()
    assert "initial schema" in migration.read_text()


def test_auth_migration_exists() -> None:
    migration = Path("alembic/versions/20260929_0002_auth_user_name_refresh_tokens.py")

    assert migration.exists()
    assert "refresh_tokens" in migration.read_text()


def test_agent_tool_capabilities_migration_exists() -> None:
    migration = Path("alembic/versions/20260929_0003_agent_tool_capabilities.py")

    assert migration.exists()
    assert "agent_memories" in migration.read_text()
