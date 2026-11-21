from collections.abc import Iterator
from datetime import date

import pytest

from app.agent.fake_model import FakeModel
from app.agent.models import set_model_override
from app.sessions import Session
from app.sql.rewrite import ScopeParameters
from app.sql.views import all_views
from app.user_context import UserContext


def make_user(
    views: list[str] | None = None,
    student_id: int | None = 1,
    roles: tuple[str, ...] = ("student",),
) -> UserContext:
    registry = all_views()
    names = views if views is not None else ["my_marks", "my_attendance"]
    return UserContext(
        user_id=99,
        username="tester",
        display_name="Test User",
        roles=roles,
        department="CSE",
        is_platform_admin=False,
        scope=ScopeParameters(
            student_id=student_id, faculty_id=None, dept_id=1, today=date(2026, 11, 11)
        ),
        grants=frozenset({("academics", "self")}),
        views={name: registry[name] for name in names},
    )


@pytest.fixture
def session() -> Session:
    return Session(session_id="test-session", user=make_user())


@pytest.fixture
def fake_models() -> Iterator[dict[str, FakeModel]]:
    models = {"main": FakeModel(), "fast": FakeModel()}
    set_model_override("main", models["main"])
    set_model_override("fast", models["fast"])
    yield models
    set_model_override("main", None)
    set_model_override("fast", None)
