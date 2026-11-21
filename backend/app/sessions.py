import asyncio
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from app.config import MAX_SESSIONS, MAX_STORED_RESULTS, SESSION_IDLE_MINUTES
from app.schemas import StoredResult
from app.user_context import UserContext


@dataclass
class Session:
    session_id: str
    user: UserContext
    agent: Any = None
    results: OrderedDict[str, StoredResult] = field(default_factory=OrderedDict)
    quizzes: dict[str, Any] = field(default_factory=dict)
    flashcards: dict[str, Any] = field(default_factory=dict)
    pdf_texts: dict[str, tuple[str, str]] = field(default_factory=dict)
    described_views: set[str] = field(default_factory=set)
    study_plans: dict[str, Any] = field(default_factory=dict)
    question_papers: dict[str, Any] = field(default_factory=dict)
    reports: dict[str, Any] = field(default_factory=dict)
    revision_questions: list[Any] = field(default_factory=list)
    revision_due_turn: int | None = None
    turns: int = 0
    uploads: Any = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_seen: float = field(default_factory=time.monotonic)
    sql_failures: int = 0

    def store_result(self, result: StoredResult) -> None:
        self.results[result.result_id] = result
        self.results.move_to_end(result.result_id)
        while len(self.results) > MAX_STORED_RESULTS:
            self.results.popitem(last=False)

    def reset_chat(self) -> None:
        self.agent = None
        self.results.clear()
        self.quizzes.clear()
        self.flashcards.clear()
        self.pdf_texts.clear()
        self.described_views.clear()
        self.study_plans.clear()
        self.question_papers.clear()
        self.reports.clear()
        self.revision_questions.clear()
        self.revision_due_turn = None
        self.turns = 0
        self.uploads = None


class SessionStore:
    def __init__(self, max_sessions: int = MAX_SESSIONS, idle_minutes: int = SESSION_IDLE_MINUTES):
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._max_sessions = max_sessions
        self._idle_seconds = idle_minutes * 60

    def create(self, user: UserContext) -> Session:
        self._evict_idle()
        while len(self._sessions) >= self._max_sessions:
            self._sessions.popitem(last=False)
        session = Session(session_id=secrets.token_urlsafe(32), user=user)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if time.monotonic() - session.last_seen > self._idle_seconds:
            self._sessions.pop(session_id, None)
            return None
        session.last_seen = time.monotonic()
        self._sessions.move_to_end(session_id)
        return session

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._sessions)

    def _evict_idle(self) -> None:
        now = time.monotonic()
        idle = [
            key for key, item in self._sessions.items() if now - item.last_seen > self._idle_seconds
        ]
        for key in idle:
            self._sessions.pop(key, None)


store = SessionStore()
