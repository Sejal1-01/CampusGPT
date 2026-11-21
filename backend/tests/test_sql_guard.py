import pytest

from app.config import MAX_RESULT_ROWS
from app.services.portal_data import reserved_names
from app.sql.guard import GuardError, check_query

ALLOWED = frozenset({"my_marks", "my_attendance", "my_fees"})


def check(sql: str):
    return check_query(sql, ALLOWED, reserved_names())


ACCEPTED = [
    "SELECT subject_name, internal_percent FROM my_marks",
    "SELECT m.subject_name FROM my_marks m JOIN my_attendance a ON a.offering_id = m.offering_id",
    "WITH low AS (SELECT subject_name FROM my_attendance WHERE attendance_percent < 75) "
    "SELECT subject_name FROM low",
    "SELECT subject_name FROM my_marks UNION SELECT subject_name FROM my_attendance",
    "SELECT SUM(pending) AS total FROM my_fees",
    "SELECT subject_name FROM my_marks WHERE subject_name LIKE '%@%'",
]

REJECTED = [
    ("SELECT 1; SELECT 2", "Exactly one"),
    ("", "Exactly one"),
    ("INSERT INTO marks VALUES (1)", "Only SELECT"),
    ("UPDATE marks SET marks_obtained = 20", "Only SELECT"),
    ("DELETE FROM marks", "Only SELECT"),
    ("REPLACE INTO marks VALUES (1)", "Only SELECT"),
    ("CREATE TABLE x (id INT)", "Only SELECT"),
    ("DROP TABLE marks", "Only SELECT"),
    ("ALTER TABLE marks ADD c INT", "Only SELECT"),
    ("TRUNCATE TABLE marks", "Only SELECT"),
    ("GRANT ALL ON *.* TO x", "Only SELECT"),
    ("SET @a = 1", ""),
    ("CALL proc()", ""),
    ("DO SLEEP(1)", ""),
    ("HANDLER marks OPEN", ""),
    ("LOAD DATA INFILE 'x' INTO TABLE marks", ""),
    ("LOCK TABLES marks READ", ""),
    ("SELECT subject_name FROM my_marks INTO OUTFILE '/tmp/x'", ""),
    ("SELECT subject_name FROM my_marks INTO DUMPFILE '/tmp/x'", ""),
    ("SELECT subject_name INTO @v FROM my_marks", ""),
    ("SELECT subject_name FROM my_marks FOR UPDATE", "Locking"),
    ("SELECT 1 /*! , SLEEP(5) */", "Executable comments"),
    ("SELECT /*+ MAX_EXECUTION_TIME(100000) */ subject_name FROM my_marks", "Executable comments"),
    ("SELECT * FROM students", "not one of your allowed views"),
    ("SELECT * FROM marks", "not one of your allowed views"),
    ("SELECT * FROM campus_auth.users", "Schema-qualified"),
    ("SELECT * FROM campus.students", "Schema-qualified"),
    ("SELECT * FROM information_schema.tables", "Schema-qualified"),
    ("SELECT * FROM mysql.user", "Schema-qualified"),
    ("SELECT * FROM performance_schema.threads", "Schema-qualified"),
    ("SELECT * FROM sys.version", "Schema-qualified"),
    (
        "SELECT subject_name FROM my_marks UNION SELECT name FROM students",
        "not one of your allowed",
    ),
    ("SELECT LOAD_FILE('/etc/passwd')", "LOAD_FILE"),
    ("SELECT SLEEP(5)", "SLEEP"),
    ("SELECT BENCHMARK(1000, MD5('a'))", "BENCHMARK"),
    ("SELECT GET_LOCK('a', 1)", "GET_LOCK"),
    ("SELECT RELEASE_LOCK('a')", "RELEASE_LOCK"),
    ("SELECT USER()", "USER"),
    ("SELECT CURRENT_USER()", "CURRENT_USER"),
    ("SELECT SESSION_USER()", "SESSION_USER"),
    ("SELECT SYSTEM_USER()", "SYSTEM_USER"),
    ("SELECT DATABASE()", ""),
    ("SELECT SCHEMA()", ""),
    ("SELECT VERSION()", ""),
    ("SELECT CONNECTION_ID()", "CONNECTION_ID"),
    ("SELECT @@version", "variables"),
    ("SELECT @x", "variables"),
    ("SELECT @x := 1", "variables"),
    ("WITH students AS (SELECT subject_name FROM my_marks) SELECT * FROM students", "reserved"),
    ("WITH my_fees AS (SELECT 1 AS a) SELECT a FROM my_fees", "reserved"),
]


@pytest.mark.parametrize("sql", ACCEPTED)
def test_accepts_safe_select(sql: str) -> None:
    assert check(sql).statement is not None


@pytest.mark.parametrize(("sql", "reason"), REJECTED)
def test_rejects_unsafe_sql(sql: str, reason: str) -> None:
    with pytest.raises(GuardError, match=reason or None):
        check(sql)


def test_adds_limit_when_missing() -> None:
    guarded = check("SELECT subject_name FROM my_marks")
    assert f"LIMIT {MAX_RESULT_ROWS}" in guarded.statement.sql(dialect="mysql")
    assert guarded.has_explicit_limit is False


def test_caps_large_limit() -> None:
    guarded = check("SELECT subject_name FROM my_marks LIMIT 100000")
    assert f"LIMIT {MAX_RESULT_ROWS}" in guarded.statement.sql(dialect="mysql")


def test_keeps_small_limit() -> None:
    guarded = check("SELECT subject_name FROM my_marks LIMIT 3")
    assert "LIMIT 3" in guarded.statement.sql(dialect="mysql")
    assert guarded.has_explicit_limit is True


def test_reports_views_used() -> None:
    guarded = check(
        "WITH a AS (SELECT offering_id FROM my_attendance) SELECT m.subject_name FROM my_marks m "
        "JOIN a ON a.offering_id = m.offering_id"
    )
    assert guarded.views == {"my_attendance", "my_marks"}


def test_view_names_are_case_insensitive() -> None:
    assert check("SELECT subject_name FROM MY_MARKS").views == {"my_marks"}
