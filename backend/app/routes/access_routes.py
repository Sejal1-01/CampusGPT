from fastapi import APIRouter

from app.access import repository, service
from app.access.model import AccessError
from app.access.resolver import allowed_views, effective_access
from app.auth import PlatformAdminSession
from app.db import Account, execute
from app.errors import AppError
from app.schemas import (
    AccessOverview,
    AuditEntry,
    EffectiveAccessResponse,
    GrantRequest,
    GrantRow,
    GrantSourceRow,
    GroupCreateRequest,
    GroupSummary,
    MemberRequest,
    OkResponse,
    PasswordRequest,
    RoleAssignRequest,
    RoleSummary,
    UserCreateRequest,
    UserSummary,
)
from app.sql.registry import DOMAINS, SCOPES

router = APIRouter(prefix="/api/access", tags=["Access"])


def _run(action: object, *args: object) -> OkResponse:
    try:
        action(*args)  # type: ignore[operator]
    except AccessError as error:
        raise AppError("access_rejected", str(error), 400) from error
    return OkResponse()


def _grants(rows: list[list[str]]) -> list[GrantRow]:
    return [GrantRow(domain=domain, scope=scope) for domain, scope in rows]


@router.get("/overview", response_model=AccessOverview)
def overview(session: PlatformAdminSession) -> AccessOverview:
    """Roles, groups, users, data domains and scopes."""
    roles = [
        RoleSummary(
            name=row["name"],
            description=row["description"],
            grants=_grants(row["grants"]),
            members=row["members"],
        )
        for row in service.list_roles()
    ]
    groups = [
        GroupSummary(
            name=row["name"],
            description=row["description"],
            grants=_grants(row["grants"]),
            members=row["members"],
        )
        for row in service.list_groups()
    ]
    users = [
        UserSummary(
            username=row["username"],
            display_name=row["display_name"],
            is_platform_admin=bool(row["is_platform_admin"]),
        )
        for row in service.list_users()
    ]
    return AccessOverview(
        roles=roles, groups=groups, users=users, domains=list(DOMAINS), scopes=list(SCOPES)
    )


@router.get("/users/{username}/effective", response_model=EffectiveAccessResponse)
def effective(username: str, session: PlatformAdminSession) -> EffectiveAccessResponse:
    """A user's effective access and where each grant came from."""
    row = repository.find_user_by_username(username)
    if row is None:
        raise AppError("not_found", f"No user named '{username}'.", 404)
    access = effective_access(int(row["id"]))
    available = {key for key in ("student_id", "faculty_id", "dept_id") if row[key] is not None}
    sources = [
        GrantSourceRow(domain=item.domain, scope=item.scope, source=item.source, name=item.name)  # type: ignore[arg-type]
        for item in access.sources
    ]
    views = sorted(allowed_views(access.grants, available))
    return EffectiveAccessResponse(
        username=username, roles=list(access.roles), grants=sources, views=views
    )


@router.post("/groups", response_model=OkResponse)
def create_group(body: GroupCreateRequest, session: PlatformAdminSession) -> OkResponse:
    """Create a user group."""
    return _run(service.create_group, body.name, body.description, session.user.user_id)


@router.delete("/groups/{name}", response_model=OkResponse)
def delete_group(name: str, session: PlatformAdminSession) -> OkResponse:
    """Delete a user group."""
    return _run(service.delete_group, name, session.user.user_id)


@router.post("/groups/{name}/members", response_model=OkResponse)
def add_member(name: str, body: MemberRequest, session: PlatformAdminSession) -> OkResponse:
    """Add a user to a group."""
    return _run(service.add_member, name, body.username, session.user.user_id)


@router.delete("/groups/{name}/members/{username}", response_model=OkResponse)
def remove_member(name: str, username: str, session: PlatformAdminSession) -> OkResponse:
    """Remove a user from a group."""
    return _run(service.remove_member, name, username, session.user.user_id)


@router.post("/grants", response_model=OkResponse)
def add_grant(body: GrantRequest, session: PlatformAdminSession) -> OkResponse:
    """Grant a (domain, scope) to a role, group or user."""
    return _run(
        service.grant, body.kind, body.target, body.domain, body.scope, session.user.user_id
    )


@router.post("/grants/revoke", response_model=OkResponse)
def revoke_grant(body: GrantRequest, session: PlatformAdminSession) -> OkResponse:
    """Revoke a (domain, scope) from a role, group or user."""
    return _run(
        service.revoke, body.kind, body.target, body.domain, body.scope, session.user.user_id
    )


@router.post("/users/{username}/roles", response_model=OkResponse)
def assign_role(
    username: str, body: RoleAssignRequest, session: PlatformAdminSession
) -> OkResponse:
    """Assign a role to a user."""
    return _run(service.assign_role, username, body.role, session.user.user_id)


@router.delete("/users/{username}/roles/{role}", response_model=OkResponse)
def unassign_role(username: str, role: str, session: PlatformAdminSession) -> OkResponse:
    """Remove a role from a user."""
    return _run(service.unassign_role, username, role, session.user.user_id)


@router.post("/users", response_model=OkResponse)
def create_user(body: UserCreateRequest, session: PlatformAdminSession) -> OkResponse:
    """Create a user (no roles until assigned)."""
    if repository.find_user_by_username(body.username):
        raise AppError("access_rejected", f"User '{body.username}' already exists.", 400)
    execute(
        Account.AUTH_RW,
        "INSERT INTO users (username, display_name, password_hash, student_id, faculty_id, dept_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            body.username,
            body.display_name,
            service.hash_password(body.password),
            body.student_id,
            body.faculty_id,
            body.dept_id,
        ),
    )
    repository.audit(session.user.user_id, "create_user", f"user:{body.username}", "")
    return OkResponse()


@router.post("/users/{username}/password", response_model=OkResponse)
def set_password(username: str, body: PasswordRequest, session: PlatformAdminSession) -> OkResponse:
    """Reset a user's password."""
    if repository.find_user_by_username(username) is None:
        raise AppError("not_found", f"No user named '{username}'.", 404)
    return _run(service.set_password, username, body.password, session.user.user_id)


@router.get("/audit", response_model=list[AuditEntry])
def audit(session: PlatformAdminSession) -> list[AuditEntry]:
    """Recent access changes: who changed which grant, and when."""
    return [
        AuditEntry(
            id=row["id"],
            changed_by=row["changed_by"],
            action=row["action"],
            target=row["target"],
            details=row["details"],
            changed_at=row["changed_at"].isoformat(),
        )
        for row in service.audit_log()
    ]
