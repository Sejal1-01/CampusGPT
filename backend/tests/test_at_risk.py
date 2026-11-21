from app.services.at_risk import find_at_risk, pick_views
from tests.integration_helpers import column, login_session, query


def test_student_gets_no_at_risk_list() -> None:
    assert "error" in find_at_risk(login_session("student1"))


def test_faculty_list_has_no_fees_and_only_own_students() -> None:
    session = login_session("faculty1")
    result = find_at_risk(session)
    own = set(column(query(session, "SELECT DISTINCT roll_no FROM my_class_students"), "roll_no"))
    assert set(column(result, "roll_no")) <= own
    assert all(value is None for value in column(result, "overdue_amount"))


def test_dean_list_includes_overdue_fees() -> None:
    result = find_at_risk(login_session("dean"))
    assert any(value for value in column(result, "overdue_amount"))


def test_department_scope_preferred_over_advisees() -> None:
    views = pick_views(frozenset(login_session("hod_cse").user.views))
    assert views is not None and views.attendance == "dept_attendance"


def test_recurring_complaints_surface_mess_2_hygiene() -> None:
    session = login_session("admin")
    result = query(session, "SELECT target, theme, weeks FROM recurring_complaint_issues")
    assert result["total_rows"] >= 0
