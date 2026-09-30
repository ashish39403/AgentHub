from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "secure-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Internship Research Agent",
            "instructions": "Find relevant software engineering internships and summarize them clearly.",
            "objective": "Help an engineering student discover and rank internship opportunities daily.",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client: TestClient, headers: dict[str, str], agent_id: str, title: str = "Morning search") -> dict:
    response = client.post(
        f"/api/v1/agents/{agent_id}/conversations",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_create_list_get_conversation_and_add_messages(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="conversation-owner@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)

    conversation = create_conversation(auth_client, headers, agent["id"])

    assert conversation["title"] == "Morning search"
    assert conversation["agent_id"] == agent["id"]
    assert conversation["user_id"] == auth["user"]["id"]

    list_response = auth_client.get(f"/api/v1/agents/{agent['id']}/conversations", headers=headers)

    assert list_response.status_code == 200
    assert len(list_response.json()["conversations"]) == 1
    assert list_response.json()["conversations"][0]["id"] == conversation["id"]

    first_message_response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "Find remote backend internships for me today."},
        headers=headers,
    )
    second_message_response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "Prioritize Python and FastAPI roles."},
        headers=headers,
    )

    assert first_message_response.status_code == 201
    assert first_message_response.json()["role"] == "user"
    assert second_message_response.status_code == 201

    detail_response = auth_client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers)

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == conversation["id"]
    assert [message["content"] for message in detail["messages"]] == [
        "Find remote backend internships for me today.",
        "Prioritize Python and FastAPI roles.",
    ]


def test_conversations_are_user_scoped(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="conversation-private-owner@example.com")
    other_user = register_user(auth_client, email="conversation-other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other_user)
    owner_agent = create_agent(auth_client, owner_headers)
    conversation = create_conversation(auth_client, owner_headers, owner_agent["id"], title="Private chat")

    cross_list_response = auth_client.get(f"/api/v1/agents/{owner_agent['id']}/conversations", headers=other_headers)
    cross_get_response = auth_client.get(f"/api/v1/conversations/{conversation['id']}", headers=other_headers)
    cross_message_response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "Trying to write to another user's conversation."},
        headers=other_headers,
    )

    assert cross_list_response.status_code == 404
    assert cross_list_response.json()["error"]["code"] == "agent_not_found"
    assert cross_get_response.status_code == 404
    assert cross_get_response.json()["error"]["code"] == "conversation_not_found"
    assert cross_message_response.status_code == 404
    assert cross_message_response.json()["error"]["code"] == "conversation_not_found"


def test_delete_conversation_removes_only_owned_conversation(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="delete-conv-owner@example.com")
    other_user = register_user(auth_client, email="delete-conv-other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other_user)
    owner_agent = create_agent(auth_client, owner_headers)
    other_agent = create_agent(auth_client, other_headers)
    owner_conversation = create_conversation(auth_client, owner_headers, owner_agent["id"])
    other_conversation = create_conversation(auth_client, other_headers, other_agent["id"])

    cross_delete_response = auth_client.delete(f"/api/v1/conversations/{owner_conversation['id']}", headers=other_headers)

    assert cross_delete_response.status_code == 404
    assert cross_delete_response.json()["error"]["code"] == "conversation_not_found"

    delete_response = auth_client.delete(f"/api/v1/conversations/{owner_conversation['id']}", headers=owner_headers)

    assert delete_response.status_code == 204

    missing_response = auth_client.get(f"/api/v1/conversations/{owner_conversation['id']}", headers=owner_headers)
    other_detail_response = auth_client.get(f"/api/v1/conversations/{other_conversation['id']}", headers=other_headers)

    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "conversation_not_found"
    assert other_detail_response.status_code == 200


def test_conversation_routes_require_auth(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/conversations/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_create_message_validates_payload(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="message-validation@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": ""},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
