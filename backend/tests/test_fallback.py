import pytest

from app.agent.fake_model import FakeModel, ScriptedTurn
from app.agent.fallback import FallbackModel, is_retriable
from app.guardrails.classifier import GuardrailVerdict


class BrokenModel(FakeModel):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    async def stream(self, *_args, **_kwargs):
        raise RuntimeError(self.message)
        yield

    async def structured_output(self, *_args, **_kwargs):
        raise RuntimeError(self.message)
        yield


async def collect(model, *args):
    return [event async for event in model.stream(*args)]


async def test_overloaded_model_falls_back_to_next() -> None:
    backup = FakeModel(turns=[ScriptedTurn(text="hello")])
    model = FallbackModel([BrokenModel("503 UNAVAILABLE"), backup], ["a", "b"])
    events = await collect(model, [], None, None)
    assert any("contentBlockDelta" in event for event in events)


async def test_quota_error_falls_back_for_structured_output() -> None:
    verdict = GuardrailVerdict(label="allowed", reason="ok")
    model = FallbackModel(
        [BrokenModel("429 RESOURCE_EXHAUSTED"), FakeModel(structured=[verdict])], ["a", "b"]
    )
    outputs = [event async for event in model.structured_output(GuardrailVerdict, [])]
    assert outputs[-1]["output"] == verdict


async def test_non_retriable_error_is_raised() -> None:
    model = FallbackModel([BrokenModel("400 INVALID_ARGUMENT"), FakeModel()], ["a", "b"])
    with pytest.raises(RuntimeError, match="400"):
        await collect(model, [], None, None)


async def test_last_model_error_is_raised() -> None:
    model = FallbackModel([BrokenModel("503"), BrokenModel("503 again")], ["a", "b"])
    with pytest.raises(RuntimeError, match="again"):
        await collect(model, [], None, None)


def test_retriable_detection() -> None:
    assert is_retriable(RuntimeError("503 UNAVAILABLE"))
    assert not is_retriable(ValueError("bad schema"))
