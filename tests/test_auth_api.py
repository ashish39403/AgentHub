from fastapi.testclient import TestClient


def test_register_login_me_refresh_and_logout(auth_client: TestClient) -> None:
    register_response = auth_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Ashish",
            "email": "ashish@example.com",
            "password": "secure-password-123",
        },
    )

    assert register_response.status_code == 201
    registered = register_response.json()
    assert registered["user"]["name"] == "Ashish"
    assert registered["user"]["email"] == "ashish@example.com"
    assert registered["tokens"]["token_type"] == "bearer"
    assert registered["tokens"]["access_token"]
    assert registered["tokens"]["refresh_token"]

    me_response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered['tokens']['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ashish@example.com"

    bad_login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "ashish@example.com", "password": "wrong-password"},
    )

    assert bad_login_response.status_code == 401
    assert bad_login_response.json()["error"]["code"] == "invalid_credentials"

    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "ashish@example.com", "password": "secure-password-123"},
    )

    assert login_response.status_code == 200
    logged_in = login_response.json()
    refresh_token = logged_in["tokens"]["refresh_token"]

    refresh_response = auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["tokens"]["refresh_token"] != refresh_token

    reused_refresh_response = auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert reused_refresh_response.status_code == 401
    assert reused_refresh_response.json()["error"]["code"] == "invalid_refresh_token"

    logout_response = auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed["tokens"]["refresh_token"]},
    )

    assert logout_response.status_code == 204

    logged_out_refresh_response = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refreshed["tokens"]["refresh_token"]},
    )

    assert logged_out_refresh_response.status_code == 401


def test_register_rejects_duplicate_email(auth_client: TestClient) -> None:
    payload = {
        "name": "Ashish",
        "email": "duplicate@example.com",
        "password": "secure-password-123",
    }

    assert auth_client.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate_response = auth_client.post("/api/v1/auth/register", json=payload)

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "auth_error"


def test_me_requires_access_token(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
