import json
import secrets
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel

from app.agent.prompt_files import render_prompt
from app.agent.structured import structured_call
from app.config import MAX_STUDY_PLAN_DAYS
from app.errors import AppError
from app.schemas import StudyPlan, StudyPlanDay
from app.services.portal_data import run_portal_query
from app.sessions import Session

NEEDED_VIEWS = ("my_exams", "my_marks")


class StudyPlanDraft(BaseModel):
    title: str
    days: list[StudyPlanDay]
    notes: str


def _facts(session: Session) -> dict[str, Any]:
    session.described_views.update(NEEDED_VIEWS)
    today = session.user.scope.today.isoformat()
    exams = run_portal_query(
        session,
        f"SELECT subject_name, exam_date FROM my_exams WHERE exam_date >= '{today}' ORDER BY exam_date",
        "Upcoming exams",
    )
    marks = run_portal_query(
        session,
        "SELECT subject_name, internal_percent FROM my_marks ORDER BY internal_percent",
        "Internal marks, weakest first",
    )
    return {"exams": exams.get("rows", []), "marks_weakest_first": marks.get("rows", [])}


def plan_window(today: date, exam_dates: list[str]) -> tuple[date, date]:
    last = max((date.fromisoformat(value) for value in exam_dates), default=today)
    end = min(last - timedelta(days=1), today + timedelta(days=MAX_STUDY_PLAN_DAYS - 1))
    return today, max(end, today)


def keep_window(days: list[StudyPlanDay], start: date, end: date) -> list[StudyPlanDay]:
    kept = []
    for day in days:
        try:
            when = date.fromisoformat(day.date)
        except ValueError:
            continue
        if start <= when <= end:
            kept.append(day)
    return kept


async def create_study_plan(session: Session, hours_per_day: float = 4.0) -> StudyPlan:
    if not set(NEEDED_VIEWS) <= set(session.user.views):
        raise AppError("forbidden", "Study plans are for students.", 403)
    facts = _facts(session)
    start, end = plan_window(session.user.scope.today, [str(row[1]) for row in facts["exams"]])
    system_prompt = render_prompt(
        "study_plan.md", start=start.isoformat(), end=end.isoformat(), hours=hours_per_day
    )
    draft = await structured_call(
        "fast", StudyPlanDraft, system_prompt, json.dumps(facts, default=str)
    )
    plan = StudyPlan(
        plan_id=f"s_{secrets.token_hex(4)}",
        title=draft.title,
        days=keep_window(draft.days, start, end),
        notes=draft.notes,
    )
    session.study_plans[plan.plan_id] = plan
    return plan


def get_study_plan(session: Session, plan_id: str) -> StudyPlan:
    plan = session.study_plans.get(plan_id)
    if plan is None:
        raise AppError("not_found", "That study plan no longer exists. Ask for a new one.", 404)
    return plan
