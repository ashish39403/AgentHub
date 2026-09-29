from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Routine User", "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Routine Agent",
            "instructions": "Help with scheduled productivity routines.",
            "objective": "Run scheduled prompts and return useful outputs.",
            "enabled_tools": ["datetime"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_routine(client: TestClient, headers: dict[str, str], agent_id: str) -> dict:
    response = client.post(
        "/api/v1/routines",
        json={
            "agent_id": agent_id,
            "name": "Morning Brief",
            "prompt": "What is the date and time for my morning brief?",
            "schedule": "daily@09:00",
            "timezone": "Asia/Kolkata",
            "is_active": True,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_create_list_get_update_delete_routine(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="routine-owner@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)
    routine = create_routine(auth_client, headers, agent["id"])

    assert routine["name"] == "Morning Brief"
    assert routine["agent_id"] == agent["id"]
    assert routine["user_id"] == auth["user"]["id"]

    list_response = auth_client.get("/api/v1/routines", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["routines"]) == 1

    get_response = auth_client.get(f"/api/v1/routines/{routine['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["schedule"] == "daily@09:00"

    update_response = auth_client.patch(
        f"/api/v1/routines/{routine['id']}",
        json={"is_active": False, "schedule": "interval:minutes:30"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False
    assert update_response.json()["schedule"] == "interval:minutes:30"

    delete_response = auth_client.delete(f"/api/v1/routines/{routine['id']}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = auth_client.get(f"/api/v1/routines/{routine['id']}", headers=headers)
    assert missing_response.status_code == 404


def test_run_routine_creates_run_log(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="routine-runner@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers)
    routine = create_routine(auth_client, headers, agent["id"])

    run_response = auth_client.post(f"/api/v1/routines/{routine['id']}/run", headers=headers)

    assert run_response.status_code == 201
    run = run_response.json()
    assert run["routine_id"] == routine["id"]
    assert run["agent_id"] == agent["id"]
    assert run["status"] == "succeeded"
    assert "datetime" in run["output"]
    assert run["finished_at"] is not None

    runs_response = auth_client.get(f"/api/v1/routines/{routine['id']}/runs", headers=headers)
    assert runs_response.status_code == 200
    assert len(runs_response.json()["runs"]) == 1
    assert runs_response.json()["runs"][0]["id"] == run["id"]


def test_routines_are_user_scoped(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="routine-private-owner@example.com")
    other = register_user(auth_client, email="routine-other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other)
    agent = create_agent(auth_client, owner_headers)
    routine = create_routine(auth_client, owner_headers, agent["id"])

    cross_get = auth_client.get(f"/api/v1/routines/{routine['id']}", headers=other_headers)
    cross_run = auth_client.post(f"/api/v1/routines/{routine['id']}/run", headers=other_headers)
    cross_runs = auth_client.get(f"/api/v1/routines/{routine['id']}/runs", headers=other_headers)

    assert cross_get.status_code == 404
    assert cross_run.status_code == 404
    assert cross_runs.status_code == 404


def test_create_routine_rejects_other_users_agent(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="routine-agent-owner@example.com")
    other = register_user(auth_client, email="routine-agent-other@example.com")
    agent = create_agent(auth_client, auth_headers(owner))

    response = auth_client.post(
        "/api/v1/routines",
        json={
            "agent_id": agent["id"],
            "name": "Bad Routine",
            "prompt": "This should fail.",
            "schedule": "daily@09:00",
        },
        headers=auth_headers(other),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "agent_not_found"
