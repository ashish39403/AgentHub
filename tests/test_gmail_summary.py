from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Gmail User", "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str], enabled_tools: list[str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Gmail Agent",
            "instructions": "Summarize Gmail safely. Never send or delete emails.",
            "objective": "Rank important emails and extract action items.",
            "enabled_tools": enabled_tools,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client: TestClient, headers: dict[str, str], agent_id: str) -> dict:
    response = client.post(f"/api/v1/agents/{agent_id}/conversations", json={"title": "Gmail"}, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_gmail_status_endpoint(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="gmail-status@example.com")

    response = auth_client.get("/api/v1/integrations/gmail/status", headers=auth_headers(auth))

    assert response.status_code == 200
    assert response.json()["provider"] == "gmail"
    assert response.json()["connected"] is False


def test_gmail_summary_tool_returns_structured_read_only_output(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="gmail-summary@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers, enabled_tools=["gmail_summary"])
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "Summarize my Gmail and rank important emails."},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tool_messages"][0]["tool_calls"]["name"] == "gmail_summary"
    tool_content = body["tool_messages"][0]["content"]
    assert "important_emails" in tool_content
    assert "send_enabled': False" in tool_content
    assert "delete_enabled': False" in tool_content
