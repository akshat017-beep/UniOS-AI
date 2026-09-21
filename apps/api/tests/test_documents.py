"""Document upload, retrieval and citation tests.

Tests run with EMBEDDING_PROVIDER=hashing, so retrieval is exercised end to end
without contacting any provider.
"""

import io


def _auth(client, email: str = "doc.student@university.edu") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "full_name": "Doc Student"},
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _upload(client, headers, name: str, body: str):
    return client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": (name, io.BytesIO(body.encode()), "text/plain")},
    )


def test_upload_requires_authentication(client) -> None:
    response = client.post(
        "/api/v1/documents", files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")}
    )
    assert response.status_code == 401


def test_upload_indexes_text_and_reports_ready(client) -> None:
    headers = _auth(client)
    response = _upload(
        client,
        headers,
        "syllabus.txt",
        "Operating systems syllabus. Deadlock detection uses a wait-for graph.",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["pages"] == 1
    assert client.get("/api/v1/documents", headers=headers).json()[0]["id"] == body["id"]


def test_executable_uploads_are_rejected(client) -> None:
    headers = _auth(client, "exe.student@university.edu")
    response = client.post(
        "/api/v1/documents",
        headers=headers,
        files={
            "file": ("payload.exe", io.BytesIO(b"MZ\x90\x00bin"), "application/octet-stream")
        },
    )
    assert response.status_code == 400
    assert "not accepted" in response.json()["detail"].lower()


def test_search_returns_citations_with_pages(client) -> None:
    headers = _auth(client, "cite.student@university.edu")
    _upload(
        client,
        headers,
        "networks.txt",
        "TCP congestion control uses slow start and congestion avoidance phases.",
    )
    response = client.post(
        "/api/v1/documents/search",
        headers=headers,
        json={"query": "congestion control slow start"},
    )
    assert response.status_code == 200
    citations = response.json()["citations"]
    assert citations, "expected at least one cited passage"
    assert citations[0]["document_title"] == "networks.txt"
    assert citations[0]["page"] == 1


def test_documents_are_private_to_their_owner(client) -> None:
    owner = _auth(client, "owner@university.edu")
    _upload(client, owner, "private.txt", "The secret exam key is alpha bravo charlie.")
    other = _auth(client, "other@university.edu")

    assert client.get("/api/v1/documents", headers=other).json() == []
    response = client.post(
        "/api/v1/documents/search", headers=other, json={"query": "secret exam key"}
    )
    assert response.json()["citations"] == []


def test_deleting_a_document_removes_its_passages(client) -> None:
    headers = _auth(client, "delete.student@university.edu")
    document_id = _upload(client, headers, "temp.txt", "Kirchhoff current law states ...").json()[
        "id"
    ]
    assert client.delete(f"/api/v1/documents/{document_id}", headers=headers).status_code == 204
    response = client.post(
        "/api/v1/documents/search", headers=headers, json={"query": "Kirchhoff"}
    )
    assert response.json()["citations"] == []


def test_chat_with_documents_reports_missing_provider_honestly(client) -> None:
    headers = _auth(client, "rag.student@university.edu")
    _upload(client, headers, "unit.txt", "Amdahl's law bounds parallel speedup.")
    response = client.post(
        "/api/v1/chat/messages",
        headers=headers,
        json={"message": "What does Amdahl's law bound?", "use_documents": True},
    )
    # No chat provider is configured in tests: the API must say so, not invent an answer.
    assert response.status_code == 503
    assert "AI_BASE_URL" in response.json()["detail"]
