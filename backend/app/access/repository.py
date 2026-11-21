from app.db import Account, execute, fetch_all, fetch_one
from app.sql.registry import Grant


def find_user_by_username(username: str) -> dict | None:
    return fetch_one(
        Account.APP,
        "SELECT id, username, display_name, password_hash, is_platform_admin, student_id, "
        "faculty_id, dept_id FROM campus_auth.users WHERE username = %s",
        (username,),
    )


def find_user(user_id: int) -> dict | None:
    return fetch_one(
        Account.APP,
        "SELECT id, username, display_name, is_platform_admin, student_id, faculty_id, dept_id "
        "FROM campus_auth.users WHERE id = %s",
        (user_id,),
    )


def user_role_names(user_id: int) -> list[str]:
    rows = fetch_all(
        Account.APP,
        "SELECT r.name FROM campus_auth.user_roles ur JOIN campus_auth.roles r ON r.id = ur.role_id "
        "WHERE ur.user_id = %s ORDER BY r.name",
        (user_id,),
    )
    return [row["name"] for row in rows]


def role_grants_for_user(user_id: int) -> list[dict]:
    return fetch_all(
        Account.APP,
        "SELECT r.name, g.domain, g.scope FROM campus_auth.user_roles ur "
        "JOIN campus_auth.roles r ON r.id = ur.role_id "
        "JOIN campus_auth.role_grants g ON g.role_id = r.id WHERE ur.user_id = %s",
        (user_id,),
    )


def group_grants_for_user(user_id: int) -> list[dict]:
    return fetch_all(
        Account.APP,
        "SELECT ug.name, g.domain, g.scope FROM campus_auth.group_members gm "
        "JOIN campus_auth.user_groups ug ON ug.id = gm.group_id "
        "JOIN campus_auth.group_grants g ON g.group_id = gm.group_id WHERE gm.user_id = %s",
        (user_id,),
    )


def direct_grants_for_user(user_id: int) -> list[dict]:
    return fetch_all(
        Account.APP,
        "SELECT domain, scope FROM campus_auth.user_grants WHERE user_id = %s",
        (user_id,),
    )


def grants_as_set(rows: list[dict]) -> set[Grant]:
    return {(row["domain"], row["scope"]) for row in rows}


def audit(changed_by: int | None, action: str, target: str, details: str) -> None:
    execute(
        Account.AUTH_RW,
        "INSERT INTO access_audit_log (changed_by, action, target, details) VALUES (%s, %s, %s, %s)",
        (changed_by, action, target, details[:500]),
    )
