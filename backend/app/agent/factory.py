from functools import cache

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

from app.agent.models import get_model
from app.agent.prompt_files import PROMPTS_DIR, render_prompt
from app.agent.tools.build import build_tools
from app.agent.tools.stretch import stretch_tool_help
from app.config import (
    COLLEGE_NAME,
    CONVERSATION_WINDOW_MESSAGES,
    CURRENT_ACADEMIC_YEAR,
    CURRENT_TERM,
    get_settings,
)
from app.services.dates import date_ranges_text
from app.services.portal_data import join_map_text, list_views_text
from app.sessions import Session
from app.user_context import UserContext

OPENUI_LIBRARY_FILE = PROMPTS_DIR / "openui_library.txt"


def _openui_library() -> str:
    if OPENUI_LIBRARY_FILE.exists():
        return OPENUI_LIBRARY_FILE.read_text(encoding="utf-8")
    return "(component library prompt missing: run `npm run gen:prompt` in frontend/)"


@cache
def _system_prompt_cached(
    display_name: str, roles: str, department: str, view_names: tuple[str, ...], extra_tools: str
) -> str:
    from app.sql.views import all_views

    views = {name: all_views()[name] for name in view_names}
    return render_prompt(
        "system.md",
        college=COLLEGE_NAME,
        display_name=display_name,
        roles=roles,
        department=department,
        today=get_settings().app_today.isoformat(),
        date_ranges=date_ranges_text(get_settings().app_today),
        term=CURRENT_TERM,
        academic_year=CURRENT_ACADEMIC_YEAR,
        view_list=list_views_text(views) or "(none)",
        join_map=join_map_text(views) or "(no joins)",
        extra_tools=extra_tools,
        openui_library=_openui_library(),
    )


def system_prompt_for(user: UserContext, extra_tools: str = "") -> str:
    return _system_prompt_cached(
        user.display_name,
        ", ".join(user.roles) or "none",
        user.department or "all departments",
        tuple(sorted(user.views)),
        extra_tools,
    )


def create_agent(session: Session) -> Agent:
    tools = build_tools(session)
    return Agent(
        model=get_model("main"),
        tools=tools,
        system_prompt=system_prompt_for(session.user, stretch_tool_help(tools)),
        conversation_manager=SlidingWindowConversationManager(
            window_size=CONVERSATION_WINDOW_MESSAGES
        ),
        callback_handler=None,
    )
