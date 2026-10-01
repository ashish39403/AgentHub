from fastapi.testclient import TestClient


class FakeComposioConnectionRequest:
    provider = "gmail"
    configured = True
    connect_url = "https://composio.example/connect/gmail"
    external_connection_id = "ca_pending_gmail"
    message = "Open the Composio link to connect gmail."
    raw_status = "INITIATED"


class FakeComposioAccount:
    id = "ca_active_gmail"
    provider = "gmail"
    status = "ACTIVE"
    user_id = None
    account_email = "student@example.com"
    raw = {}


class FakeComposioClient:
    def is_configured(self) -> bool:
        return True

    async def create_connection_request(self, **kwargs):
        return FakeComposioConnectionRequest()

    async def list_connected_accounts(self, **kwargs):
        return []

    async def delete_connected_account(self, connected_account_id: str) -> bool:
        return True


class FakeActiveComposioClient(FakeComposioClient):
    async def list_connected_accounts(self, **kwargs):
        return [FakeComposioAccount()]


def register_user(client: TestClient, *, email: str = "integrations@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Integration User", "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def test_integration_catalog_returns_minimum_mvp_providers(auth_client: TestClient) -> None:
    auth = register_user(auth_client)

    response = auth_client.get("/api/v1/integrations", headers=auth_headers(auth))

    assert response.status_code == 200
    providers = {item["provider"] for item in response.json()["integrations"]}
    assert providers == {"gmail", "notion", "github"}


def test_gmail_status_endpoint_uses_generic_provider_flow(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="gmail-status-compat@example.com")

    response = auth_client.get("/api/v1/integrations/gmail/status", headers=auth_headers(auth))

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "gmail"
    assert body["connected"] is False
    assert body["status"] == "disconnected"


def test_connect_integration_creates_user_scoped_pending_connection(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="connect-integration@example.com")

    response = auth_client.post("/api/v1/integrations/gmail/connect", headers=auth_headers(auth))

    assert response.status_code == 202
    body = response.json()
    assert body["provider"] == "gmail"
    assert body["status"] in {"pending", "disconnected"}
    assert body["connected"] is False
    assert body["external_connection_id"] is None
    assert (
        "COMPOSIO_API_KEY" in body["message"]
        or "auth config id" in body["message"]
        or "Composio is configured" in body["message"]
    )


def test_connect_integration_returns_composio_hosted_link(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("app.services.integration_service.get_composio_client", lambda: FakeComposioClient())
    monkeypatch.setattr("app.services.integration_service.settings.composio_gmail_auth_config_id", "ac_gmail")
    auth = register_user(auth_client, email="connect-link@example.com")

    response = auth_client.post("/api/v1/integrations/gmail/connect", headers=auth_headers(auth))

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["connect_url"] == "https://composio.example/connect/gmail"
    assert body["external_connection_id"] is None


def test_status_syncs_active_composio_account(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("app.services.integration_service.get_composio_client", lambda: FakeActiveComposioClient())
    monkeypatch.setattr("app.services.integration_service.settings.composio_gmail_auth_config_id", "ac_gmail")
    auth = register_user(auth_client, email="sync-active@example.com")
    headers = auth_headers(auth)

    response = auth_client.get("/api/v1/integrations/gmail/status", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "connected"
    assert body["connected"] is True
    assert body["account_email"] == "student@example.com"
    assert body["external_connection_id"] == "ca_active_gmail"


def test_disconnect_integration_marks_connection_disconnected(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="disconnect-integration@example.com")
    headers = auth_headers(auth)
    auth_client.post("/api/v1/integrations/notion/connect", headers=headers)

    response = auth_client.post("/api/v1/integrations/notion/disconnect", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "notion"
    assert body["status"] == "disconnected"
    assert body["connected"] is False


def test_unknown_integration_provider_returns_404(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="unknown-integration@example.com")

    response = auth_client.get("/api/v1/integrations/slack/status", headers=auth_headers(auth))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "integration_not_found"
