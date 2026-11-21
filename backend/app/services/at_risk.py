from dataclasses import dataclass
from typing import Any

from app.config import ATTENDANCE_THRESHOLD_PERCENT, INTERNAL_FAIL_PERCENT, SGPA_DROP_THRESHOLD
from app.services.portal_data import run_portal_query
from app.sessions import Session


@dataclass(frozen=True)
class RiskViews:
    attendance: str
    marks: str
    results: str | None
    fees: str | None


SCOPE_PRIORITY = (
    RiskViews("attendance_summary", "marks", "results", "fee_status"),
    RiskViews("dept_attendance", "dept_marks", "dept_results", None),
    RiskViews("advisee_attendance", "advisee_marks", "advisee_results", None),
    RiskViews("my_class_attendance", "my_class_marks", None, None),
)


def pick_views(allowed: frozenset[str]) -> RiskViews | None:
    for option in SCOPE_PRIORITY:
        needed = {option.attendance, option.marks} | {
            name for name in (option.results, option.fees) if name
        }
        if needed <= allowed:
            return option
    return None


def _sgpa_cte(results_view: str | None) -> str:
    if results_view is None:
        return "drops AS (SELECT NULL AS student_id, NULL AS sgpa_drop)"
    return (
        "ranked AS (SELECT student_id, sgpa, ROW_NUMBER() OVER (PARTITION BY student_id "
        f"ORDER BY semester DESC) AS position FROM {results_view}), "
        "drops AS (SELECT student_id, MAX(CASE WHEN position = 2 THEN sgpa END) - "
        "MAX(CASE WHEN position = 1 THEN sgpa END) AS sgpa_drop FROM ranked "
        "WHERE position <= 2 GROUP BY student_id)"
    )


def _fees_cte(fees_view: str | None) -> str:
    if fees_view is None:
        return "dues AS (SELECT NULL AS student_id, NULL AS overdue_amount)"
    return (
        "dues AS (SELECT student_id, SUM(pending) AS overdue_amount FROM "
        f"{fees_view} WHERE is_overdue = 1 GROUP BY student_id)"
    )


def build_sql(views: RiskViews) -> str:
    return f"""
    WITH people AS (SELECT DISTINCT student_id, roll_no, student_name FROM {views.attendance}),
    att AS (SELECT student_id, MIN(attendance_percent) AS lowest_attendance,
            GROUP_CONCAT(CASE WHEN attendance_percent < {ATTENDANCE_THRESHOLD_PERCENT}
                         THEN subject_name END SEPARATOR ', ') AS low_attendance_subjects
            FROM {views.attendance} GROUP BY student_id),
    mk AS (SELECT student_id, MIN(internal_percent) AS lowest_internal,
           GROUP_CONCAT(CASE WHEN internal_percent < {INTERNAL_FAIL_PERCENT}
                        THEN subject_name END SEPARATOR ', ') AS failing_subjects
           FROM {views.marks} GROUP BY student_id),
    {_sgpa_cte(views.results)},
    {_fees_cte(views.fees)}
    SELECT p.roll_no, p.student_name, a.lowest_attendance, a.low_attendance_subjects,
           m.lowest_internal, m.failing_subjects, d.sgpa_drop, f.overdue_amount
    FROM people p
    LEFT JOIN att a ON a.student_id = p.student_id
    LEFT JOIN mk m ON m.student_id = p.student_id
    LEFT JOIN drops d ON d.student_id = p.student_id
    LEFT JOIN dues f ON f.student_id = p.student_id
    WHERE a.lowest_attendance < {ATTENDANCE_THRESHOLD_PERCENT}
       OR m.lowest_internal < {INTERNAL_FAIL_PERCENT}
       OR d.sgpa_drop >= {SGPA_DROP_THRESHOLD}
       OR f.overdue_amount > 0
    ORDER BY p.roll_no
    """


def find_at_risk(session: Session) -> dict[str, Any]:
    views = pick_views(session.user.allowed_view_names)
    if views is None:
        return {
            "error": "At-risk lists are only available to faculty, advisors, HODs, the Dean and admins."
        }
    session.described_views.update(
        name for name in (views.attendance, views.marks, views.results, views.fees) if name
    )
    explanation = (
        "Students with attendance below 75% or internals below 40% in any current subject, "
        "or an SGPA drop of 1.0 or more" + (", or overdue fees" if views.fees else "")
    )
    return run_portal_query(session, build_sql(views), explanation)
