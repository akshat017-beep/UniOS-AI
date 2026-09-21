CREDENTIALS = {
    "email": "student@university.edu",
    "password": "StrongPass123",
    "full_name": "Test Student",
}


def register(client, **overrides):
    return client.post("/api/v1/auth/register", json={**CREDENTIALS, **overrides})


def test_register_returns_tokens(client):
    response = register(client)
    assert response.status_code == 201
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_duplicate_email_is_rejected(client):
    register(client)
    assert register(client).status_code == 409


def test_login_and_me(client):
    register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == CREDENTIALS["email"]
    assert me.json()["role"] == "STUDENT"


def test_wrong_password_is_rejected(client):
    register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": CREDENTIALS["email"], "password": "WrongPassword1"},
    )
    assert response.status_code == 401


def test_me_requires_a_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_students_cannot_list_users(client):
    token = register(client).json()["access_token"]
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admins_can_list_users(client):
    token = register(client, email="admin@university.edu", role="ADMIN").json()["access_token"]
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_refresh_token_issues_new_pair(client):
    refresh_token = register(client).json()["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_access_token_is_not_accepted_as_refresh(client):
    access = register(client).json()["access_token"]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": access}).status_code == 401
