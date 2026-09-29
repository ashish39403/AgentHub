from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Action User", "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str], enabled_tools: list[str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Action Agent",
            "instructions": "Handle scheduled actions safely.",
            "objective": "Draft messages and require confirmation for external sends.",
            "enabled_tools": enabled_tools,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client: TestClient, headers: dict[str, str], agent_id: str) -> dict:
    response = client.post(f"/api/v1/agents/{agent_id}/conversations", json={"title": "Actions"}, headers=headers)
    assert response.status_code == 201
    return response.json()


def create_routine(client: TestClient, headers: dict[str, str], agent_id: str, prompt: str) -> dict:
    response = client.post(
        "/api/v1/routines",
        json={
            "agent_id": agent_id,
            "name": "Scheduled Action",
            "prompt": prompt,
            "schedule": "daily@21:00",
            "timezone": "Asia/Kolkata",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_scheduled_draft_action_creates_draft_output(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="draft-action@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers, enabled_tools=["draft_message"])
    routine = create_routine(auth_client, headers, agent["id"], "Draft a message reminding my friend about the project meeting.")

    response = auth_client.post(f"/api/v1/routines/{routine['id']}/run", headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "succeeded"
    assert "draft_message" in body["output"]
    assert "draft_only" in body["output"]


def test_slack_send_requires_confirmation_and_does_not_send(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="slack-action@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers, enabled_tools=["send_slack_message"])
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "Send a Slack message to the team saying standup starts now."},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tool_messages"][0]["tool_calls"]["name"] == "send_slack_message"
    assert "confirmation_required" in body["tool_messages"][0]["content"]
    assert "requires_confirmation': True" in body["tool_messages"][0]["content"]
