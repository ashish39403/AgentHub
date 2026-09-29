from app.core.config import settings


class ComposioClient:
    def is_configured(self) -> bool:
        return bool(settings.composio_api_key)

    async def get_connection_status(self, *, user_id, provider: str) -> dict:
        return {
            "provider": provider,
            "configured": self.is_configured(),
            "connected": False,
            "message": "Composio credentials are configured, but per-user OAuth connection flow is not wired yet."
            if self.is_configured()
            else "Set COMPOSIO_API_KEY to enable Composio connection flow.",
        }


def get_composio_client() -> ComposioClient:
    return ComposioClient()
