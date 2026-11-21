import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(REPO_ROOT / ".env")

MAX_RESULT_ROWS = 500
MAX_ROWS_TO_MODEL = 200
QUERY_TIMEOUT_MS = 5000
CONVERSATION_WINDOW_MESSAGES = 20
MAX_MESSAGE_CHARS = 2000
MAX_SESSIONS = 200
SESSION_IDLE_MINUTES = 60
MAX_STORED_RESULTS = 20
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_TEXT_CHARS = 50_000
MODEL_MAX_RETRIES = 3
SQL_MAX_RETRIES = 1
ATTENDANCE_THRESHOLD_PERCENT = 75
INTERNAL_FAIL_PERCENT = 40
SGPA_DROP_THRESHOLD = 1.0
TAGGING_CONCURRENCY = 2
TAGGING_BATCH_SIZE = 20
SESSION_COOKIE_NAME = "campusgpt_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 8 * 60 * 60
SEARCH_MAX_RESULTS = 5
GUARDRAIL_TIMEOUT_SECONDS = 8
MAX_STUDY_PLAN_DAYS = 21
REVISION_DELAY_TURNS = 2
MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 20_000
MAX_CSV_COLUMNS = 50
SQLITE_MAX_STEPS = 5_000_000
MAX_PAPER_MARKS = 200
THINKING_LEVEL_MAIN = "low"
THINKING_LEVEL_FAST = "minimal"

COLLEGE_NAME = "IIIT Bhagalpur"
CURRENT_ACADEMIC_YEAR = "2026-27"
CURRENT_TERM = "odd"


@dataclass(frozen=True)
class MySqlAccount:
    user: str
    password: str


@dataclass(frozen=True)
class Settings:
    model_provider: str
    model_id_main: str
    model_id_fast: str
    model_fallback_ids: tuple[str, ...]
    gemini_api_key: str
    aws_region: str
    tavily_api_key: str
    mysql_host: str
    mysql_port: int
    mysql_db: str
    mysql_auth_db: str
    readonly_account: MySqlAccount
    app_account: MySqlAccount
    auth_rw_account: MySqlAccount
    root_password: str
    platform_admin_password: str
    session_secret: str
    app_today: date


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings(
        model_provider=_env("MODEL_PROVIDER", "gemini"),
        model_id_main=_env("MODEL_ID_MAIN"),
        model_id_fast=_env("MODEL_ID_FAST"),
        model_fallback_ids=tuple(
            name.strip() for name in _env("MODEL_FALLBACK_IDS").split(",") if name.strip()
        ),
        gemini_api_key=_env("GEMINI_API_KEY"),
        aws_region=_env("AWS_REGION"),
        tavily_api_key=_env("TAVILY_API_KEY"),
        mysql_host=_env("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(_env("MYSQL_PORT", "3306")),
        mysql_db=_env("MYSQL_DB", "campus"),
        mysql_auth_db=_env("MYSQL_AUTH_DB", "campus_auth"),
        readonly_account=MySqlAccount(_env("MYSQL_RO_USER"), _env("MYSQL_RO_PASSWORD")),
        app_account=MySqlAccount(_env("MYSQL_APP_USER"), _env("MYSQL_APP_PASSWORD")),
        auth_rw_account=MySqlAccount(_env("MYSQL_AUTH_RW_USER"), _env("MYSQL_AUTH_RW_PASSWORD")),
        root_password=_env("MYSQL_ROOT_PASSWORD"),
        platform_admin_password=_env("PLATFORM_ADMIN_PASSWORD"),
        session_secret=_env("SESSION_SECRET"),
        app_today=date.fromisoformat(_env("APP_TODAY", "2026-11-11")),
    )
