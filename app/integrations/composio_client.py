from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class ComposioConnectionRequest:
    provider: str
    configured: bool
    connect_url: str | None
    external_connection_id: str | None
    message: str


class ComposioClient:
    def is_configured(self) -> bool:
        return bool(settings.composio_api_key)

    async def create_connection_request(self, *, user_id: str, provider: str) -> ComposioConnectionRequest:
        if not self.is_configured():
            return ComposioConnectionRequest(
                provider=provider,
                configured=False,
                connect_url=None,
                external_connection_id=None,
                message="Set COMPOSIO_API_KEY to enable the Composio connection flow.",
            )

        return ComposioConnectionRequest(
            provider=provider,
            configured=True,
            connect_url=None,
            external_connection_id=None,
            message=(
                "Composio is configured. Hosted OAuth link generation is the next integration step; "
                "no provider account has been marked connected yet."
            ),
        )


def get_composio_client() -> ComposioClient:
    return ComposioClient()
