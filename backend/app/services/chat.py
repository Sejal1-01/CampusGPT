import asyncio
import contextlib
import json
import logging
import threading
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from app.agent.factory import create_agent
from app.config import MAX_MESSAGE_CHARS
from app.errors import AppError
from app.guardrails.classifier import GuardrailVerdict, classify, refusal_text
from app.learning.quiz import revision_due
from app.schemas import ChatEvent
from app.sessions import Session

logger = logging.getLogger(__name__)
FRIENDLY_MODEL_ERROR = "The AI service didn't respond. Please try again in a minute."
EMPTY_ANSWER = "I couldn't produce an answer. Please rephrase the question."
REVISION_NOTE = (
    "\n\n[System note: {count} question(s) the student answered wrongly earlier are due for "
    "revision. After answering, call revision_quiz() and add its QuizCard with a one-line intro.]"
)


def with_revision_note(session: Session, message: str) -> str:
    session.turns += 1
    if not revision_due(session):
        return message
    return message + REVISION_NOTE.format(count=len(session.revision_questions))


@dataclass
class ChatTrace:
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    text: str = ""
    refused_by_guardrail: str | None = None
    first_token_ms: int | None = None
    total_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


def validate_message(message: str) -> str:
    text = message.strip()
    if not text:
        raise AppError("empty_message", "Type a question first.", 400)
    if len(text) > MAX_MESSAGE_CHARS:
        raise AppError(
            "message_too_long", f"Messages can be at most {MAX_MESSAGE_CHARS} characters.", 400
        )
    return text


def claim_session(session: Session) -> None:
    if session.lock.locked():
        raise AppError("busy", "Still answering your previous question.", 409)


class _TurnState:
    def __init__(self, trace: ChatTrace, started: float) -> None:
        self.trace = trace
        self.started = started
        self.seen_tools: set[str] = set()
        self.current_text: list[str] = []

    def on_text(self, delta: str) -> ChatEvent:
        if self.trace.first_token_ms is None:
            self.trace.first_token_ms = int((time.monotonic() - self.started) * 1000)
        self.current_text.append(delta)
        return ChatEvent(type="text", delta=delta)

    def on_tool(self, tool_use: dict[str, Any]) -> list[ChatEvent]:
        tool_id = tool_use.get("toolUseId", "")
        if tool_id in self.seen_tools:
            return []
        self.seen_tools.add(tool_id)
        self.current_text.clear()
        return [
            ChatEvent(type="reset"),
            ChatEvent(type="tool", name=tool_use.get("name"), status="start"),
        ]

    def on_message(self, message: dict[str, Any]) -> list[ChatEvent]:
        events: list[ChatEvent] = []
        for block in message.get("content", []):
            if "toolUse" in block:
                use = block["toolUse"]
                self.trace.tool_calls.append(
                    {"id": use.get("toolUseId"), "name": use.get("name"), "input": use.get("input")}
                )
            if "toolResult" in block:
                self._attach_result(block["toolResult"])
                events.append(ChatEvent(type="tool", status="end"))
        return events

    def _attach_result(self, result: dict[str, Any]) -> None:
        texts = [item.get("text", "") for item in result.get("content", []) if "text" in item]
        for call in self.trace.tool_calls:
            if call.get("id") == result.get("toolUseId") and "output" not in call:
                call["output"] = "\n".join(texts)
                return

    def on_result(self, result: Any) -> None:
        usage = getattr(getattr(result, "metrics", None), "accumulated_usage", {}) or {}
        self.trace.input_tokens = int(usage.get("inputTokens", 0))
        self.trace.output_tokens = int(usage.get("outputTokens", 0))


def _translate(event: dict[str, Any], state: _TurnState) -> list[ChatEvent]:
    if "data" in event and isinstance(event["data"], str) and event["data"]:
        return [state.on_text(event["data"])]
    if "current_tool_use" in event and event["current_tool_use"].get("toolUseId"):
        return state.on_tool(event["current_tool_use"])
    if "message" in event and isinstance(event["message"], dict):
        return state.on_message(event["message"])
    if "result" in event:
        state.on_result(event["result"])
    return []


async def stream_chat(session: Session, message: str, trace: ChatTrace) -> AsyncIterator[ChatEvent]:
    started = time.monotonic()
    async with session.lock:
        yield ChatEvent(type="status", text="Checking your question")
        async for event in _guarded_answer(session, message, trace, started):
            yield event
        trace.total_ms = int((time.monotonic() - started) * 1000)
        _log_turn(session, trace)
        yield ChatEvent(type="done", latency_ms=trace.total_ms)


async def _guarded_answer(
    session: Session, message: str, trace: ChatTrace, started: float
) -> AsyncIterator[ChatEvent]:
    """Runs the guardrail alongside the agent; agent output is held back until the check passes."""
    if session.agent is None:
        session.agent = create_agent(session)
    history = list(session.agent.messages)
    cancel = threading.Event()
    queue: asyncio.Queue[ChatEvent | None] = asyncio.Queue()
    prompt = with_revision_note(session, message)
    agent_task = asyncio.create_task(_pump(session, prompt, trace, started, cancel, queue))
    verdict = await classify(message)
    refusal = refusal_text(verdict)
    if refusal:
        await _abort_agent(session, agent_task, cancel, history)
        yield _refuse(session, trace, verdict, refusal)
        return
    while (event := await queue.get()) is not None:
        yield event
    await agent_task


async def _pump(
    session: Session,
    message: str,
    trace: ChatTrace,
    started: float,
    cancel: threading.Event,
    queue: asyncio.Queue[ChatEvent | None],
) -> None:
    try:
        async for event in _run_agent(session, message, trace, started, cancel):
            await queue.put(event)
    finally:
        await queue.put(None)


async def _abort_agent(
    session: Session, agent_task: asyncio.Task[None], cancel: threading.Event, history: list
) -> None:
    cancel.set()
    agent_task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await agent_task
    if session.agent is not None:
        session.agent.messages[:] = history


def _refuse(
    session: Session, trace: ChatTrace, verdict: GuardrailVerdict, refusal: str
) -> ChatEvent:
    trace.refused_by_guardrail = verdict.label
    trace.tool_calls.clear()
    trace.text = refusal
    logger.info("user=%s guardrail=%s", session.user.user_id, verdict.label)
    return ChatEvent(type="refusal", text=refusal)


async def _run_agent(
    session: Session, message: str, trace: ChatTrace, started: float, cancel: threading.Event
) -> AsyncIterator[ChatEvent]:
    agent = session.agent
    state = _TurnState(trace, started)
    try:
        async for raw in agent.stream_async(message, cancel_signal=cancel):
            for event in _translate(raw, state):
                yield event
    except (asyncio.CancelledError, GeneratorExit):
        raise
    except Exception:
        logger.exception("user=%s agent failed", session.user.user_id)
        session.agent = None
        yield ChatEvent(type="error", code="model_error", message=FRIENDLY_MODEL_ERROR)
        return
    trace.text = "".join(state.current_text)
    if not trace.text.strip() and not cancel.is_set():
        yield ChatEvent(type="error", code="empty_answer", message=EMPTY_ANSWER)


def _log_turn(session: Session, trace: ChatTrace) -> None:
    logger.info(
        "user=%s tools=%s ttft_ms=%s total_ms=%s tokens_in=%s tokens_out=%s",
        session.user.user_id,
        json.dumps([call["name"] for call in trace.tool_calls]),
        trace.first_token_ms,
        trace.total_ms,
        trace.input_tokens,
        trace.output_tokens,
    )
