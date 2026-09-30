from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.integration import IntegrationListResponse, IntegrationStatusResponse
from app.services.integration_service import (
    UnknownIntegrationProviderError,
    connect_user_integration,
    disconnect_user_integration,
    get_user_integration_status,
    list_user_integrations,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def integration_not_found_error(exc: UnknownIntegrationProviderError) -> AppHTTPException:
    return AppHTTPException(status_code=404, code="integration_not_found", message=str(exc))


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(session: DbSession, current_user: CurrentUser) -> IntegrationListResponse:
    return await list_user_integrations(session, user=current_user)


@router.get("/{provider}/status", response_model=IntegrationStatusResponse)
async def integration_status(provider: str, session: DbSession, current_user: CurrentUser) -> IntegrationStatusResponse:
    try:
        return await get_user_integration_status(session, user=current_user, provider=provider)
    except UnknownIntegrationProviderError as exc:
        raise integration_not_found_error(exc) from exc


@router.post("/{provider}/connect", response_model=IntegrationStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def connect_integration(provider: str, session: DbSession, current_user: CurrentUser) -> IntegrationStatusResponse:
    try:
        return await connect_user_integration(session, user=current_user, provider=provider)
    except UnknownIntegrationProviderError as exc:
        raise integration_not_found_error(exc) from exc


@router.post("/{provider}/disconnect", response_model=IntegrationStatusResponse)
async def disconnect_integration(
    provider: str,
    session: DbSession,
    current_user: CurrentUser,
) -> IntegrationStatusResponse:
    try:
        return await disconnect_user_integration(session, user=current_user, provider=provider)
    except UnknownIntegrationProviderError as exc:
        raise integration_not_found_error(exc) from exc
