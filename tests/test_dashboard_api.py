from fastapi.testclient import TestClient


def register_user(client: TestClient, *, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Dashboard User", "email": email, "password": "secure-password-123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_response['tokens']['access_token']}"}


def create_agent(client: TestClient, headers: dict[str, str], *, enabled_tools: list[str] | None = None) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Dashboard Agent",
            "instructions": "Help with dashboard test automation.",
            "objective": "Run useful tasks and keep logs.",
            "enabled_tools": enabled_tools or ["datetime"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_routine(client: TestClient, headers: dict[str, str], agent_id: str, *, name: str) -> dict:
    response = client.post(
        "/api/v1/routines",
        json={
            "agent_id": agent_id,
            "name": name,
            "prompt": "What is the date and time for dashboard testing?",
            "schedule": "daily@09:00",
            "timezone": "Asia/Kolkata",
            "is_active": True,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client: TestClient, headers: dict[str, str], agent_id: str) -> dict:
    response = client.post(
        f"/api/v1/agents/{agent_id}/conversations",
        json={"title": "Dashboard activity"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_dashboard_empty_state(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="dashboard-empty@example.com")
    headers = auth_headers(auth)

    summary_response = auth_client.get("/api/v1/dashboard/summary", headers=headers)
    runs_response = auth_client.get("/api/v1/dashboard/recent-runs", headers=headers)
    activity_response = auth_client.get("/api/v1/dashboard/recent-activity", headers=headers)
    action_items_response = auth_client.get("/api/v1/dashboard/action-items", headers=headers)

    assert summary_response.status_code == 200
    assert summary_response.json()["agents_count"] == 0
    assert summary_response.json()["active_routines_count"] == 0
    assert summary_response.json()["total_routine_runs_count"] == 0
    assert summary_response.json()["last_run_at"] is None
    assert runs_response.json()["runs"] == []
    assert activity_response.json()["activities"] == []
    assert action_items_response.json()["action_items"] == []


def test_dashboard_summary_recent_runs_and_activity_are_user_scoped(auth_client: TestClient) -> None:
    owner = register_user(auth_client, email="dashboard-owner@example.com")
    other = register_user(auth_client, email="dashboard-other@example.com")
    owner_headers = auth_headers(owner)
    other_headers = auth_headers(other)

    owner_agent = create_agent(auth_client, owner_headers)
    owner_routine_one = create_routine(auth_client, owner_headers, owner_agent["id"], name="Morning Brief")
    owner_routine_two = create_routine(auth_client, owner_headers, owner_agent["id"], name="Evening Brief")
    other_agent = create_agent(auth_client, other_headers)
    other_routine = create_routine(auth_client, other_headers, other_agent["id"], name="Other Brief")

    first_run = auth_client.post(f"/api/v1/routines/{owner_routine_one['id']}/run", headers=owner_headers).json()
    second_run = auth_client.post(f"/api/v1/routines/{owner_routine_two['id']}/run", headers=owner_headers).json()
    auth_client.post(f"/api/v1/routines/{other_routine['id']}/run", headers=other_headers)

    conversation = create_conversation(auth_client, owner_headers, owner_agent["id"])
    auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "What is the date and time right now?"},
        headers=owner_headers,
    )

    summary_response = auth_client.get("/api/v1/dashboard/summary", headers=owner_headers)
    runs_response = auth_client.get("/api/v1/dashboard/recent-runs", headers=owner_headers)
    activity_response = auth_client.get("/api/v1/dashboard/recent-activity", headers=owner_headers)

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["agents_count"] == 1
    assert summary["active_routines_count"] == 2
    assert summary["total_routine_runs_count"] == 2
    assert summary["succeeded_routine_runs_count"] == 2

    runs = runs_response.json()["runs"]
    assert [run["id"] for run in runs] == [second_run["id"], first_run["id"]]
    assert {run["routine_name"] for run in runs} == {"Morning Brief", "Evening Brief"}

    activities = activity_response.json()["activities"]
    assert activities
    assert {activity["agent_id"] for activity in activities} == {owner_agent["id"]}
    assert conversation["id"] in {activity["conversation_id"] for activity in activities}


def test_dashboard_action_items_from_confirmation_required_tools(auth_client: TestClient) -> None:
    auth = register_user(auth_client, email="dashboard-actions@example.com")
    headers = auth_headers(auth)
    agent = create_agent(auth_client, headers, enabled_tools=["send_slack_message"])
    conversation = create_conversation(auth_client, headers, agent["id"])

    response = auth_client.post(
        f"/api/v1/conversations/{conversation['id']}/runs",
        json={"content": "Send a slack message reminding the team about the demo."},
        headers=headers,
    )
    assert response.status_code == 201

    action_items_response = auth_client.get("/api/v1/dashboard/action-items", headers=headers)
    assert action_items_response.status_code == 200
    action_items = action_items_response.json()["action_items"]
    assert len(action_items) == 1
    assert action_items[0]["agent_id"] == agent["id"]
    assert action_items[0]["tool_name"] == "send_slack_message"
    assert action_items[0]["requires_confirmation"] is True

    summary = auth_client.get("/api/v1/dashboard/summary", headers=headers).json()
    assert summary["pending_action_items_count"] == 1
