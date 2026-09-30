from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Tool User",
            "email": email,
            "password": "secure-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str], enabled_tools: list[str] | None = None) -> dict:
    payload = {
        "name": "Tool Agent",
        "instructions": "Use tools only when they are useful and enabled.",
        "objective": "Help the user automate personal workflows.",
    }
    if enabled_tools is not None:
        payload["enabled_tools"] = enabled_tools

    response = client.post("/api/v1/agents", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_tool_catalog_lists_ten_tools(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="tool-catalog@example.com")

    response = auth_client.get("/api/v1/tools", headers=auth_headers(auth))

    assert response.status_code == 200
    tools = response.json()["tools"]
    assert {tool["name"] for tool in tools} == {
        "datetime",
        "web_search",
        "summarize_text",
        "save_memory",
        "get_memory",
        "draft_message",
        "send_slack_message",
        "gmail_summary",
        "notion_create_page",
        "github_issue_search",
    }
    slack_tool = next(tool for tool in tools if tool["name"] == "send_slack_message")
    assert slack_tool["requires_confirmation"] is True
    assert slack_tool["safety_level"] == "external_action"


def test_agent_tools_default_and_update(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="agent-tools@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)

    assert agent["enabled_tools"] == [
        "datetime",
        "web_search",
        "summarize_text",
        "draft_message",
        "save_memory",
        "get_memory",
    ]

    get_response = auth_client.get(f"/api/v1/agents/{agent['id']}/tools", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["enabled_tools"] == agent["enabled_tools"]

    update_response = auth_client.put(
        f"/api/v1/agents/{agent['id']}/tools",
        json={"enabled_tools": ["datetime", "web_search", "save_memory", "draft_message"]},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["enabled_tools"] == ["datetime", "web_search", "save_memory", "draft_message"]
    assert [tool["name"] for tool in update_response.json()["tools"]] == [
        "datetime",
        "web_search",
        "save_memory",
        "draft_message",
    ]


def test_unknown_tool_is_rejected(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="unknown-tool@example.com")
    headers = auth_headers(auth)

    response = auth_client.post(
        "/api/v1/agents",
        json={
            "name": "Invalid Tool Agent",
            "instructions": "This should fail because the tool is unknown.",
            "objective": "Validate tool config.",
            "enabled_tools": ["datetime", "apply_to_internship"],
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_tool_config"


def test_agent_tools_are_user_scoped(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="tool-owner@example.com")
    other = register_user(auth_client, email="tool-other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other)
    agent = create_agent(auth_client, owner_headers)

    get_response = auth_client.get(f"/api/v1/agents/{agent['id']}/tools", headers=other_headers)
    update_response = auth_client.put(
        f"/api/v1/agents/{agent['id']}/tools",
        json={"enabled_tools": ["datetime", "web_search"]},
        headers=other_headers,
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404
