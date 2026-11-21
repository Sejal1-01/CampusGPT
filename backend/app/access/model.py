from dataclasses import dataclass, field

from app.sql.registry import DOMAINS, SCOPES, Grant

COLLEGE_WIDE_ROLES = frozenset({"dean", "admin"})
WALLED_DOMAINS = frozenset({"academics", "teaching_feedback"})


class AccessError(Exception):
    pass


@dataclass(frozen=True)
class GrantSource:
    domain: str
    scope: str
    source: str
    name: str


@dataclass(frozen=True)
class EffectiveAccess:
    roles: tuple[str, ...]
    grants: frozenset[Grant]
    sources: tuple[GrantSource, ...] = field(default=())


def validate_grant(domain: str, scope: str) -> None:
    if domain not in DOMAINS:
        raise AccessError(f"Unknown data domain '{domain}'. Valid: {', '.join(DOMAINS)}.")
    if scope not in SCOPES:
        raise AccessError(f"Unknown scope '{scope}'. Valid: {', '.join(SCOPES)}.")


def breaks_department_wall(domain: str, scope: str) -> bool:
    return domain in WALLED_DOMAINS and scope == "college"


def check_department_wall(
    domain: str, scope: str, holder_roles: list[set[str]], target: str
) -> None:
    if not breaks_department_wall(domain, scope):
        return
    for roles in holder_roles:
        if not roles & COLLEGE_WIDE_ROLES:
            raise AccessError(
                f"Department wall: ({domain}, college) can only be held by a Dean or Admin; "
                f"{target} includes someone who is neither."
            )
