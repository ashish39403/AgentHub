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


def agent_payload(name: str = "Internship Research Agent") -> dict:
    return {
        "name": name,
        "instructions": "Find relevant software engineering internships and summarize them clearly.",
        "objective": "Help an engineering student discover and rank internship opportunities daily.",
    }


def create_agent(client: TestClient, headers: dict[str, str], name: str = "Internship Research Agent") -> dict:
    response = client.post("/api/v1/agents", json=agent_payload(name), headers=headers)
    assert response.status_code == 201
    return response.json()


def test_create_list_get_update_and_delete_agent(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="agent-owner@example.com")
    headers = auth_headers(auth)

    created = create_agent(auth_client, headers)

    assert created["name"] == "Internship Research Agent"
    assert created["user_id"] == auth["user"]["id"]
    assert "web_search" in created["enabled_tools"]
    assert "datetime" in created["enabled_tools"]

    list_response = auth_client.get("/api/v1/agents", headers=headers)

    assert list_response.status_code == 200
    assert len(list_response.json()["agents"]) == 1
    assert list_response.json()["agents"][0]["id"] == created["id"]

    get_response = auth_client.get(f"/api/v1/agents/{created['id']}", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["objective"] == created["objective"]

    update_response = auth_client.patch(
        f"/api/v1/agents/{created['id']}",
        json={"name": "Daily Internship Scout"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Daily Internship Scout"
    assert update_response.json()["instructions"] == created["instructions"]

    delete_response = auth_client.delete(f"/api/v1/agents/{created['id']}", headers=headers)

    assert delete_response.status_code == 204

    missing_response = auth_client.get(f"/api/v1/agents/{created['id']}", headers=headers)

    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "agent_not_found"


def test_agent_routes_require_auth(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/agents")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_agents_are_user_scoped(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="owner@example.com")
    other_user = register_user(auth_client, email="other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other_user)

    owner_agent = create_agent(auth_client, owner_headers, name="Private Agent")
    create_agent(auth_client, other_headers, name="Other Agent")

    owner_list_response = auth_client.get("/api/v1/agents", headers=owner_headers)
    other_list_response = auth_client.get("/api/v1/agents", headers=other_headers)

    assert [agent["name"] for agent in owner_list_response.json()["agents"]] == ["Private Agent"]
    assert [agent["name"] for agent in other_list_response.json()["agents"]] == ["Other Agent"]

    cross_get_response = auth_client.get(f"/api/v1/agents/{owner_agent['id']}", headers=other_headers)
    cross_update_response = auth_client.patch(
        f"/api/v1/agents/{owner_agent['id']}",
        json={"name": "Hijacked Agent"},
        headers=other_headers,
    )
    cross_delete_response = auth_client.delete(f"/api/v1/agents/{owner_agent['id']}", headers=other_headers)

    assert cross_get_response.status_code == 404
    assert cross_update_response.status_code == 404
    assert cross_delete_response.status_code == 404

    still_owner_agent = auth_client.get(f"/api/v1/agents/{owner_agent['id']}", headers=owner_headers)

    assert still_owner_agent.status_code == 200
    assert still_owner_agent.json()["name"] == "Private Agent"


def test_create_agent_validates_payload(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="validation@example.com")

    response = auth_client.post(
        "/api/v1/agents",
        json={
            "name": "A",
            "instructions": "short",
            "objective": "short",
        },
        headers=auth_headers(auth),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
