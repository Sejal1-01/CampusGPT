from pathlib import Path
from typing import Any

import yaml

from app.access.model import (
    COLLEGE_WIDE_ROLES,
    AccessError,
    breaks_department_wall,
    validate_grant,
)

POLICY_PATH = Path(__file__).with_name("policy.yaml")


def read_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = yaml.safe_load(path.read_text())
    for role, spec in policy.get("roles", {}).items():
        for domain, scope in spec.get("grants", []):
            validate_grant(domain, scope)
            if breaks_department_wall(domain, scope) and role not in COLLEGE_WIDE_ROLES:
                raise AccessError(f"Policy gives ({domain}, college) to role '{role}'.")
    for group, spec in policy.get("groups", {}).items():
        for domain, scope in spec.get("grants", []):
            validate_grant(domain, scope)
            if breaks_department_wall(domain, scope):
                raise AccessError(f"Policy gives ({domain}, college) to group '{group}'.")
    return policy


def load_policy(cursor: Any, policy: dict[str, Any]) -> None:
    """Writes the default policy into campus_auth using a cursor connected to that schema."""
    for role, spec in policy.get("roles", {}).items():
        cursor.execute(
            "INSERT INTO roles (name, description) VALUES (%s, %s)",
            (role, spec.get("description", "")),
        )
        role_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO role_grants (role_id, domain, scope) VALUES (%s, %s, %s)",
            [(role_id, domain, scope) for domain, scope in spec.get("grants", [])],
        )
    for group, spec in policy.get("groups", {}).items():
        cursor.execute(
            "INSERT INTO user_groups (name, description) VALUES (%s, %s)",
            (group, spec.get("description", "")),
        )
        group_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO group_grants (group_id, domain, scope) VALUES (%s, %s, %s)",
            [(group_id, domain, scope) for domain, scope in spec.get("grants", [])],
        )
