from collections.abc import Iterator

import pytest

from app.access import service
from app.access.model import AccessError
from app.auth import authenticate
from app.db import Account, connection, fetch_one
from tests.integration_helpers import DEMO_PASSWORD


def views_of(username: str) -> set[str]:
    return set(authenticate(username, DEMO_PASSWORD).views)


@pytest.fixture
def cleanup() -> Iterator[list]:
    undo: list = []
    yield undo
    for action in reversed(undo):
        action()


def test_multi_role_user_gets_union_of_grants() -> None:
    names = views_of("hod_cse")
    assert {"my_classes", "my_advisees", "dept_marks"} <= names


def test_group_grant_applies_to_members_only() -> None:
    assert "dept_marks" in views_of("faculty2")
    assert "dept_marks" not in views_of("faculty1")


def test_group_member_department_scope_uses_own_department() -> None:
    user = authenticate("faculty2", DEMO_PASSWORD)
    assert user.scope.dept_id == 1


def test_per_user_grant_takes_effect_at_next_login(cleanup) -> None:
    before = authenticate("faculty1", DEMO_PASSWORD)
    service.grant("user", "faculty1", "hostel", "college")
    cleanup.append(lambda: service.revoke("user", "faculty1", "hostel", "college"))
    assert "hostels" not in before.views
    assert "hostels" in views_of("faculty1")


def test_user_in_no_groups_keeps_role_grants() -> None:
    assert "my_class_marks" in views_of("faculty1")


def test_group_with_no_grants_changes_nothing(cleanup) -> None:
    service.create_group("Empty Test Group", "")
    cleanup.append(lambda: service.delete_group("Empty Test Group"))
    service.add_member("Empty Test Group", "faculty1")
    assert views_of("faculty1") == views_of("faculty1")
    assert "dept_marks" not in views_of("faculty1")


@pytest.mark.parametrize("domain", ["academics", "teaching_feedback"])
def test_department_wall_rejects_college_grant_to_non_dean_role(domain: str) -> None:
    with pytest.raises(AccessError, match="Department wall"):
        service.grant("role", "hod", domain, "college")


def test_department_wall_rejects_college_grant_to_user() -> None:
    with pytest.raises(AccessError, match="Department wall"):
        service.grant("user", "faculty1", "academics", "college")


def test_department_wall_rejects_college_grant_to_group() -> None:
    with pytest.raises(AccessError, match="Department wall"):
        service.grant("group", "Exam Cell – CSE", "academics", "college")


def test_department_wall_rejects_adding_non_dean_to_college_group(cleanup) -> None:
    service.create_group("Dean Office Test", "")
    cleanup.append(lambda: service.delete_group("Dean Office Test"))
    service.add_member("Dean Office Test", "dean")
    service.grant("group", "Dean Office Test", "academics", "college")
    with pytest.raises(AccessError, match="Department wall"):
        service.add_member("Dean Office Test", "faculty1")


def test_dean_may_hold_college_academics() -> None:
    service.grant("role", "dean", "academics", "college")


def test_platform_admin_cannot_hold_grants_roles_or_groups() -> None:
    with pytest.raises(AccessError, match="platform admin"):
        service.grant("user", "platform_admin", "fees", "self")
    with pytest.raises(AccessError, match="platform admin"):
        service.assign_role("platform_admin", "admin")
    with pytest.raises(AccessError, match="platform admin"):
        service.add_member("Exam Cell – CSE", "platform_admin")


def test_unknown_domain_or_scope_rejected() -> None:
    with pytest.raises(AccessError, match="Unknown data domain"):
        service.grant("role", "admin", "users", "college")
    with pytest.raises(AccessError, match="Unknown scope"):
        service.grant("role", "admin", "fees", "galaxy")


def test_access_changes_are_audited(cleanup) -> None:
    service.create_group("Audit Test Group", "x")
    cleanup.append(lambda: service.delete_group("Audit Test Group"))
    row = fetch_one(Account.AUTH_RW, "SELECT action FROM access_audit_log ORDER BY id DESC LIMIT 1")
    assert row["action"] == "create_group"


def _run_as_readonly(sql: str) -> None:
    with connection(Account.READONLY) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        cursor.fetchall()


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM campus_auth.users",
        "SELECT * FROM campus_auth.role_grants",
        "INSERT INTO campus.departments (id, code, name) VALUES (99, 'X', 'X')",
        "DELETE FROM campus.marks",
        "DROP TABLE campus.marks",
        "SELECT LOAD_FILE('/etc/passwd') IS NOT NULL",
    ],
)
def test_readonly_mysql_user_is_restricted(sql: str) -> None:
    from mysql.connector import Error

    if "LOAD_FILE" in sql:
        with connection(Account.READONLY) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT LOAD_FILE('/etc/passwd')")
            assert cursor.fetchall()[0][0] is None
        return
    with pytest.raises(Error):
        _run_as_readonly(sql)
