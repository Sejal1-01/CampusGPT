import json
import secrets
from dataclasses import dataclass

from pydantic import BaseModel

from app.agent.prompt_files import load_prompt
from app.agent.structured import structured_call
from app.errors import AppError
from app.schemas import AccreditationReport, ReportSection
from app.services.portal_data import run_portal_query
from app.sessions import Session


@dataclass(frozen=True)
class MetricQuery:
    title: str
    sql: str


COLLEGE_QUERIES = (
    MetricQuery(
        "Pass % by department (internals, current semester)",
        "SELECT dept_code, ROUND(AVG(internal_pass) * 100, 2) AS pass_percent FROM marks GROUP BY dept_code",
    ),
    MetricQuery(
        "Average SGPA by department and academic year",
        "SELECT dept_code, academic_year, ROUND(AVG(sgpa), 2) AS avg_sgpa FROM results GROUP BY dept_code, academic_year ORDER BY academic_year",
    ),
    MetricQuery(
        "Average attendance by department",
        "SELECT dept_code, ROUND(AVG(attendance_percent), 2) AS avg_attendance FROM attendance_summary GROUP BY dept_code",
    ),
    MetricQuery(
        "Teaching feedback by department",
        "SELECT dept_code, ROUND(AVG(rating), 2) AS avg_rating, ROUND(AVG(sentiment = 'positive') * 100, 1) AS positive_percent FROM feedback GROUP BY dept_code",
    ),
)
DEPARTMENT_QUERIES = (
    MetricQuery(
        "Pass % by subject (internals, current semester)",
        "SELECT subject_name, ROUND(AVG(internal_pass) * 100, 2) AS pass_percent FROM dept_marks GROUP BY subject_name",
    ),
    MetricQuery(
        "Average SGPA by academic year",
        "SELECT academic_year, ROUND(AVG(sgpa), 2) AS avg_sgpa FROM dept_results GROUP BY academic_year ORDER BY academic_year",
    ),
    MetricQuery(
        "Average attendance by semester",
        "SELECT semester, ROUND(AVG(attendance_percent), 2) AS avg_attendance FROM dept_attendance GROUP BY semester",
    ),
    MetricQuery(
        "Teaching feedback by faculty",
        "SELECT faculty_name, ROUND(AVG(rating), 2) AS avg_rating, ROUND(AVG(sentiment = 'positive') * 100, 1) AS positive_percent FROM dept_feedback GROUP BY faculty_name",
    ),
)
COLLEGE_VIEWS = {"marks", "results", "attendance_summary", "feedback"}
DEPARTMENT_VIEWS = {"dept_marks", "dept_results", "dept_attendance", "dept_feedback"}


class AccreditationDraft(BaseModel):
    sections: list[ReportSection]


def pick_scope(views: set[str]) -> tuple[str, tuple[MetricQuery, ...], set[str]] | None:
    if views >= COLLEGE_VIEWS:
        return "college", COLLEGE_QUERIES, COLLEGE_VIEWS
    if views >= DEPARTMENT_VIEWS:
        return "department", DEPARTMENT_QUERIES, DEPARTMENT_VIEWS
    return None


async def create_report(session: Session) -> AccreditationReport:
    choice = pick_scope(set(session.user.views))
    if choice is None:
        raise AppError("forbidden", "Accreditation drafts are for HODs, the Dean and admins.", 403)
    scope, queries, views = choice
    session.described_views.update(views)
    metrics, result_ids = [], []
    for query in queries:
        outcome = run_portal_query(session, query.sql, query.title)
        if "result_id" in outcome:
            result_ids.append(outcome["result_id"])
            metrics.append(
                {"metric": query.title, "columns": outcome["columns"], "rows": outcome["rows"]}
            )
    draft = await structured_call(
        "fast",
        AccreditationDraft,
        load_prompt("accreditation.md"),
        json.dumps(metrics, default=str),
    )
    label = session.user.department if scope == "department" else "college"
    report = AccreditationReport(
        report_id=f"a_{secrets.token_hex(4)}",
        scope=label or scope,
        result_ids=result_ids,
        sections=draft.sections,
    )
    session.reports[report.report_id] = report
    return report


def get_report(session: Session, report_id: str) -> AccreditationReport:
    report = session.reports.get(report_id)
    if report is None:
        raise AppError("not_found", "That report draft no longer exists. Ask for a new one.", 404)
    return report
