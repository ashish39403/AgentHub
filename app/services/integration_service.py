from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.composio_client import ComposioConnectedAccount, get_composio_client
from app.models.enums import IntegrationConnectionStatus, IntegrationProvider
from app.models.integration_connection import IntegrationConnection
from app.models.user import User
from app.repositories import integration_connections as integration_repository
from app.schemas.integration import IntegrationListResponse, IntegrationResponse, IntegrationStatusResponse


@dataclass(frozen=True)
class IntegrationDefinition:
    provider: IntegrationProvider
    name: str
    description: str
    scopes: list[str]
    icon: str
    auth_config_setting: str


INTEGRATION_CATALOG: dict[IntegrationProvider, IntegrationDefinition] = {
    IntegrationProvider.GMAIL: IntegrationDefinition(
        provider=IntegrationProvider.GMAIL,
        name="Gmail",
        description="Read recent emails, summarize inbox activity, rank important messages, and extract action items.",
        scopes=["gmail.readonly"],
        icon="gmail",
        auth_config_setting="composio_gmail_auth_config_id",
    ),
    IntegrationProvider.NOTION: IntegrationDefinition(
        provider=IntegrationProvider.NOTION,
        name="Notion",
        description="Prepare workspace pages for agent reports and saved research outputs.",
        scopes=["notion.pages.write"],
        icon="notion",
        auth_config_setting="composio_notion_auth_config_id",
    ),
    IntegrationProvider.GITHUB: IntegrationDefinition(
        provider=IntegrationProvider.GITHUB,
        name="GitHub",
        description="Search repositories and issues for engineering workflow context.",
        scopes=["github.read"],
        icon="github",
        auth_config_setting="composio_github_auth_config_id",
    ),
}


class UnknownIntegrationProviderError(ValueError):
    pass


async def list_user_integrations(session: AsyncSession, *, user: User) -> IntegrationListResponse:
    await sync_user_integrations(session, user=user)
    connections = await integration_repository.list_connections_for_user(session, user.id)
    connections_by_provider = {connection.provider: connection for connection in connections}
    return IntegrationListResponse(
        integrations=[
            build_integration_response(definition, connections_by_provider.get(provider))
            for provider, definition in INTEGRATION_CATALOG.items()
        ]
    )


async def get_user_integration_status(
    session: AsyncSession,
    *,
    user: User,
    provider: str,
) -> IntegrationStatusResponse:
    integration_provider = parse_provider(provider)
    await sync_user_integrations(session, user=user, provider=integration_provider)
    definition = INTEGRATION_CATALOG[integration_provider]
    connection = await integration_repository.get_connection_for_user(
        session,
        user_id=user.id,
        provider=integration_provider,
    )
    return IntegrationStatusResponse(**build_integration_response(definition, connection).model_dump())


async def get_provider_status_dict(session: AsyncSession, *, user_id: UUID, provider: str) -> dict:
    integration_provider = parse_provider(provider)
    await sync_connection_for_user(session, user_id=user_id, provider=integration_provider)
    definition = INTEGRATION_CATALOG[integration_provider]
    connection = await integration_repository.get_connection_for_user(
        session,
        user_id=user_id,
        provider=integration_provider,
    )
    return build_integration_response(definition, connection).model_dump(mode="json")


async def connect_user_integration(
    session: AsyncSession,
    *,
    user: User,
    provider: str,
) -> IntegrationStatusResponse:
    integration_provider = parse_provider(provider)
    definition = INTEGRATION_CATALOG[integration_provider]
    connection_request = await get_composio_client().create_connection_request(
        user_id=str(user.id),
        provider=integration_provider.value,
        auth_config_id=auth_config_id_for(definition),
    )

    status = (
        IntegrationConnectionStatus.PENDING
        if connection_request.configured
        else IntegrationConnectionStatus.DISCONNECTED
    )
    connection = await integration_repository.upsert_connection(
        session,
        user_id=user.id,
        provider=integration_provider,
        status=status,
        scopes=definition.scopes,
        external_connection_id=connection_request.external_connection_id,
        metadata={
            "connect_url": connection_request.connect_url,
            "message": connection_request.message,
            "requested_at": datetime.now(UTC).isoformat(),
        },
    )
    await session.commit()
    await session.refresh(connection)
    return IntegrationStatusResponse(**build_integration_response(definition, connection).model_dump())


async def disconnect_user_integration(
    session: AsyncSession,
    *,
    user: User,
    provider: str,
) -> IntegrationStatusResponse:
    integration_provider = parse_provider(provider)
    definition = INTEGRATION_CATALOG[integration_provider]
    existing_connection = await integration_repository.get_connection_for_user(
        session,
        user_id=user.id,
        provider=integration_provider,
    )
    if existing_connection and existing_connection.external_connection_id:
        await get_composio_client().delete_connected_account(existing_connection.external_connection_id)

    connection = await integration_repository.upsert_connection(
        session,
        user_id=user.id,
        provider=integration_provider,
        status=IntegrationConnectionStatus.DISCONNECTED,
        scopes=definition.scopes,
        account_email=None,
        external_connection_id=None,
        metadata={"message": f"{definition.name} disconnected locally."},
    )
    connection.connected_at = None
    connection.expires_at = None
    await session.commit()
    await session.refresh(connection)
    return IntegrationStatusResponse(**build_integration_response(definition, connection).model_dump())


