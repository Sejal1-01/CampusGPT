import secrets

from pydantic import BaseModel, Field

from app.agent.prompt_files import render_prompt
from app.agent.structured import structured_call
from app.errors import AppError
from app.schemas import Flashcard, FlashcardSet
from app.sessions import Session

DEFAULT_CARDS = 8
MAX_CARDS = 20


class FlashcardDraft(BaseModel):
    cards: list[Flashcard] = Field(min_length=1)


async def create_flashcards(
    session: Session, topic: str, n: int = DEFAULT_CARDS, source_text: str = ""
) -> FlashcardSet:
    count = max(1, min(MAX_CARDS, int(n)))
    user_text = f"Topic: {topic}" + (f"\n\nSource text:\n{source_text}" if source_text else "")
    draft = await structured_call(
        "fast", FlashcardDraft, render_prompt("flashcards.md", n=count), user_text
    )
    flashcard_set = FlashcardSet(
        set_id=f"f_{secrets.token_hex(4)}", topic=topic, cards=draft.cards[:count]
    )
    session.flashcards[flashcard_set.set_id] = flashcard_set
    return flashcard_set


def get_flashcards(session: Session, set_id: str) -> FlashcardSet:
    flashcard_set = session.flashcards.get(set_id)
    if flashcard_set is None:
        raise AppError("not_found", "Those flashcards no longer exist. Ask for new ones.", 404)
    return flashcard_set
