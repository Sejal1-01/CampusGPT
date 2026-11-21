from typing import Literal

from strands.models import Model

from app.agent.fallback import FallbackModel
from app.config import THINKING_LEVEL_FAST, THINKING_LEVEL_MAIN, get_settings

ModelSlot = Literal["main", "fast"]

_override: dict[ModelSlot, Model] = {}


def set_model_override(slot: ModelSlot, model: Model | None) -> None:
    """Lets tests inject a FakeModel at the get_model() boundary."""
    if model is None:
        _override.pop(slot, None)
    else:
        _override[slot] = model


def get_model(slot: ModelSlot) -> Model:
    if slot in _override:
        return _override[slot]
    settings = get_settings()
    primary = settings.model_id_main if slot == "main" else settings.model_id_fast
    names = [primary] + [name for name in settings.model_fallback_ids if name != primary]
    if len(names) == 1:
        return _build(slot, primary)
    return FallbackModel([_build(slot, name) for name in names], names)


def _build(slot: ModelSlot, model_id: str) -> Model:
    settings = get_settings()
    if settings.model_provider == "bedrock":
        from strands.models.bedrock import BedrockModel

        temperature = 0.2 if slot == "main" else 0.0
        return BedrockModel(
            model_id=model_id, region_name=settings.aws_region or None, temperature=temperature
        )
    if settings.model_provider == "gemini":
        from strands.models.gemini import GeminiModel

        level = THINKING_LEVEL_MAIN if slot == "main" else THINKING_LEVEL_FAST
        params = (
            {"thinking_config": {"thinking_level": level}} if model_id.startswith("gemini") else {}
        )
        return GeminiModel(
            client_args={"api_key": settings.gemini_api_key}, model_id=model_id, params=params
        )
    raise ValueError(f"Unknown MODEL_PROVIDER '{settings.model_provider}'")
