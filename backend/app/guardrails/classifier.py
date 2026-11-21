import asyncio
import logging
import re
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.agent.prompt_files import load_prompt
from app.agent.structured import ModelUnavailableError, structured_call
from app.config import GUARDRAIL_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)
WORDLIST_PATH = Path(__file__).with_name("wordlist.txt")
Label = Literal["allowed", "harmful", "vulgar", "off_topic"]

REFUSALS: dict[str, str] = {
    "vulgar": "I can't help with that. Please keep it respectful. I can help with your portal "
    "data, concepts and quizzes.",
    "harmful": "I can't help with that. I can help with your college data, explain concepts or "
    "make a quiz.",
    "off_topic": "That's outside what I do. I can answer questions about your college data, "
    "explain concepts, make quizzes and flashcards, or search the web for academic and "
    "general questions.",
}


class GuardrailVerdict(BaseModel):
    label: Label
    reason: str


@cache
def _blocked_terms() -> tuple[str, ...]:
    lines = WORDLIST_PATH.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip().lower() for line in lines if line.strip())


def contains_blocked_word(message: str) -> bool:
    text = message.lower()
    for term in _blocked_terms():
        if term.isascii():
            if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", text):
                return True
        elif term in text:
            return True
    return False


async def classify(message: str) -> GuardrailVerdict:
    if contains_blocked_word(message):
        return GuardrailVerdict(label="vulgar", reason="matched word list")
    try:
        return await asyncio.wait_for(
            structured_call("fast", GuardrailVerdict, load_prompt("guardrail.md"), message),
            GUARDRAIL_TIMEOUT_SECONDS,
        )
    except (ModelUnavailableError, TimeoutError):
        logger.warning("guardrail classifier unavailable; the system prompt still enforces scope")
        return GuardrailVerdict(label="allowed", reason="classifier unavailable")


def refusal_text(verdict: GuardrailVerdict) -> str | None:
    return REFUSALS.get(verdict.label)
