"""Chat and agent API tests.

No provider is configured in tests, so the API must say so honestly with 503
instead of inventing an answer.
"""


def _auth(client) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "chat.student@university.edu",
            "password": "StrongPass123",
            "full_name": "Chat Student",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_agents_are_listed(client) -> None:
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    names = {agent["name"] for agent in response.json()}
    assert {"study", "research", "coding", "career", "document"} <= names
    assert len(names) == 9


def test_routing_preview_requires_authentication(client) -> None:
    assert client.post("/api/v1/agents/route", json={"message": "hi"}).status_code == 401


def test_routing_preview_explains_its_choice(client) -> None:
    response = client.post(
        "/api/v1/agents/route",
        json={"message": "Debug this python error in my function"},
        headers=_auth(client),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "coding"
    assert body["signals"]


def test_ai_status_reports_unconfigured_provider(client) -> None:
    response = client.get("/api/v1/agents/status", headers=_auth(client))
    assert response.status_code == 200
    assert response.json()["configured"] is False


def test_sending_a_message_without_a_provider_returns_503(client) -> None:
    response = client.post(
        "/api/v1/chat/messages",
        json={"message": "Explain gradient descent"},
        headers=_auth(client),
    )
    assert response.status_code == 503
    assert "AI_BASE_URL" in response.json()["detail"]


def test_conversations_start_empty_and_require_authentication(client) -> None:
    headers = _auth(client)
    assert client.get("/api/v1/chat/conversations", headers=headers).json() == []
    assert client.get("/api/v1/chat/conversations").status_code == 401


def test_unknown_conversation_is_404(client) -> None:
    response = client.get(
        "/api/v1/chat/conversations/00000000-0000-0000-0000-000000000000",
        headers=_auth(client),
    )
    assert response.status_code == 404
