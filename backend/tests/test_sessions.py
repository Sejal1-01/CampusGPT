import time

from app.config import MAX_STORED_RESULTS
from app.schemas import StoredResult
from app.sessions import Session, SessionStore
from tests.conftest import make_user


def stored(result_id: str) -> StoredResult:
    return StoredResult(
        result_id=result_id,
        columns=["a"],
        rows=[[1]],
        total_rows=1,
        truncated=False,
        sql="s",
        explanation="e",
    )


def test_store_caps_sessions() -> None:
    store = SessionStore(max_sessions=2)
    first = store.create(make_user())
    store.create(make_user())
    store.create(make_user())
    assert len(store) == 2
    assert store.get(first.session_id) is None


def test_idle_sessions_expire() -> None:
    store = SessionStore(idle_minutes=1)
    session = store.create(make_user())
    session.last_seen = time.monotonic() - 120
    assert store.get(session.session_id) is None


def test_results_are_lru_bounded() -> None:
    session = Session(session_id="s", user=make_user())
    for index in range(MAX_STORED_RESULTS + 5):
        session.store_result(stored(f"r_{index}"))
    assert len(session.results) == MAX_STORED_RESULTS
    assert "r_0" not in session.results


def test_reset_chat_clears_history_state() -> None:
    session = Session(session_id="s", user=make_user())
    session.agent = object()
    session.store_result(stored("r_1"))
    session.described_views.add("my_marks")
    session.reset_chat()
    assert session.agent is None
    assert not session.results
    assert not session.described_views
