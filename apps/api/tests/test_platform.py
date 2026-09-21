"""University platform tests: calendar, notifications, announcements, search, admin."""

from datetime import UTC, datetime, timedelta


def _register(client, email: str, role: str = "STUDENT") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "full_name": email.split("@")[0],
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _promote(client, email: str, role: str) -> dict[str, str]:
    """Register with an elevated role where registration allows it."""
    return _register(client, email, role)


def test_events_are_created_and_listed(client) -> None:
    headers = _register(client, "cal@university.edu")
    starts = datetime.now(UTC) + timedelta(days=1)
    response = client.post(
        "/api/v1/university/events",
        headers=headers,
        json={"title": "Compiler design revision", "starts_at": starts.isoformat()},
    )
    assert response.status_code == 201, response.text
    events = client.get("/api/v1/university/events", headers=headers).json()
    assert [event["title"] for event in events] == ["Compiler design revision"]


def test_events_are_private_to_their_owner(client) -> None:
    owner = _register(client, "owner.cal@university.edu")
    client.post(
        "/api/v1/university/events",
        headers=owner,
        json={
            "title": "Private viva",
            "starts_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        },
    )
    other = _register(client, "other.cal@university.edu")
    assert client.get("/api/v1/university/events", headers=other).json() == []


def test_notifications_can_be_marked_read(client) -> None:
    headers = _register(client, "notify@university.edu")
    created = client.post(
        "/api/v1/university/notifications",
        headers=headers,
        json={"title": "Assignment due", "body": "DBMS assignment due Friday"},
    ).json()
    assert created["is_read"] is False
    marked = client.post(
        f"/api/v1/university/notifications/{created['id']}/read", headers=headers
    ).json()
    assert marked["is_read"] is True
    assert client.get(
        "/api/v1/university/notifications?unread_only=true", headers=headers
    ).json() == []


def test_students_cannot_publish_announcements(client) -> None:
    headers = _register(client, "student.ann@university.edu")
    response = client.post(
        "/api/v1/university/announcements", headers=headers, json={"title": "Fake circular"}
    )
    assert response.status_code == 403


def test_faculty_can_publish_and_everyone_can_read(client) -> None:
    faculty = _promote(client, "faculty.ann@university.edu", "FACULTY")
    response = client.post(
        "/api/v1/university/announcements",
        headers=faculty,
        json={"title": "Lab rescheduled", "body": "Monday lab moves to Wednesday", "notify": True},
    )
    assert response.status_code == 201, response.text

    student = _register(client, "reader.ann@university.edu")
    titles = [item["title"] for item in client.get(
        "/api/v1/university/announcements", headers=student
    ).json()]
    assert "Lab rescheduled" in titles


def test_ai_planning_without_a_provider_is_honest(client) -> None:
    headers = _register(client, "plan@university.edu")
    response = client.post(
        "/api/v1/university/plan",
        headers=headers,
        json={"goal": "Prepare for the DBMS end semester exam", "days": 3},
    )
    assert response.status_code == 503
    assert "AI_BASE_URL" in response.json()["detail"]


def test_global_search_finds_the_users_own_content(client) -> None:
    headers = _register(client, "search@university.edu")
    client.post(
        "/api/v1/university/events",
        headers=headers,
        json={
            "title": "Thermodynamics quiz",
            "starts_at": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        },
    )
    hits = client.get("/api/v1/search?q=thermodynamics", headers=headers).json()["hits"]
    assert any(hit["kind"] == "event" for hit in hits)


def test_admin_stats_require_an_admin_role(client) -> None:
    student = _register(client, "nosy@university.edu")
    assert client.get("/api/v1/admin/stats", headers=student).status_code == 403


def test_coding_status_reports_available_runtimes(client) -> None:
    headers = _register(client, "coder@university.edu")
    body = client.get("/api/v1/coding/status", headers=headers).json()
    assert body["execution_enabled"] is True
    assert {language["id"] for language in body["languages"]} >= {"python", "javascript"}
    assert "network" in body["isolation_note"].lower()


def test_python_code_runs_in_the_sandbox(client) -> None:
    headers = _register(client, "runner@university.edu")
    response = client.post(
        "/api/v1/coding/run",
        headers=headers,
        json={"language": "python", "source": "print(6 * 7)"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["stdout"].strip() == "42"
    assert body["exit_code"] == 0


def test_sandbox_stops_infinite_loops(client) -> None:
    headers = _register(client, "loop@university.edu")
    response = client.post(
        "/api/v1/coding/run",
        headers=headers,
        json={"language": "python", "source": "while True:\n    pass"},
    )
    body = response.json()
    assert body["timed_out"] is True
    assert body["exit_code"] == 124


def test_multimodal_status_lists_missing_configuration(client) -> None:
    headers = _register(client, "media@university.edu")
    body = client.get("/api/v1/multimodal/status", headers=headers).json()
    assert body["vision_configured"] is False
    assert "AI_VISION_MODEL" in body["detail"]


def test_study_material_without_a_provider_is_honest(client) -> None:
    headers = _register(client, "study.tool@university.edu")
    response = client.post(
        "/api/v1/tools/study-material",
        headers=headers,
        json={"topic": "Normalisation in DBMS", "format": "flashcards"},
    )
    assert response.status_code == 503


def test_unknown_study_format_is_rejected(client) -> None:
    headers = _register(client, "badformat@university.edu")
    response = client.post(
        "/api/v1/tools/study-material",
        headers=headers,
        json={"topic": "Graphs", "format": "hologram"},
    )
    assert response.status_code == 400
