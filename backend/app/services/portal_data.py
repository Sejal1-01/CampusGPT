import json
import logging
import secrets
import time
from datetime import date, datetime
from decimal import Decimal
from functools import cache
from typing import Any

from mysql.connector import Error as MySqlError

from app.config import MAX_RESULT_ROWS, MAX_ROWS_TO_MODEL, QUERY_TIMEOUT_MS
from app.db import run_bounded_query
from app.schemas import StoredResult
from app.sessions import Session
from app.sql.guard import GuardError, check_query
from app.sql.registry import LogicalView
from app.sql.rewrite import RewriteError, cte_names_of, rewrite
from app.sql.views import all_views

logger = logging.getLogger(__name__)
TIMEOUT_ERROR_CODE = 3024
TWO_FAILURES_MESSAGE = (
    "I couldn't answer that safely. Try rephrasing the question, for example by naming the "
    "subject, semester or department."
)


def reserved_names() -> frozenset[str]:
    from app.sql.views import all_views as views

    base_tables = {
        "departments",
        "faculty",
        "students",
        "subjects",
        "course_offerings",
        "registrations",
        "class_sessions",
        "attendance",
        "attendance_summary",
        "attendance_weekly",
        "marks",
        "results",
        "fee_dues",
        "fee_payments",
        "exams",
        "hostels",
        "rooms",
        "hostel_allocations",
        "messes",
        "mess_allocations",
        "mess_change_requests",
        "feedback",
        "feedback_tags",
        "feedback_themes",
        "complaints",
        "complaint_tags",
        "complaint_themes",
        "users",
    }
    return frozenset(base_tables | set(views()))


def list_views_text(views: dict[str, LogicalView]) -> str:
    return "\n".join(f"- {item.name}: {item.description}" for item in views.values())


def join_map_text(views: dict[str, LogicalView]) -> str:
    lines: list[str] = []
    names = sorted(views)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            shared = set(views[left].join_keys) & set(views[right].join_keys)
            lines.extend(f"{left}.{key} = {right}.{key}" for key in sorted(shared))
    return "\n".join(lines)


@cache
def _describe_cached(name: str, other_views: tuple[str, ...]) -> str:
    item = all_views()[name]
    lines = [f"View {item.name}: {item.description}", "Columns:"]
    for column in item.columns:
        values = (
            f" Allowed values: {', '.join(column.allowed_values)}." if column.allowed_values else ""
        )
        lines.append(f"- {column.name} ({column.type}): {column.meaning}.{values}")
    joins = [
        f"{item.name}.{key} = {other}.{key}"
        for other in other_views
        if other != name
        for key in sorted(set(item.join_keys) & set(all_views()[other].join_keys))
    ]
    lines.append("Join keys: " + ("; ".join(joins) if joins else "none"))
    lines.append("Formats: amounts in INR, percentages 0-100, dates YYYY-MM-DD.")
    for example in item.examples:
        lines.append(f"Example: {example.question}\n  SQL: {example.sql}")
    return "\n".join(lines)


def describe_view(session: Session, name: str) -> str:
    key = name.strip().lower()
    views = session.user.views
    if key not in views:
        return f"'{name}' is not one of your views. Your views:\n{list_views_text(views)}"
    session.described_views.add(key)
    return _describe_cached(key, tuple(sorted(views)))


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _count_rows(final_sql: str) -> int | None:
    try:
        result = run_bounded_query(
            f"SELECT COUNT(*) FROM ({final_sql}) AS counted", 1, QUERY_TIMEOUT_MS
        )
        return int(result.rows[0][0])
    except MySqlError:
        return None


def _prepare(session: Session, sql: str) -> tuple[str, bool]:
    guarded = check_query(sql, session.user.allowed_view_names, reserved_names())
    undescribed = sorted(guarded.views - session.described_views)
    if undescribed:
        raise GuardError(f"describe_view({undescribed[0]}) first.")
    final_sql = rewrite(
        guarded.statement, session.user.views, session.user.scope, cte_names_of(guarded.statement)
    )
    return final_sql, guarded.has_explicit_limit


def _total_rows(final_sql: str, has_limit: bool, row_count: int) -> int:
    if has_limit or row_count < MAX_RESULT_ROWS:
        return row_count
    unlimited = final_sql.rsplit(" LIMIT ", 1)[0]
    return _count_rows(unlimited) or row_count


def run_portal_query(session: Session, sql: str, explanation: str) -> dict[str, Any]:
    started = time.monotonic()
    try:
        final_sql, has_limit = _prepare(session, sql)
        result = run_bounded_query(final_sql, MAX_RESULT_ROWS, QUERY_TIMEOUT_MS)
    except (GuardError, RewriteError) as error:
        return _rejection(session, str(error))
    except MySqlError as error:
        return _database_failure(session, error)
    session.sql_failures = 0
    rows = [[_json_value(value) for value in row] for row in result.rows]
    total = _total_rows(final_sql, has_limit, len(rows))
    stored = StoredResult(
        result_id=f"r_{secrets.token_hex(4)}",
        columns=result.columns,
        rows=rows,
        total_rows=total,
        truncated=total > len(rows),
        sql=sql.strip(),
        explanation=explanation.strip(),
    )
    session.store_result(stored)
    logger.info(
        "user=%s query ok rows=%s ms=%s sql=%s",
        session.user.user_id,
        total,
        int((time.monotonic() - started) * 1000),
        final_sql,
    )
    return _model_payload(stored)


def _model_payload(stored: StoredResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "result_id": stored.result_id,
        "columns": stored.columns,
        "rows": stored.rows[:MAX_ROWS_TO_MODEL],
        "total_rows": stored.total_rows,
    }
    if stored.total_rows == 0:
        payload["note"] = "No matching records. Say so plainly; do not draw an empty chart."
    elif stored.truncated:
        payload["note"] = f"Showing {len(stored.rows)} of {stored.total_rows} rows."
    return payload


def _rejection(session: Session, reason: str) -> dict[str, Any]:
    session.sql_failures += 1
    logger.info("user=%s query rejected: %s", session.user.user_id, reason)
    if session.sql_failures >= 2:
        session.sql_failures = 0
        return {"error": reason, "give_up": TWO_FAILURES_MESSAGE}
    return {"error": reason, "hint": "Fix the query and retry once."}


def _database_failure(session: Session, error: MySqlError) -> dict[str, Any]:
    logger.warning("user=%s query failed: %s", session.user.user_id, error)
    if getattr(error, "errno", None) == TIMEOUT_ERROR_CODE:
        return {
            "error": "The query took too long.",
            "give_up": "That question was too heavy to "
            "answer quickly. Try narrowing it to a department, semester or subject.",
        }
    return _rejection(session, f"MySQL error: {getattr(error, 'msg', 'query failed')}")


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def rerun_saved_query(session: Session, sql: str, explanation: str) -> StoredResult:
    """Re-runs a pinned dashboard query; the guard and scope rewrite apply to the current user."""
    session.described_views.update(session.user.views)
    outcome = run_portal_query(session, sql, explanation)
    if "result_id" not in outcome:
        from app.errors import AppError

        raise AppError("query_rejected", outcome.get("error", "That query can't be run."), 400)
    return session.results[outcome["result_id"]]
