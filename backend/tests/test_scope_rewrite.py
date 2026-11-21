import pytest

from app.db import Account, fetch_all, fetch_one
from tests.integration_helpers import column, login_session, query


def student_id_of(username: str) -> int:
    row = fetch_one(
        Account.APP, "SELECT student_id FROM campus_auth.users WHERE username = %s", (username,)
    )
    return int(row["student_id"])


def faculty_of(username: str) -> tuple[int, int]:
    row = fetch_one(
        Account.APP,
        "SELECT faculty_id, dept_id FROM campus_auth.users WHERE username = %s",
        (username,),
    )
    return int(row["faculty_id"]), int(row["dept_id"])


@pytest.mark.parametrize(
    "view", ["my_marks", "my_attendance", "my_results", "my_fees", "my_registrations"]
)
def test_student_sees_only_own_rows(view: str) -> None:
    session = login_session("student1")
    result = query(session, f"SELECT DISTINCT student_id FROM {view}")
    assert set(column(result, "student_id")) == {student_id_of("student1")}


def test_student_cannot_filter_their_way_to_another_student() -> None:
    session = login_session("student1")
    other = student_id_of("student2")
    result = query(session, f"SELECT student_id FROM my_marks WHERE student_id = {other} OR 1 = 1")
    assert other not in column(result, "student_id")


def test_student_cannot_use_college_views() -> None:
    session = login_session("student1")
    result = query(session, "SELECT roll_no FROM students")
    assert "error" in result


def test_faculty_sees_only_own_classes() -> None:
    session = login_session("faculty1")
    faculty_id, _dept = faculty_of("faculty1")
    result = query(session, "SELECT DISTINCT offering_id FROM my_class_attendance")
    taught = {
        row["id"]
        for row in fetch_all(
            Account.APP, "SELECT id FROM course_offerings WHERE faculty_id = %s", (faculty_id,)
        )
    }
    assert set(column(result, "offering_id")) <= taught
    assert column(result, "offering_id")


def test_faculty_feedback_is_anonymous_and_own() -> None:
    session = login_session("faculty1")
    faculty_id, _dept = faculty_of("faculty1")
    result = query(session, "SELECT DISTINCT faculty_id FROM my_class_feedback")
    assert set(column(result, "faculty_id")) == {faculty_id}
    assert "student_id" not in session.user.views["my_class_feedback"].template.split("FROM")[0]


def test_advisor_sees_only_advisees() -> None:
    session = login_session("advisor1")
    faculty_id, _dept = faculty_of("advisor1")
    result = query(session, "SELECT student_id FROM my_advisees")
    advisees = {
        row["id"]
        for row in fetch_all(
            Account.APP, "SELECT id FROM students WHERE advisor_id = %s", (faculty_id,)
        )
    }
    assert set(column(result, "student_id")) == advisees


def test_advisor_has_no_fee_views() -> None:
    session = login_session("advisor1")
    assert not {
        name
        for name, item in session.user.views.items()
        if ("fees", "college") in item.grants or ("fees", "self") in item.grants
    }
    assert "error" in query(session, "SELECT pending FROM fee_status")


@pytest.mark.parametrize("view", ["dept_students", "dept_marks", "dept_attendance", "dept_results"])
def test_hod_sees_only_own_department(view: str) -> None:
    session = login_session("hod_cse")
    result = query(session, f"SELECT DISTINCT student_id FROM {view}")
    departments = {
        row["dept_id"]
        for row in fetch_all(
            Account.APP,
            "SELECT DISTINCT dept_id FROM students WHERE id IN ("
            + ",".join(str(value) for value in column(result, "student_id"))
            + ")",
        )
    }
    assert departments == {1}


def test_hod_has_no_fees_hostel_mess_or_complaints() -> None:
    names = set(login_session("hod_cse").user.views)
    forbidden = {
        "fee_status",
        "fee_dues",
        "my_fees",
        "hostels",
        "hostel_allocations",
        "messes",
        "complaints",
    }
    assert not names & forbidden


def test_dean_has_college_academics_and_fees_only() -> None:
    names = set(login_session("dean").user.views)
    assert {"students", "marks", "fee_status", "feedback"} <= names
    assert not names & {
        "hostels",
        "hostel_allocations",
        "messes",
        "complaints",
        "student_residence",
    }


def test_dean_sees_all_departments() -> None:
    result = query(
        login_session("dean"), "SELECT dept_code, COUNT(*) AS n FROM students GROUP BY dept_code"
    )
    assert set(column(result, "dept_code")) == {"CSE", "ECE", "ME", "CE"}


def test_admin_sees_complaints_with_student_details() -> None:
    session = login_session("admin")
    result = query(session, "SELECT roll_no, student_name, mess_name FROM complaints LIMIT 5")
    assert len(result["rows"]) == 5
    assert "users" not in session.user.views


def test_platform_admin_has_no_views() -> None:
    session = login_session_platform_admin()
    assert session.user.views == {}
    assert session.user.is_platform_admin


def login_session_platform_admin():
    from app.auth import authenticate
    from app.config import get_settings
    from app.sessions import Session

    user = authenticate("platform_admin", get_settings().platform_admin_password)
    return Session(session_id="test-platform", user=user)


def test_undescribed_view_is_rejected() -> None:
    session = login_session("student1")
    from app.services.portal_data import run_portal_query

    result = run_portal_query(session, "SELECT subject_name FROM my_marks", "x")
    assert "describe_view(my_marks) first" in result["error"]


def test_zero_rows_has_note() -> None:
    result = query(login_session("student1"), "SELECT subject_name FROM my_marks WHERE 1 = 0")
    assert result["total_rows"] == 0
    assert "No matching records" in result["note"]


def test_result_over_limit_reports_total() -> None:
    result = query(login_session("admin"), "SELECT student_id FROM fee_status")
    assert len(result["rows"]) <= 200
    assert result["total_rows"] > 500
    assert "Showing 500 of" in result["note"]


def test_second_rejection_gives_up() -> None:
    session = login_session("student1")
    first = query(session, "SELECT * FROM students")
    second = query(session, "SELECT * FROM students")
    assert "give_up" not in first and "give_up" in second
