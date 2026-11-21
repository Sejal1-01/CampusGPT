import asyncio
import logging
from typing import TypeVar

from pydantic import BaseModel

from app.agent.models import ModelSlot, get_model
from app.config import MODEL_MAX_RETRIES

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class ModelUnavailableError(Exception):
    pass


async def structured_call[T: BaseModel](
    slot: ModelSlot, output_model: type[T], system_prompt: str, user_text: str
) -> T:
    messages = [{"role": "user", "content": [{"text": user_text}]}]
    last_error: Exception | None = None
    for attempt in range(MODEL_MAX_RETRIES):
        try:
            return await _single_call(slot, output_model, system_prompt, messages)
        except Exception as error:
            last_error = error
            logger.warning("structured call failed (attempt %s): %s", attempt + 1, error)
            await asyncio.sleep(2**attempt)
    raise ModelUnavailableError(str(last_error))


async def _single_call[T: BaseModel](
    slot: ModelSlot, output_model: type[T], system_prompt: str, messages: list
) -> T:
    output: T | None = None
    async for event in get_model(slot).structured_output(
        output_model, messages, system_prompt=system_prompt
    ):
        if "output" in event:
            output = event["output"]
    if output is None:
        raise ValueError("model returned no structured output")
    return output
