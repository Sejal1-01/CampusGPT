from app.auth import authenticate
from app.services.portal_data import run_portal_query
from app.sessions import Session

DEMO_PASSWORD = "demo123"


def login_session(username: str) -> Session:
    return Session(session_id=f"test-{username}", user=authenticate(username, DEMO_PASSWORD))


def query(session: Session, sql: str) -> dict:
    session.described_views.update(session.user.views)
    return run_portal_query(session, sql, "test query")


def column(result: dict, name: str) -> list:
    index = result["columns"].index(name)
    return [row[index] for row in result["rows"]]
