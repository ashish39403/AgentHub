from pydantic import BaseModel


class IntegrationStatusResponse(BaseModel):
    provider: str
    configured: bool
    connected: bool
    message: str
