from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IntegrationResponse(BaseModel):
    id: UUID | str
    provider: str
    name: str
    description: str
    configured: bool
    connected: bool
    status: str
    scopes: list[str]
    icon: str
    message: str
    account_email: str | None = None
    external_connection_id: str | None = None
    connect_url: str | None = None
    connected_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IntegrationListResponse(BaseModel):
    integrations: list[IntegrationResponse]


class IntegrationStatusResponse(IntegrationResponse):
    pass
