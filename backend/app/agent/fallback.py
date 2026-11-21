import logging
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from pydantic import BaseModel
from strands.models import Model

logger = logging.getLogger(__name__)
RETRIABLE_MARKERS = (
    "429",
    "500",
    "503",
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "INTERNAL",
    "Throttl",
)


def is_retriable(error: Exception) -> bool:
    text = f"{type(error).__name__} {error}"
    return any(marker in text for marker in RETRIABLE_MARKERS)


class FallbackModel(Model):
    """Tries each model in order; moves on when one is overloaded or out of free-tier quota."""

    def __init__(self, models: list[Model], names: list[str]) -> None:
        self.models = models
        self.names = names

    def update_config(self, **model_config: Any) -> None:
        self.models[0].update_config(**model_config)

    def get_config(self) -> Any:
        return self.models[0].get_config()

    async def stream(
        self, messages: Any, tool_specs: Any = None, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncIterable[Any]:
        for index, model in enumerate(self.models):
            started = False
            try:
                async for event in model.stream(messages, tool_specs, system_prompt, **kwargs):
                    started = True
                    yield event
                return
            except Exception as error:
                if started or index == len(self.models) - 1 or not is_retriable(error):
                    raise
                logger.warning(
                    "model %s unavailable (%s); trying %s",
                    self.names[index],
                    str(error)[:80],
                    self.names[index + 1],
                )

    async def structured_output(
        self,
        output_model: type[BaseModel],
        prompt: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        for index, model in enumerate(self.models):
            try:
                async for event in model.structured_output(
                    output_model, prompt, system_prompt=system_prompt, **kwargs
                ):
                    yield event
                return
            except Exception as error:
                if index == len(self.models) - 1 or not is_retriable(error):
                    raise
                logger.warning(
                    "model %s unavailable (%s); trying %s",
                    self.names[index],
                    str(error)[:80],
                    self.names[index + 1],
                )
