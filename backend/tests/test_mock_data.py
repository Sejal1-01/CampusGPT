"""Integration checks for the seeded mock data; run scripts/generate_mock_data.py first."""

import json
from collections.abc import Iterator
from typing import Any

import bcrypt
import mysql.connector
import pytest

from app.config import BACKEND_ROOT, CURRENT_ACADEMIC_YEAR, get_settings

TODAY = "2026-11-11"
LABELS_PATH = BACKEND_ROOT / "evals" / "datasets" / "tagging_labels.json"
TEACHING_THEMES = {
    "pace",
    "clarity",
    "doubt_solving",
    "punctuality",
    "syllabus_coverage",
    "teaching_material",
    "approachability",
    "assessment_fairness",
    "other",
}
COMPLAINT_THEMES = {
    "food_quality",
    "hygiene",
    "menu_variety",
    "mess_timing",
    "room_maintenance",
    "water_supply",
    "electricity",
    "wifi",
    "security",
    "cleanliness",
    "other",
}
HYGIENE_PATTERN = "hygien|cockroach|dirty|ganda|gandi|keeda|flies|safai"
PACE_PATTERN = "fast|rush|speed|slow"
EXPECTED_ROWS = {
    "departments": (4, 4),
    "faculty": (60, 60),
    "students": (800, 800),
    "subjects": (160, 160),
    "course_offerings": (160, 160),
    "registrations": (4000, 4000),
    "exams": (160, 160),
    "hostels": (3, 3),
    "messes": (3, 3),
    "feedback": (1100, 1300),
    "complaints": (280, 320),
    "mess_change_requests": (35, 45),
    "attendance": (150_000, 200_000),
    "results": (2400, 2400),
}

OVERDUE_STUDENTS = """
SELECT DISTINCT fd.student_id FROM fee_dues fd
LEFT JOIN (SELECT fee_due_id, SUM(amount_paid) AS paid FROM fee_payments GROUP BY fee_due_id) p
  ON p.fee_due_id = fd.id
WHERE fd.amount_due - COALESCE(p.paid, 0) > 0 AND fd.due_date < %s
"""
INTERNAL_BY_OFFERING = """
SELECT m.student_id, s.name, co.section, SUM(m.marks_obtained) * 100 / SUM(m.max_marks) AS pct
FROM marks m JOIN course_offerings co ON co.id = m.offering_id JOIN subjects s ON s.id = co.subject_id
WHERE co.dept_id = 1 AND m.component <> 'end_sem'
GROUP BY m.student_id, m.offering_id, s.name, co.section
"""
DBMS_SECTION_A = """
SELECT co.id FROM course_offerings co JOIN subjects s ON s.id = co.subject_id
WHERE co.dept_id = 1 AND co.semester = 5 AND co.section = 'A'
  AND s.name = 'Database Management Systems'
"""


@pytest.fixture(scope="module")
def cursor() -> Iterator[Any]:
    settings = get_settings()
    connection = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user="root",
        password=settings.root_password,
        database=settings.mysql_db,
    )
    yield connection.cursor(dictionary=True)
    connection.close()


def scalar(cursor: Any, sql: str, params: tuple = ()) -> Any:
    cursor.execute(sql, params)
    return next(iter(cursor.fetchone().values()))