async def get_connected_account_for_provider(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: str,
) -> IntegrationConnection | None:
    integration_provider = parse_provider(provider)
    connection = await sync_connection_for_user(session, user_id=user_id, provider=integration_provider)
    if connection and connection.status == IntegrationConnectionStatus.CONNECTED and connection.external_connection_id:
        return connection
    return None


async def sync_user_integrations(
    session: AsyncSession,
    *,
    user: User,
    provider: IntegrationProvider | None = None,
) -> None:
    providers = [provider] if provider else list(INTEGRATION_CATALOG)
    for integration_provider in providers:
        await sync_connection_for_user(session, user_id=user.id, provider=integration_provider)
    await session.commit()


async def sync_connection_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: IntegrationProvider,
) -> IntegrationConnection | None:
    definition = INTEGRATION_CATALOG[provider]
    auth_config_id = auth_config_id_for(definition)
    existing_connection = await integration_repository.get_connection_for_user(
        session,
        user_id=user_id,
        provider=provider,
    )
    accounts = await get_composio_client().list_connected_accounts(
        user_id=str(user_id),
        provider=provider.value,
        auth_config_id=auth_config_id,
        connected_account_id=existing_connection.external_connection_id if existing_connection else None,
    )
    best_account = choose_best_account(accounts)
    if best_account is None:
        return existing_connection

    status = status_from_composio(best_account.status)
    metadata = {
        **(existing_connection.metadata_ if existing_connection else {}),
        "composio_status": best_account.status,
        "synced_at": datetime.now(UTC).isoformat(),
    }
    connection = await integration_repository.upsert_connection(
        session,
        user_id=user_id,
        provider=provider,
        status=status,
        scopes=definition.scopes,
        account_email=best_account.account_email,
        external_connection_id=best_account.id,
        metadata=metadata,
    )
    if status == IntegrationConnectionStatus.CONNECTED and connection.connected_at is None:
        connection.connected_at = datetime.now(UTC)
    return connection


def parse_provider(provider: str) -> IntegrationProvider:
    try:
        integration_provider = IntegrationProvider(provider.strip().lower())
    except ValueError as exc:
        raise UnknownIntegrationProviderError(f"Unsupported integration provider: {provider}") from exc
    if integration_provider not in INTEGRATION_CATALOG:
        raise UnknownIntegrationProviderError(f"Unsupported integration provider: {provider}")
    return integration_provider


def build_integration_response(
    definition: IntegrationDefinition,
    connection: IntegrationConnection | None,
) -> IntegrationResponse:
    configured = get_composio_client().is_configured() and bool(auth_config_id_for(definition))
    status = connection.status if connection else IntegrationConnectionStatus.DISCONNECTED
    connected = status == IntegrationConnectionStatus.CONNECTED
    metadata = connection.metadata_ if connection else {}
    message = str(metadata.get("message") or default_message(definition, status, configured))

    return IntegrationResponse(
        id=connection.id if connection else definition.provider.value,
        provider=definition.provider.value,
        name=definition.name,
        description=definition.description,
        configured=configured,
        connected=connected,
        status=status.value,
        scopes=connection.scopes if connection else definition.scopes,
        icon=definition.icon,
        message=message,
        account_email=connection.account_email if connection else None,
        external_connection_id=connection.external_connection_id if connection and connected else None,
        connect_url=metadata.get("connect_url") if isinstance(metadata.get("connect_url"), str) else None,
        connected_at=connection.connected_at if connection else None,
        expires_at=connection.expires_at if connection else None,
        created_at=connection.created_at if connection else None,
        updated_at=connection.updated_at if connection else None,
    )


def default_message(
    definition: IntegrationDefinition,
    status: IntegrationConnectionStatus,
    configured: bool,
) -> str:
    if status == IntegrationConnectionStatus.CONNECTED:
        return f"{definition.name} is connected."
    if status == IntegrationConnectionStatus.PENDING:
        return f"{definition.name} connection was requested. Complete OAuth before agents can use it."
    if not configured:
        return f"Set COMPOSIO_API_KEY and {env_name_for_auth_config(definition)} to enable this integration."
    return f"{definition.name} is ready to connect through Composio."


def auth_config_id_for(definition: IntegrationDefinition) -> str | None:
    value = getattr(settings, definition.auth_config_setting)
    return value.strip() if isinstance(value, str) and value.strip() else None


def env_name_for_auth_config(definition: IntegrationDefinition) -> str:
    return definition.auth_config_setting.upper()


def choose_best_account(accounts: list[ComposioConnectedAccount]) -> ComposioConnectedAccount | None:
    if not accounts:
        return None
    active_account = next((account for account in accounts if account.status.upper() == "ACTIVE"), None)
    return active_account or accounts[0]


def status_from_composio(status: str) -> IntegrationConnectionStatus:
    normalized = status.upper()
    if normalized == "ACTIVE":
        return IntegrationConnectionStatus.CONNECTED
    if normalized in {"INITIALIZING", "INITIATED"}:
        return IntegrationConnectionStatus.PENDING
    if normalized in {"REVOKED", "INACTIVE"}:
        return IntegrationConnectionStatus.DISCONNECTED
    return IntegrationConnectionStatus.ERROR
