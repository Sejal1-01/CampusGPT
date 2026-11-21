from fastapi.testclient import TestClient
from mysql.connector import Error as MySqlError

from app.main import app
from app.services import portal_data
from tests.integration_helpers import login_session


def test_health_reports_database_down(monkeypatch) -> None:
    monkeypatch.setattr("app.main.ping", lambda: False)
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "degraded", "database": False}


def test_chat_returns_503_when_database_down(monkeypatch) -> None:
    with TestClient(app) as client:
        client.post("/api/auth/login", json={"username": "student1", "password": "demo123"})
        monkeypatch.setattr("app.routes.chat_routes.ping", lambda: False)
        response = client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "unavailable"


def test_query_timeout_gives_friendly_message(monkeypatch) -> None:
    def timeout(*_args, **_kwargs):
        raise MySqlError(errno=3024, msg="Query execution was interrupted")

    monkeypatch.setattr(portal_data, "run_bounded_query", timeout)
    session = login_session("dean")
    session.described_views.update(session.user.views)
    result = portal_data.run_portal_query(session, "SELECT dept_code FROM students", "x")
    assert "too heavy" in result["give_up"]


def test_raw_database_errors_are_not_shown_verbatim(monkeypatch) -> None:
    def broken(*_args, **_kwargs):
        raise MySqlError(errno=1054, msg="Unknown column 'x' in 'field list'")

    monkeypatch.setattr(portal_data, "run_bounded_query", broken)
    session = login_session("dean")
    session.described_views.update(session.user.views)
    result = portal_data.run_portal_query(session, "SELECT dept_code FROM students", "x")
    assert "hint" in result
