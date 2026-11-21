from typing import Annotated

import bcrypt
from fastapi import Depends, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.access import repository
from app.access.resolver import allowed_views, effective_access
from app.config import SESSION_COOKIE_MAX_AGE_SECONDS, SESSION_COOKIE_NAME, get_settings
from app.db import Account, fetch_one
from app.errors import AppError
from app.sessions import Session, store
from app.sql.rewrite import ScopeParameters
from app.user_context import UserContext

INVALID_LOGIN = AppError("invalid_login", "Wrong username or password.", 401)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="campusgpt-session")


def sign_session_id(session_id: str) -> str:
    return _serializer().dumps(session_id)


def read_session_id(cookie: str) -> str | None:
    try:
        return str(_serializer().loads(cookie, max_age=SESSION_COOKIE_MAX_AGE_SECONDS))
    except BadSignature:
        return None


def authenticate(username: str, password: str) -> UserContext:
    row = repository.find_user_by_username(username)
    if row is None:
        bcrypt.checkpw(b"timing-equaliser", bcrypt.hashpw(b"x", bcrypt.gensalt(4)))
        raise INVALID_LOGIN
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        raise INVALID_LOGIN
    return build_user_context(row)


def _department_code(dept_id: int | None) -> str | None:
    if dept_id is None:
        return None
    row = fetch_one(Account.APP, "SELECT code FROM departments WHERE id = %s", (dept_id,))
    return row["code"] if row else None


def build_user_context(row: dict) -> UserContext:
    scope = ScopeParameters(
        student_id=row["student_id"],
        faculty_id=row["faculty_id"],
        dept_id=row["dept_id"],
        today=get_settings().app_today,
    )
    if row["is_platform_admin"]:
        access_roles: tuple[str, ...] = ()
        grants: frozenset = frozenset()
    else:
        access = effective_access(int(row["id"]))
        access_roles, grants = access.roles, access.grants
    return UserContext(
        user_id=int(row["id"]),
        username=row["username"],
        display_name=row["display_name"],
        roles=access_roles,
        department=_department_code(row["dept_id"]),
        is_platform_admin=bool(row["is_platform_admin"]),
        scope=scope,
        grants=grants,
        views=allowed_views(grants, scope.available()),
    )


def login(username: str, password: str) -> Session:
    return store.create(authenticate(username, password))


def current_session(request: Request) -> Session:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_id = read_session_id(cookie) if cookie else None
    session = store.get(session_id) if session_id else None
    if session is None:
        raise AppError("unauthenticated", "Your session has expired. Please log in again.", 401)
    return session


def chat_session(request: Request) -> Session:
    session = current_session(request)
    if session.user.is_platform_admin:
        raise AppError("forbidden", "The platform admin account has no chat access.", 403)
    return session


def platform_admin_session(request: Request) -> Session:
    session = current_session(request)
    if not session.user.is_platform_admin:
        raise AppError("forbidden", "Only the platform admin can manage access.", 403)
    return session


CurrentSession = Annotated[Session, Depends(current_session)]
ChatSession = Annotated[Session, Depends(chat_session)]
PlatformAdminSession = Annotated[Session, Depends(platform_admin_session)]
