import bcrypt

from app.access import repository
from app.access.model import AccessError, check_department_wall, validate_grant
from app.db import Account, execute, fetch_all, fetch_one

GRANT_TABLES = {
    "role": ("role_grants", "role_id"),
    "group": ("group_grants", "group_id"),
    "user": ("user_grants", "user_id"),
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _rw_one(sql: str, params: tuple) -> dict | None:
    return fetch_one(Account.AUTH_RW, sql, params)


def _rw_all(sql: str, params: tuple = ()) -> list[dict]:
    return fetch_all(Account.AUTH_RW, sql, params)


def _user_id(username: str) -> int:
    row = _rw_one("SELECT id, is_platform_admin FROM users WHERE username = %s", (username,))
    if row is None:
        raise AccessError(f"No user named '{username}'.")
    if row["is_platform_admin"]:
        raise AccessError("The platform admin cannot hold roles, groups or grants.")
    return int(row["id"])


def _role_id(name: str) -> int:
    row = _rw_one("SELECT id FROM roles WHERE name = %s", (name,))
    if row is None:
        raise AccessError(f"No role named '{name}'.")
    return int(row["id"])


def _group_id(name: str) -> int:
    row = _rw_one("SELECT id FROM user_groups WHERE name = %s", (name,))
    if row is None:
        raise AccessError(f"No group named '{name}'.")
    return int(row["id"])


def _roles_of(user_id: int) -> set[str]:
    rows = _rw_all(
        "SELECT r.name FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE ur.user_id = %s",
        (user_id,),
    )
    return {row["name"] for row in rows}


def _group_member_ids(group_id: int) -> list[int]:
    rows = _rw_all("SELECT user_id FROM group_members WHERE group_id = %s", (group_id,))
    return [int(row["user_id"]) for row in rows]


def _role_holder_ids(role_id: int) -> list[int]:
    rows = _rw_all("SELECT user_id FROM user_roles WHERE role_id = %s", (role_id,))
    return [int(row["user_id"]) for row in rows]


def _grants_of(kind: str, target_id: int) -> list[tuple[str, str]]:
    table, key = GRANT_TABLES[kind]
    rows = _rw_all(f"SELECT domain, scope FROM {table} WHERE {key} = %s", (target_id,))
    return [(row["domain"], row["scope"]) for row in rows]


def _wall_check_role(role_name: str, domain: str, scope: str) -> None:
    holder_roles = [{role_name}]
    check_department_wall(domain, scope, holder_roles, f"role '{role_name}'")


def _wall_check_users(user_ids: list[int], domain: str, scope: str, target: str) -> None:
    check_department_wall(domain, scope, [_roles_of(user_id) for user_id in user_ids], target)


def create_role(name: str, description: str, actor: int | None = None) -> None:
    if _rw_one("SELECT id FROM roles WHERE name = %s", (name,)):
        raise AccessError(f"Role '{name}' already exists.")
    execute(
        Account.AUTH_RW,
        "INSERT INTO roles (name, description) VALUES (%s, %s)",
        (name, description),
    )
    repository.audit(actor, "create_role", name, description)


def grant(kind: str, target: str, domain: str, scope: str, actor: int | None = None) -> None:
    validate_grant(domain, scope)
    target_id = _resolve_target(kind, target, domain, scope)
    table, key = GRANT_TABLES[kind]
    execute(
        Account.AUTH_RW,
        f"INSERT IGNORE INTO {table} ({key}, domain, scope) VALUES (%s, %s, %s)",
        (target_id, domain, scope),
    )
    repository.audit(actor, "grant", f"{kind}:{target}", f"{domain},{scope}")


def _resolve_target(kind: str, target: str, domain: str, scope: str) -> int:
    if kind == "role":
        _wall_check_role(target, domain, scope)
        return _role_id(target)
    if kind == "group":
        group_id = _group_id(target)
        _wall_check_users(_group_member_ids(group_id), domain, scope, f"group '{target}'")
        return group_id
    if kind == "user":
        user_id = _user_id(target)
        _wall_check_users([user_id], domain, scope, f"user '{target}'")
        return user_id
    raise AccessError("Grant target must be role, group or user.")


def revoke(kind: str, target: str, domain: str, scope: str, actor: int | None = None) -> None:
    table, key = GRANT_TABLES[kind]
    target_id = {"role": _role_id, "group": _group_id, "user": _user_id}[kind](target)
    execute(
        Account.AUTH_RW,
        f"DELETE FROM {table} WHERE {key} = %s AND domain = %s AND scope = %s",
        (target_id, domain, scope),
    )
    repository.audit(actor, "revoke", f"{kind}:{target}", f"{domain},{scope}")


def create_group(name: str, description: str, actor: int | None = None) -> None:
    if _rw_one("SELECT id FROM user_groups WHERE name = %s", (name,)):
        raise AccessError(f"Group '{name}' already exists.")
    execute(
        Account.AUTH_RW,
        "INSERT INTO user_groups (name, description, created_by) VALUES (%s, %s, %s)",
        (name, description, actor),
    )
    repository.audit(actor, "create_group", name, description)


def delete_group(name: str, actor: int | None = None) -> None:
    execute(Account.AUTH_RW, "DELETE FROM user_groups WHERE id = %s", (_group_id(name),))
    repository.audit(actor, "delete_group", name, "")


def add_member(group: str, username: str, actor: int | None = None) -> None:
    group_id = _group_id(group)
    user_id = _user_id(username)
    for domain, scope in _grants_of("group", group_id):
        _wall_check_users([user_id], domain, scope, f"group '{group}'")
    execute(
        Account.AUTH_RW,
        "INSERT IGNORE INTO group_members (group_id, user_id, added_by) VALUES (%s, %s, %s)",
        (group_id, user_id, actor),
    )
    repository.audit(actor, "add_member", f"group:{group}", username)


def remove_member(group: str, username: str, actor: int | None = None) -> None:
    execute(
        Account.AUTH_RW,
        "DELETE FROM group_members WHERE group_id = %s AND user_id = %s",
        (_group_id(group), _user_id(username)),
    )
    repository.audit(actor, "remove_member", f"group:{group}", username)


def assign_role(username: str, role: str, actor: int | None = None) -> None:
    user_id = _user_id(username)
    role_id = _role_id(role)
    _check_role_change(user_id, _roles_of(user_id) | {role})
    execute(
        Account.AUTH_RW,
        "INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (%s, %s)",
        (user_id, role_id),
    )
    repository.audit(actor, "assign_role", f"user:{username}", role)


def unassign_role(username: str, role: str, actor: int | None = None) -> None:
    user_id = _user_id(username)
    _check_role_change(user_id, _roles_of(user_id) - {role})
    execute(
        Account.AUTH_RW,
        "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s",
        (user_id, _role_id(role)),
    )
    repository.audit(actor, "unassign_role", f"user:{username}", role)


def _check_role_change(user_id: int, new_roles: set[str]) -> None:
    held = list(_grants_of("user", user_id))
    for row in _rw_all(
        "SELECT g.domain, g.scope FROM group_members gm JOIN group_grants g ON g.group_id = gm.group_id "
        "WHERE gm.user_id = %s",
        (user_id,),
    ):
        held.append((row["domain"], row["scope"]))
    for role in new_roles:
        row = _rw_one("SELECT id FROM roles WHERE name = %s", (role,))
        if row:
            held.extend(_grants_of("role", int(row["id"])))
    for domain, scope in held:
        check_department_wall(domain, scope, [new_roles], "this role change")


def set_password(username: str, password: str, actor: int | None = None) -> None:
    execute(
        Account.AUTH_RW,
        "UPDATE users SET password_hash = %s WHERE username = %s",
        (hash_password(password), username),
    )
    repository.audit(actor, "set_password", f"user:{username}", "")


def list_roles() -> list[dict]:
    roles = _rw_all("SELECT id, name, description FROM roles ORDER BY name")
    for role in roles:
        role["grants"] = [list(item) for item in _grants_of("role", int(role["id"]))]
        role["members"] = [
            row["username"]
            for row in _rw_all(
                "SELECT u.username FROM user_roles ur JOIN users u ON u.id = ur.user_id "
                "WHERE ur.role_id = %s ORDER BY u.username",
                (role["id"],),
            )
        ]
    return roles


def list_groups() -> list[dict]:
    groups = _rw_all("SELECT id, name, description FROM user_groups ORDER BY name")
    for group in groups:
        group["grants"] = [list(item) for item in _grants_of("group", int(group["id"]))]
        group["members"] = [
            row["username"]
            for row in _rw_all(
                "SELECT u.username FROM group_members gm JOIN users u ON u.id = gm.user_id "
                "WHERE gm.group_id = %s ORDER BY u.username",
                (group["id"],),
            )
        ]
    return groups


def list_users() -> list[dict]:
    return _rw_all(
        "SELECT id, username, display_name, is_platform_admin FROM users ORDER BY username"
    )


def audit_log(limit: int = 100) -> list[dict]:
    return _rw_all(
        "SELECT a.id, u.username AS changed_by, a.action, a.target, a.details, a.changed_at "
        "FROM access_audit_log a LEFT JOIN users u ON u.id = a.changed_by "
        "ORDER BY a.id DESC LIMIT %s",
        (limit,),
    )
