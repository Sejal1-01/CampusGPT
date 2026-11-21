from fastapi import APIRouter, Response

from app.auth import CurrentSession, login, sign_session_id
from app.config import SESSION_COOKIE_MAX_AGE_SECONDS, SESSION_COOKIE_NAME
from app.schemas import DemoAccount, LoginRequest, Me, OkResponse
from app.services.starters import DEMO_ACCOUNTS, starter_questions
from app.sessions import Session, store

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def me_from_session(session: Session) -> Me:
    user = session.user
    return Me(
        username=user.username,
        display_name=user.display_name,
        roles=list(user.roles) or (["platform_admin"] if user.is_platform_admin else []),
        department=user.department,
        is_platform_admin=user.is_platform_admin,
        allowed_areas=user.allowed_areas,
        starter_questions=[] if user.is_platform_admin else starter_questions(user.roles),
    )


@router.get("/demo-accounts", response_model=list[DemoAccount])
def demo_accounts() -> list[DemoAccount]:
    """Seeded demo accounts listed on the login page."""
    return [DemoAccount(**item) for item in DEMO_ACCOUNTS]


@router.post("/login", response_model=Me)
def login_route(body: LoginRequest, response: Response) -> Me:
    """Log in and set the session cookie."""
    session = login(body.username.strip(), body.password)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        sign_session_id(session.session_id),
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return me_from_session(session)


@router.post("/logout", response_model=OkResponse)
def logout_route(response: Response, session: CurrentSession) -> OkResponse:
    """Log out; clears the session and chat history."""
    store.remove(session.session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return OkResponse()


@router.get("/me", response_model=Me)
def me_route(session: CurrentSession) -> Me:
    """Current user's name, data roles and allowed areas."""
    return me_from_session(session)