def rows(cursor: Any, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cursor.execute(sql, params)
    return cursor.fetchall()


@pytest.mark.parametrize(("table", "bounds"), EXPECTED_ROWS.items())
def test_row_counts(cursor: Any, table: str, bounds: tuple[int, int]) -> None:
    count = scalar(cursor, f"SELECT COUNT(*) FROM {table}")
    assert bounds[0] <= count <= bounds[1]


def test_tags_use_only_allowed_themes(cursor: Any) -> None:
    from app.sql.views import COMPLAINT_THEMES, TEACHING_THEMES

    feedback = {row["theme"] for row in rows(cursor, "SELECT DISTINCT theme FROM feedback_themes")}
    complaints = {
        row["theme"] for row in rows(cursor, "SELECT DISTINCT theme FROM complaint_themes")
    }
    assert feedback <= set(TEACHING_THEMES)
    assert complaints <= set(COMPLAINT_THEMES)


def test_student_shape(cursor: Any) -> None:
    stats = rows(
        cursor, "SELECT AVG(gender = 'F') AS girls, AVG(is_hosteller) AS hostel FROM students"
    )[0]
    assert 0.2 <= stats["girls"] <= 0.3
    assert 0.55 <= stats["hostel"] <= 0.65
    mismatched = scalar(
        cursor,
        "SELECT COUNT(*) FROM students s JOIN faculty f ON f.id = s.advisor_id "
        "WHERE f.dept_id <> s.dept_id OR f.is_advisor = 0",
    )
    assert mismatched == 0
    assert scalar(cursor, "SELECT COUNT(*) FROM faculty WHERE is_hod = 1 AND is_advisor = 1") == 4


def test_offerings_and_teaching_load(cursor: Any) -> None:
    cross_dept = scalar(
        cursor,
        "SELECT COUNT(*) FROM course_offerings co JOIN faculty f ON f.id = co.faculty_id "
        "JOIN subjects s ON s.id = co.subject_id WHERE f.dept_id <> co.dept_id OR s.dept_id <> co.dept_id",
    )
    assert cross_dept == 0
    loads = rows(
        cursor, "SELECT faculty_id, COUNT(*) AS n FROM course_offerings GROUP BY faculty_id"
    )
    assert {load["n"] for load in loads} <= {2, 3}
    years = rows(cursor, "SELECT DISTINCT academic_year FROM course_offerings")
    assert [year["academic_year"] for year in years] == [CURRENT_ACADEMIC_YEAR]


def test_sessions_held_below_planned(cursor: Any) -> None:
    stats = rows(
        cursor,
        "SELECT MIN(a.held) AS lo, MAX(a.held) AS hi, MIN(co.planned_classes - a.held) AS gap "
        "FROM attendance_summary a JOIN course_offerings co ON co.id = a.offering_id",
    )[0]
    assert 40 <= stats["lo"] <= stats["hi"] <= 52
    assert stats["gap"] > 0
    assert scalar(cursor, "SELECT MAX(held_on) FROM class_sessions").isoformat() <= TODAY


def test_marks_have_no_end_sem(cursor: Any) -> None:
    components = rows(cursor, "SELECT DISTINCT component FROM marks ORDER BY component")
    assert [c["component"] for c in components] == ["assignment", "mid1", "mid2"]


def test_pattern_boys_hostel_b_defaults(cursor: Any) -> None:
    stats = rows(
        cursor,
        "SELECT h.name, COUNT(*) AS residents, SUM(od.student_id IS NOT NULL) AS defaulters "
        "FROM hostel_allocations ha JOIN rooms r ON r.id = ha.room_id JOIN hostels h ON h.id = r.hostel_id "
        f"LEFT JOIN ({OVERDUE_STUDENTS}) od ON od.student_id = ha.student_id "
        "WHERE ha.to_date IS NULL GROUP BY h.name",
        (TODAY,),
    )
    rates = {row["name"]: float(row["defaulters"]) / row["residents"] for row in stats}
    others = [rate for name, rate in rates.items() if name != "Boys Hostel B"]
    for rate in others:
        assert 2.3 <= rates["Boys Hostel B"] / rate <= 4.0


def test_pattern_dbms_low_marks(cursor: Any) -> None:
    by_subject: dict[tuple[str, str], list[float]] = {}
    for row in rows(cursor, INTERNAL_BY_OFFERING):
        by_subject.setdefault((row["name"], row["section"]), []).append(float(row["pct"]))
    dbms = by_subject.pop(("Database Management Systems", "A"))
    dbms_average = sum(dbms) / len(dbms)
    assert all(dbms_average + 15 < sum(p) / len(p) for p in by_subject.values())
    assert sum(p < 40 for p in dbms) >= 8


def test_pattern_dbms_negative_pace_feedback(cursor: Any) -> None:
    feedback = rows(
        cursor, f"SELECT rating, comment FROM feedback WHERE offering_id = ({DBMS_SECTION_A})"
    )
    negative = [f for f in feedback if f["rating"] <= 2]
    assert len(negative) >= 0.6 * len(feedback)
    pace = scalar(
        cursor,
        f"SELECT COUNT(*) FROM feedback WHERE offering_id = ({DBMS_SECTION_A}) "
        "AND rating <= 2 AND LOWER(comment) REGEXP %s",
        (PACE_PATTERN,),
    )
    assert pace == len(negative)


def weekly_attendance(cursor: Any, before: bool) -> float:
    operator = "<" if before else ">="
    return float(
        scalar(
            cursor,
            "SELECT SUM(aw.present_count) * 100 / SUM(aw.possible_count) FROM attendance_weekly aw "
            "JOIN course_offerings co ON co.id = aw.offering_id "
            f"WHERE co.dept_id = 2 AND co.semester = 3 AND co.section = 'B' AND aw.week_start {operator} %s",
            ("2026-09-14",),
        )
    )


def test_pattern_ece_attendance_drop(cursor: Any) -> None:
    assert weekly_attendance(cursor, before=True) >= 85
    assert weekly_attendance(cursor, before=False) <= 65
    other = scalar(
        cursor,
        "SELECT SUM(aw.present_count) * 100 / SUM(aw.possible_count) FROM attendance_weekly aw "
        "JOIN course_offerings co ON co.id = aw.offering_id "
        "WHERE NOT (co.dept_id = 2 AND co.semester = 3 AND co.section = 'B') AND aw.week_start >= %s",
        ("2026-09-14",),
    )
    assert float(other) >= 85


def test_weekly_matches_raw_attendance(cursor: Any) -> None:
    weekly = scalar(cursor, "SELECT SUM(present_count) FROM attendance_weekly")
    raw = scalar(cursor, "SELECT SUM(present) FROM attendance")
    summary = scalar(cursor, "SELECT SUM(attended) FROM attendance_summary")
    assert weekly == raw == summary


def test_pattern_at_risk_count(cursor: Any) -> None:
    from scripts.generate_mock_data import AT_RISK_SQL

    assert 20 <= scalar(cursor, AT_RISK_SQL, (CURRENT_ACADEMIC_YEAR, CURRENT_ACADEMIC_YEAR)) <= 40


def test_pattern_mess2_hygiene(cursor: Any) -> None:
    hygiene = "category = 'mess' AND LOWER(text) REGEXP %s"
    weeks = scalar(
        cursor,
        f"SELECT COUNT(DISTINCT YEARWEEK(created_at, 1)) FROM complaints WHERE mess_id = 2 AND {hygiene}",
        (HYGIENE_PATTERN,),
    )
    assert weeks >= 4
    november = rows(
        cursor,
        f"SELECT mess_id, COUNT(*) AS n FROM complaints WHERE {hygiene} "
        "AND created_at >= '2026-11-01' GROUP BY mess_id",
        (HYGIENE_PATTERN,),
    )
    counts = {row["mess_id"]: row["n"] for row in november}
    assert counts.get(2, 0) >= 3
    assert all(n < counts[2] for mess_id, n in counts.items() if mess_id != 2)


def test_complaints_match_student_mess_and_hostel(cursor: Any) -> None:
    wrong_mess = scalar(
        cursor,
        "SELECT COUNT(*) FROM complaints c LEFT JOIN mess_allocations ma ON ma.student_id = c.student_id "
        "AND ma.month = DATE_FORMAT(c.created_at, '%Y-%m') "
        "WHERE c.category = 'mess' AND (ma.mess_id IS NULL OR ma.mess_id <> c.mess_id)",
    )
    wrong_hostel = scalar(
        cursor,
        "SELECT COUNT(*) FROM complaints c LEFT JOIN hostel_allocations ha "
        "ON ha.student_id = c.student_id AND ha.to_date IS NULL LEFT JOIN rooms r ON r.id = ha.room_id "
        "WHERE c.category = 'hostel' AND (r.hostel_id IS NULL OR r.hostel_id <> c.hostel_id)",
    )
    bad_resolution = scalar(
        cursor,
        "SELECT COUNT(*) FROM complaints WHERE (status = 'resolved') <> (resolved_at IS NOT NULL)",
    )
    assert wrong_mess == wrong_hostel == bad_resolution == 0


def test_hostels_are_gender_matched(cursor: Any) -> None:
    mismatched = scalar(
        cursor,
        "SELECT COUNT(*) FROM hostel_allocations ha JOIN students s ON s.id = ha.student_id "
        "JOIN rooms r ON r.id = ha.room_id JOIN hostels h ON h.id = r.hostel_id "
        "WHERE h.gender <> s.gender OR s.is_hosteller = 0",
    )
    hostellers = scalar(cursor, "SELECT COUNT(*) FROM students WHERE is_hosteller = 1")
    allocated = scalar(cursor, "SELECT COUNT(*) FROM hostel_allocations WHERE to_date IS NULL")
    assert mismatched == 0
    assert hostellers == allocated


def sgpa_gap(cursor: Any, dept_code: str) -> float:
    stats = rows(
        cursor,
        "SELECT s.is_hosteller, AVG(r.sgpa) AS sgpa FROM results r JOIN students s ON s.id = r.student_id "
        "JOIN departments d ON d.id = s.dept_id WHERE d.code = %s GROUP BY s.is_hosteller",
        (dept_code,),
    )
    by_flag = {row["is_hosteller"]: float(row["sgpa"]) for row in stats}
    return by_flag[0] - by_flag[1]


def test_pattern_me_hosteller_sgpa_gap(cursor: Any) -> None:
    assert 0.3 <= sgpa_gap(cursor, "ME") <= 0.5
    for dept_code in ("CSE", "ECE", "CE"):
        assert abs(sgpa_gap(cursor, dept_code)) < 0.15


def test_results_cgpa_and_status(cursor: Any) -> None:
    inconsistent = scalar(
        cursor,
        "SELECT COUNT(*) FROM results WHERE (backlogs > 0) <> (result_status = 'fail') "
        "OR sgpa NOT BETWEEN 0 AND 10 OR academic_year NOT REGEXP '^20[0-9]{2}-[0-9]{2}$'",
    )
    assert inconsistent == 0


def auth_rows(cursor: Any, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return rows(cursor, sql.replace("{auth}", get_settings().mysql_auth_db), params)


def user_roles(cursor: Any) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for row in auth_rows(
        cursor,
        "SELECT u.username, r.name FROM {auth}.users u "
        "LEFT JOIN {auth}.user_roles ur ON ur.user_id = u.id LEFT JOIN {auth}.roles r ON r.id = ur.role_id",
    ):
        result.setdefault(row["username"], set()).update({row["name"]} - {None})
    return result


def test_seeded_user_roles(cursor: Any) -> None:
    assert user_roles(cursor) == {
        "student1": {"student"},
        "student2": {"student"},
        "faculty1": {"faculty"},
        "faculty2": {"faculty"},
        "advisor1": {"faculty", "advisor"},
        "hod_cse": {"faculty", "advisor", "hod"},
        "dean": {"dean"},
        "admin": {"admin"},
        "admin2": {"admin"},
        "platform_admin": set(),
    }


def seeded(cursor: Any, username: str) -> dict[str, Any]:
    return auth_rows(cursor, "SELECT * FROM {auth}.users WHERE username = %s", (username,))[0]


def test_seeded_passwords_and_links(cursor: Any) -> None:
    platform = seeded(cursor, "platform_admin")
    assert bcrypt.checkpw(
        get_settings().platform_admin_password.encode(), platform["password_hash"].encode()
    )
    assert platform["is_platform_admin"] == 1
    assert not auth_rows(
        cursor,
        "SELECT 1 FROM {auth}.group_members gm JOIN {auth}.users u ON u.id = gm.user_id "
        "WHERE u.username = 'platform_admin' UNION SELECT 1 FROM {auth}.user_grants g "
        "JOIN {auth}.users u ON u.id = g.user_id WHERE u.username = 'platform_admin'",
    )
    for username in ("student1", "faculty1", "dean", "admin2"):
        assert bcrypt.checkpw(b"demo123", seeded(cursor, username)["password_hash"].encode())
    for username in ("dean", "admin", "admin2"):
        user = seeded(cursor, username)
        assert user["student_id"] is user["faculty_id"] is user["dept_id"] is None


def test_student1(cursor: Any) -> None:
    user = seeded(cursor, "student1")
    student = rows(cursor, "SELECT * FROM students WHERE id = %s", (user["student_id"],))[0]
    assert (student["dept_id"], student["current_semester"], student["section"]) == (1, 5, "A")
    assert user["dept_id"] == 1 and student["is_hosteller"] == 1
    hostel = scalar(
        cursor,
        "SELECT h.name FROM hostel_allocations ha JOIN rooms r ON r.id = ha.room_id "
        "JOIN hostels h ON h.id = r.hostel_id WHERE ha.student_id = %s AND ha.to_date IS NULL",
        (student["id"],),
    )
    assert hostel == "Boys Hostel B"
    overdue = [row["student_id"] for row in rows(cursor, OVERDUE_STUDENTS, (TODAY,))]
    assert student["id"] in overdue
    assert (
        scalar(cursor, "SELECT COUNT(*) FROM complaints WHERE student_id = %s", (student["id"],))
        >= 1
    )


def test_student2(cursor: Any) -> None:
    user = seeded(cursor, "student2")
    student = rows(cursor, "SELECT * FROM students WHERE id = %s", (user["student_id"],))[0]
    assert (student["dept_id"], student["current_semester"], student["section"]) == (2, 3, "B")
    assert student["is_hosteller"] == 0 and user["dept_id"] == 2
    low = scalar(
        cursor,
        "SELECT COUNT(*) FROM attendance_summary WHERE student_id = %s AND attended * 100 < 75 * held",
        (student["id"],),
    )
    assert low >= 1


def test_faculty1_teaches_dbms_and_low_attendance_os(cursor: Any) -> None:
    user = seeded(cursor, "faculty1")
    assert user["dept_id"] == 1
    assert (
        scalar(cursor, f"SELECT faculty_id FROM course_offerings WHERE id = ({DBMS_SECTION_A})")
        == user["faculty_id"]
    )
    below = scalar(
        cursor,
        "SELECT COUNT(*) FROM attendance_summary a JOIN course_offerings co ON co.id = a.offering_id "
        "JOIN subjects s ON s.id = co.subject_id WHERE co.faculty_id = %s AND s.name = 'Operating Systems' "
        "AND a.attended * 100 < 75 * a.held",
        (user["faculty_id"],),
    )
    assert below >= 3


def test_faculty2_in_exam_cell(cursor: Any) -> None:
    user = seeded(cursor, "faculty2")
    groups = auth_rows(
        cursor,
        "SELECT g.name FROM {auth}.group_members gm JOIN {auth}.user_groups g ON g.id = gm.group_id "
        "WHERE gm.user_id = %s",
        (user["id"],),
    )
    assert [group["name"] for group in groups] == ["Exam Cell – CSE"]
    faculty1 = seeded(cursor, "faculty1")
    assert user["dept_id"] == 1 and user["faculty_id"] != faculty1["faculty_id"]


def test_advisor1_has_at_risk_advisees(cursor: Any) -> None:
    user = seeded(cursor, "advisor1")
    advisor = rows(cursor, "SELECT * FROM faculty WHERE id = %s", (user["faculty_id"],))[0]
    assert advisor["dept_id"] == 1 and advisor["is_advisor"] == 1 and advisor["is_hod"] == 0
    at_risk = scalar(
        cursor,
        "SELECT COUNT(DISTINCT s.id) FROM students s JOIN attendance_summary a ON a.student_id = s.id "
        "LEFT JOIN (SELECT student_id, offering_id, SUM(marks_obtained) * 100 / SUM(max_marks) AS pct "
        "FROM marks GROUP BY student_id, offering_id) m "
        "ON m.student_id = a.student_id AND m.offering_id = a.offering_id "
        "WHERE s.advisor_id = %s AND (a.attended * 100 < 75 * a.held OR m.pct < 40)",
        (advisor["id"],),
    )
    assert at_risk >= 3


def test_hod_cse(cursor: Any) -> None:
    user = seeded(cursor, "hod_cse")
    hod = rows(cursor, "SELECT * FROM faculty WHERE id = %s", (user["faculty_id"],))[0]
    assert (hod["dept_id"], hod["is_hod"], hod["is_advisor"]) == (1, 1, 1)


def test_labels_file_matches_rows(cursor: Any) -> None:
    labels = json.loads(LABELS_PATH.read_text())
    assert (len(labels["feedback"]), len(labels["complaints"])) == (40, 20)
    for item in labels["feedback"]:
        assert (
            scalar(cursor, "SELECT comment FROM feedback WHERE id = %s", (item["id"],))
            == item["text"]
        )
        assert set(item["themes"]) <= TEACHING_THEMES
    for item in labels["complaints"]:
        assert (
            scalar(cursor, "SELECT text FROM complaints WHERE id = %s", (item["id"],))
            == item["text"]
        )
        assert set(item["themes"]) <= COMPLAINT_THEMES
    sentiments = {item["sentiment"] for item in labels["feedback"]}
    assert sentiments == {"positive", "neutral", "negative"}
    assert any("pace" in item["themes"] for item in labels["feedback"])
    assert any("hygiene" in item["themes"] for item in labels["complaints"])
