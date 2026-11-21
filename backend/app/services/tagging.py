from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.agent.prompt_files import render_prompt
from app.agent.structured import structured_call
from app.sql.views import COMPLAINT_THEMES, TEACHING_THEMES

Kind = Literal["feedback", "complaint"]
THEMES_BY_KIND: dict[str, tuple[str, ...]] = {
    "feedback": TEACHING_THEMES,
    "complaint": COMPLAINT_THEMES,
}
LABELS = {"feedback": "teaching feedback comment", "complaint": "hostel/mess/campus complaint"}


class TagResult(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    themes: list[str] = Field(min_length=1)
    summary: str

    @field_validator("summary")
    @classmethod
    def short_summary(cls, value: str) -> str:
        return value.strip()[:255]


class TaggedItem(TagResult):
    item_number: int


class TagBatch(BaseModel):
    items: list[TaggedItem]


def clean_themes(kind: Kind, themes: list[str]) -> list[str]:
    allowed = THEMES_BY_KIND[kind]
    kept = [
        theme
        for theme in dict.fromkeys(item.strip().lower() for item in themes)
        if theme in allowed
    ]
    return kept or ["other"]


def _clean(kind: Kind, item: TagResult) -> TagResult:
    return TagResult(
        sentiment=item.sentiment, themes=clean_themes(kind, item.themes), summary=item.summary
    )


async def tag_batch(kind: Kind, texts: list[str]) -> list[TagResult | None]:
    """Tags several texts in one model call; returns None for any item the model skipped."""
    system_prompt = render_prompt(
        "tagger.md", kind=LABELS[kind], themes=", ".join(THEMES_BY_KIND[kind])
    )
    numbered = "\n".join(f"[{number}] {text}" for number, text in enumerate(texts, start=1))
    batch = await structured_call("fast", TagBatch, system_prompt, numbered)
    by_number = {item.item_number: item for item in batch.items}
    return [
        _clean(kind, by_number[number]) if number in by_number else None
        for number in range(1, len(texts) + 1)
    ]


async def tag_text(kind: Kind, text: str) -> TagResult:
    result = (await tag_batch(kind, [text]))[0]
    if result is None:
        raise ValueError("model returned no tags")
    return result
