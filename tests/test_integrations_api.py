from fastapi.testclient import TestClient


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
    assert "COMPOSIO_API_KEY" in body["message"] or "Composio is configured" in body["message"]


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
