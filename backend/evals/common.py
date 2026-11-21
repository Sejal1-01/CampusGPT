import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.agent.prompt_files import render_prompt
from app.agent.structured import ModelUnavailableError, structured_call
from app.auth import authenticate
from app.config import get_settings
from app.schemas import StoredResult
from app.services.chat import ChatTrace, stream_chat
from app.sessions import Session

logger = logging.getLogger("evals")
DATASETS = Path(__file__).with_name("datasets")
DEMO_PASSWORD = "demo123"
MIN_INTERVAL_SECONDS = float(os.environ.get("EVAL_MIN_INTERVAL_SECONDS", "4"))
CASE_RETRIES = 3
RETRY_WAIT_SECONDS = 20
_last_call = [0.0]


def load_dataset(name: str) -> Any:
    return json.loads((DATASETS / name).read_text(encoding="utf-8"))


def new_session(username: str) -> Session:
    password = (
        get_settings().platform_admin_password if username == "platform_admin" else DEMO_PASSWORD
    )
    return Session(
        session_id=f"eval-{username}-{time.monotonic_ns()}", user=authenticate(username, password)
    )


@dataclass
class TurnOutcome:
    trace: ChatTrace
    events: list[dict[str, Any]]
    new_results: list[StoredResult] = field(default_factory=list)
    error: str | None = None

    @property
    def exposed_data(self) -> str:
        return json.dumps(
            [{"columns": item.columns, "rows": item.rows} for item in self.new_results],
            ensure_ascii=False,
            default=str,
        )

    @property
    def exposed_all(self) -> str:
        return self.trace.text + "\n" + self.exposed_data

    @property
    def first_tool(self) -> str:
        return self.trace.tool_calls[0]["name"] if self.trace.tool_calls else "none"


async def _throttle() -> None:
    wait = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_call[0])
    if wait > 0:
        await asyncio.sleep(wait)
    _last_call[0] = time.monotonic()


async def run_turn(session: Session, prompt: str) -> TurnOutcome:
    outcome = TurnOutcome(trace=ChatTrace(), events=[])
    for attempt in range(CASE_RETRIES):
        await _throttle()
        before = set(session.results)
        outcome = TurnOutcome(trace=ChatTrace(), events=[])
        async for event in stream_chat(session, prompt, outcome.trace):
            outcome.events.append(event.model_dump(exclude_none=True))
        errors = [item for item in outcome.events if item["type"] == "error"]
        outcome.new_results = [item for key, item in session.results.items() if key not in before]
        if not errors or errors[0].get("code") != "model_error":
            outcome.error = errors[0]["message"] if errors else None
            return outcome
        logger.warning("model error, retrying in %ss (attempt %s)", RETRY_WAIT_SECONDS, attempt + 1)
        await asyncio.sleep(RETRY_WAIT_SECONDS * (attempt + 1))
    outcome.error = "model_error after retries"
    return outcome


class JudgeVerdict(BaseModel):
    passed: bool
    reason: str


async def judge(rubric: str, material: str) -> JudgeVerdict:
    await _throttle()
    try:
        return await structured_call(
            "fast", JudgeVerdict, render_prompt("judge.md", rubric=rubric), material
        )
    except ModelUnavailableError as error:
        return JudgeVerdict(passed=False, reason=f"judge unavailable: {error}")


CHART_PATTERN = re.compile(r'DataChart\(\s*"([^"]+)"\s*,\s*"([a-z_]+)"')
INSIGHT_PATTERN = re.compile(r'Insight\(\s*"((?:[^"\\]|\\.)*)"')


def chart_kinds(text: str) -> list[str]:
    kinds = [match.group(2) for match in CHART_PATTERN.finditer(text)]
    if "StatCards(" in text or "StatCard(" in text:
        kinds.append("stat")
    if "DataTable(" in text:
        kinds.append("table")
    return kinds


def insights(text: str) -> list[str]:
    return [match.group(1) for match in INSIGHT_PATTERN.finditer(text)]


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]
