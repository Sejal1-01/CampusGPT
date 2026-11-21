from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.agent.fake_model import ScriptedTurn, ToolCall
from app.config import SESSION_COOKIE_NAME, get_settings
from app.guardrails.classifier import GuardrailVerdict
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str = "demo123") -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def sse_events(text: str) -> list[dict]:
    import json

    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def test_health(client) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "database": True}


def test_login_sets_cookie_and_me_works(client) -> None:
    me = login(client, "student1")
    assert me["roles"] == ["student"]
    assert me["department"] == "CSE"
    assert me["starter_questions"]
    assert client.get("/api/auth/me").json()["username"] == "student1"


def test_wrong_password_is_401_with_error_shape(client) -> None:
    response = client.post("/api/auth/login", json={"username": "student1", "password": "nope"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_login"


def test_invalid_cookie_is_401(client) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, "forged.value")
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_logout_clears_session(client) -> None:
    login(client, "student1")
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_me_reveals_nothing_about_other_users(client) -> None:
    me = login(client, "admin")
    assert set(me) == {
        "username",
        "display_name",
        "roles",
        "department",
        "is_platform_admin",
        "allowed_areas",
        "starter_questions",
    }


def test_empty_chat_message_is_400(client) -> None:
    login(client, "student1")
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_message"


def test_too_long_chat_message_is_400(client) -> None:
    login(client, "student1")
    response = client.post("/api/chat", json={"message": "a" * 2001})
    assert response.json()["error"]["code"] == "message_too_long"


def test_chat_requires_login(client) -> None:
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401


def test_chat_streams_answer_with_result(client, fake_models) -> None:
    login(client, "student1")
    fake_models["fast"].structured = [GuardrailVerdict(label="allowed", reason="ok")]
    sql = "SELECT subject_name, attendance_percent FROM my_attendance"
    fake_models["main"].turns = [
        ScriptedTurn(tool_calls=[ToolCall("describe_view", {"name": "my_attendance"})]),
        ScriptedTurn(tool_calls=[ToolCall("query_portal_data", {"sql": sql, "explanation": "x"})]),
        ScriptedTurn(text='root = Answer([t])\nt = TextBlock("ok")'),
    ]
    response = client.post("/api/chat", json={"message": "my attendance"})
    events = sse_events(response.text)
    assert response.headers["content-type"].startswith("text/event-stream")
    assert events[-1]["type"] == "done"
    tool_output = fake_models["main"].calls[-1]["messages"][-1]["content"][0]["toolResult"]
    result_id = tool_output["content"][0]["text"].split('"result_id": "')[1].split('"')[0]
    stored = client.get(f"/api/results/{result_id}").json()
    assert stored["sql"] == sql and stored["rows"]
    csv_response = client.get(f"/api/results/{result_id}/csv")
    assert csv_response.text.startswith("subject_name,attendance_percent")


def test_unknown_result_is_404(client) -> None:
    login(client, "student1")
    assert client.get("/api/results/r_missing").status_code == 404


def test_unknown_quiz_is_404(client) -> None:
    login(client, "student1")
    assert client.get("/api/quiz/q_missing").status_code == 404
    assert client.post("/api/quiz/q_missing/submit", json={"answers": [0]}).status_code == 404


def test_new_chat_resets(client) -> None:
    login(client, "student1")
    assert client.post("/api/chat/reset").json() == {"ok": True}


def test_pdf_upload_rejects_non_pdf(client) -> None:
    login(client, "student1")
    response = client.post("/api/files/pdf", files={"file": ("x.pdf", b"hello", "application/pdf")})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "not_pdf"


@pytest.mark.parametrize("username", ["student1", "admin", "dean"])
def test_access_api_is_403_for_everyone_but_platform_admin(client, username: str) -> None:
    login(client, username)
    assert client.get("/api/access/overview").status_code == 403


def test_platform_admin_has_access_page_but_no_chat(client) -> None:
    me = login(client, "platform_admin", get_settings().platform_admin_password)
    assert me["is_platform_admin"] is True
    assert client.get("/api/access/overview").status_code == 200
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 403


def test_access_api_rejects_department_wall_break(client) -> None:
    login(client, "platform_admin", get_settings().platform_admin_password)
    response = client.post(
        "/api/access/grants",
        json={"kind": "role", "target": "hod", "domain": "academics", "scope": "college"},
    )
    assert response.status_code == 400
    assert "Department wall" in response.json()["error"]["message"]


def test_effective_access_shows_sources(client) -> None:
    login(client, "platform_admin", get_settings().platform_admin_password)
    body = client.get("/api/access/users/faculty2/effective").json()
    assert {
        "source": "group",
        "name": "Exam Cell – CSE",
        "domain": "academics",
        "scope": "department",
    } in body["grants"]
    assert "dept_marks" in body["views"]
