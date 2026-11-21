import asyncio

import pytest

from app.agent.fake_model import ScriptedTurn, ToolCall
from app.errors import AppError
from app.guardrails.classifier import GuardrailVerdict
from app.services.chat import ChatTrace, claim_session, stream_chat, validate_message

ANSWER = 'root = Answer([t])\nt = TextBlock("Hello")'


async def collect(session, message: str) -> tuple[list, ChatTrace]:
    trace = ChatTrace()
    events = [event async for event in stream_chat(session, message, trace)]
    return events, trace


def allow(fake_models) -> None:
    fake_models["fast"].structured = [GuardrailVerdict(label="allowed", reason="ok")]


async def test_plain_answer_streams_text_then_done(session, fake_models) -> None:
    allow(fake_models)
    fake_models["main"].turns = [ScriptedTurn(text=ANSWER)]
    events, trace = await collect(session, "hi")
    types = [event.type for event in events]
    assert types[0] == "status" and types[-1] == "done"
    assert "".join(event.delta or "" for event in events if event.type == "text") == ANSWER
    assert trace.text == ANSWER


async def test_tool_call_resets_interim_text_and_records_trace(session, fake_models) -> None:
    allow(fake_models)
    fake_models["main"].turns = [
        ScriptedTurn(
            text="Let me check", tool_calls=[ToolCall("describe_view", {"name": "my_marks"})]
        ),
        ScriptedTurn(text=ANSWER),
    ]
    events, trace = await collect(session, "show my marks")
    types = [event.type for event in events]
    assert types.index("reset") < types.index("tool")
    assert trace.tool_calls[0]["name"] == "describe_view"
    assert "my_marks" in session.described_views
    assert trace.text == ANSWER


async def test_guardrail_refusal_skips_agent(session, fake_models) -> None:
    fake_models["fast"].structured = [GuardrailVerdict(label="off_topic", reason="website")]
    events, trace = await collect(session, "Build me a website")
    assert [event.type for event in events] == ["status", "refusal", "done"]
    assert trace.refused_by_guardrail == "off_topic"
    assert session.agent.messages == []


async def test_model_failure_becomes_friendly_error(session, fake_models, monkeypatch) -> None:
    allow(fake_models)

    async def broken(*_args, **_kwargs):
        raise RuntimeError("429 quota")
        yield

    monkeypatch.setattr(fake_models["main"], "stream", broken)
    events, _trace = await collect(session, "hi")
    errors = [event for event in events if event.type == "error"]
    assert errors and "try again" in (errors[0].message or "")
    assert session.agent is None


async def test_empty_model_answer_is_reported(session, fake_models) -> None:
    allow(fake_models)
    fake_models["main"].turns = [ScriptedTurn(text="")]
    events, _trace = await collect(session, "hi")
    assert any(event.type == "error" and event.code == "empty_answer" for event in events)


@pytest.mark.parametrize("message", ["", "   ", "\n\t"])
def test_empty_message_rejected(message: str) -> None:
    with pytest.raises(AppError) as error:
        validate_message(message)
    assert error.value.status_code == 400


def test_long_message_rejected() -> None:
    with pytest.raises(AppError, match="2000"):
        validate_message("a" * 2001)


@pytest.mark.parametrize(
    "message", ["मेरा CGPA क्या है? 📊", "Mera attendance kitna hai 🙂", "DBMS 的 marks"]
)
def test_mixed_scripts_and_emoji_are_accepted(message: str) -> None:
    assert validate_message(message) == message


async def test_second_message_while_answering_is_busy(session) -> None:
    await session.lock.acquire()
    try:
        with pytest.raises(AppError) as error:
            claim_session(session)
        assert error.value.status_code == 409
    finally:
        session.lock.release()
    await asyncio.sleep(0)


async def test_parallel_tool_results_attach_to_their_own_call(session, fake_models) -> None:
    allow(fake_models)
    fake_models["main"].turns = [
        ScriptedTurn(
            tool_calls=[
                ToolCall("describe_view", {"name": "my_marks"}),
                ToolCall("describe_view", {"name": "my_attendance"}),
            ]
        ),
        ScriptedTurn(text=ANSWER),
    ]
    _events, trace = await collect(session, "marks and attendance")
    assert "View my_marks" in trace.tool_calls[0]["output"]
    assert "View my_attendance" in trace.tool_calls[1]["output"]
