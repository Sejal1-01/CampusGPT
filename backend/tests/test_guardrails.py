import pytest

from app.guardrails.classifier import (
    GuardrailVerdict,
    classify,
    contains_blocked_word,
    refusal_text,
)


@pytest.mark.parametrize(
    "message",
    ["you are a bitch", "tum chutiya ho", "MADARCHOD", "ये मादरचोद है", "what a fucking joke"],
)
def test_word_list_blocks_profanity(message: str) -> None:
    assert contains_blocked_word(message)


@pytest.mark.parametrize(
    "message",
    [
        "Explain Dickens' writing style",
        "What is my CGPA?",
        "Mera attendance kitna hai",
        "Scunthorpe",
    ],
)
def test_word_list_allows_clean_text(message: str) -> None:
    assert not contains_blocked_word(message)


async def test_word_list_refuses_without_calling_model(fake_models) -> None:
    verdict = await classify("tum chutiya ho")
    assert verdict.label == "vulgar"
    assert fake_models["fast"].calls == []


async def test_classifier_label_drives_refusal(fake_models) -> None:
    fake_models["fast"].structured = [GuardrailVerdict(label="off_topic", reason="website")]
    verdict = await classify("Build me a website for my startup")
    assert refusal_text(verdict) is not None


async def test_allowed_message_has_no_refusal(fake_models) -> None:
    fake_models["fast"].structured = [GuardrailVerdict(label="allowed", reason="data question")]
    assert refusal_text(await classify("What is my CGPA?")) is None
