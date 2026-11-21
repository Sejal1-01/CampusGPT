import json
from collections.abc import AsyncGenerator, AsyncIterable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel
from strands.models import Model


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ScriptedTurn:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class FakeModel(Model):
    """Scripted model for tests: replays turns and structured outputs without any network call."""

    def __init__(
        self,
        turns: list[ScriptedTurn] | None = None,
        structured: list[BaseModel] | None = None,
    ) -> None:
        self.turns = list(turns or [])
        self.structured = list(structured or [])
        self.calls: list[dict[str, Any]] = []
        self.config: dict[str, Any] = {"model_id": "fake"}

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return self.config

    async def structured_output(
        self,
        output_model: type[BaseModel],
        prompt: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        self.calls.append({"structured": output_model.__name__, "prompt": prompt})
        if not self.structured:
            raise AssertionError(f"FakeModel has no scripted {output_model.__name__}")
        yield {"output": self.structured.pop(0)}

    async def stream(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[dict[str, Any]]:
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        turn = self.turns.pop(0) if self.turns else ScriptedTurn(text="")
        yield {"messageStart": {"role": "assistant"}}
        if turn.text:
            yield {"contentBlockStart": {"start": {}}}
            for index in range(0, len(turn.text), 20):
                yield {"contentBlockDelta": {"delta": {"text": turn.text[index : index + 20]}}}
            yield {"contentBlockStop": {}}
        for number, call in enumerate(turn.tool_calls):
            start = {
                "toolUse": {"name": call.name, "toolUseId": f"tool_{len(self.calls)}_{number}"}
            }
            yield {"contentBlockStart": {"start": start}}
            yield {
                "contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(call.arguments)}}}
            }
            yield {"contentBlockStop": {}}
        stop_reason = "tool_use" if turn.tool_calls else "end_turn"
        yield {"messageStop": {"stopReason": stop_reason}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 10, "outputTokens": 10, "totalTokens": 20},
                "metrics": {"latencyMs": 1},
            }
        }
