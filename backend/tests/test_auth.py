from fastapi.testclient import TestClient

from app.config import settings


def issue_csrf(client: TestClient) -> dict[str, str]:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {"X-CSRF-Token": token}


def signup_user(client: TestClient, email: str = "engineer@example.com"):
    return client.post(
        "/api/v1/auth/signup",
        headers=issue_csrf(client),
        json={
            "email": email,
            "full_name": "Grid Engineer",
            "password": "StrongPass123",
        },
    )


def login_user(client: TestClient, email: str = "engineer@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        headers=issue_csrf(client),
        json={"email": email, "password": password},
    )


def test_signup_sets_session_and_returns_user(client: TestClient):
    response = signup_user(client)

    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == "engineer@example.com"
    assert settings.ACCESS_COOKIE_NAME in response.cookies
    assert settings.REFRESH_COOKIE_NAME in response.cookies


def test_login_and_me_flow(client: TestClient):
    signup_user(client)
    response = login_user(client)

    assert response.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "engineer@example.com"


def test_protected_route_requires_auth(client: TestClient):
    response = client.get("/api/v1/transformers/")

    assert response.status_code == 401


def test_csrf_required_for_unsafe_requests(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"


def test_refresh_renews_session(client: TestClient):
    signup_user(client)
    response = client.post("/api/v1/auth/refresh", headers=issue_csrf(client))

    assert response.status_code == 200
    assert response.json()["message"] == "Session refreshed"


def test_logout_clears_session(client: TestClient):
    signup_user(client)
    response = client.post("/api/v1/auth/logout", headers=issue_csrf(client))

    assert response.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_auth_rate_limiting_returns_429(client: TestClient):
    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        response = client.post(
            "/api/v1/auth/login",
            headers=issue_csrf(client),
            json={"email": "limit@example.com", "password": "wrongpass123"},
        )
        assert response.status_code == 401

    limited = client.post(
        "/api/v1/auth/login",
        headers=issue_csrf(client),
        json={"email": "limit@example.com", "password": "wrongpass123"},
    )
    assert limited.status_code == 429