from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IntegrationConnectionStatus, IntegrationProvider
from app.models.integration_connection import IntegrationConnection


async def list_connections_for_user(session: AsyncSession, user_id: UUID) -> list[IntegrationConnection]:
    result = await session.execute(
        select(IntegrationConnection)
        .where(IntegrationConnection.user_id == user_id)
        .order_by(IntegrationConnection.provider.asc())
    )
    return list(result.scalars().all())


async def get_connection_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: IntegrationProvider,
) -> IntegrationConnection | None:
    result = await session.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == provider,
        )
    )
    return result.scalar_one_or_none()


async def upsert_connection(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: IntegrationProvider,
    status: IntegrationConnectionStatus,
    scopes: list[str],
    account_email: str | None = None,
    external_connection_id: str | None = None,
    metadata: dict | None = None,
) -> IntegrationConnection:
    connection = await get_connection_for_user(session, user_id=user_id, provider=provider)
    if connection is None:
        connection = IntegrationConnection(user_id=user_id, provider=provider, scopes=scopes)
        session.add(connection)

    connection.status = status
    connection.scopes = scopes
    connection.account_email = account_email
    connection.external_connection_id = external_connection_id
    connection.metadata_ = metadata or {}
    await session.flush()
    return connection
