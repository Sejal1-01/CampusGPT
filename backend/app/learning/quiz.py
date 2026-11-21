import logging
import secrets
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

from app.agent.prompt_files import load_prompt, render_prompt
from app.agent.structured import ModelUnavailableError, structured_call
from app.config import REVISION_DELAY_TURNS
from app.errors import AppError
from app.schemas import (
    QuizPublic,
    QuizQuestionPublic,
    QuizQuestionResult,
    QuizResult,
    Reexplanation,
)
from app.sessions import Session

logger = logging.getLogger(__name__)
MIN_QUESTIONS = 1
MAX_QUESTIONS = 15
OPTIONS_PER_QUESTION = 4
DIFFICULTIES = ("easy", "medium", "hard")


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=OPTIONS_PER_QUESTION, max_length=OPTIONS_PER_QUESTION)
    correct_option: int = Field(ge=0, le=OPTIONS_PER_QUESTION - 1)
    explanation: str
    concept: str


class QuizDraft(BaseModel):
    questions: list[QuizQuestion]

    @field_validator("questions")
    @classmethod
    def not_empty(cls, value: list[QuizQuestion]) -> list[QuizQuestion]:
        if not value:
            raise ValueError("quiz has no questions")
        return value


class ReexplanationDraft(BaseModel):
    items: list[Reexplanation]


@dataclass
class QuizState:
    quiz_id: str
    topic: str
    difficulty: str
    questions: list[QuizQuestion]
    result: QuizResult | None = field(default=None)


def clamp_question_count(n: int) -> int:
    return max(MIN_QUESTIONS, min(MAX_QUESTIONS, int(n)))


async def create_quiz(
    session: Session, topic: str, n: int, difficulty: str, source_text: str = ""
) -> QuizState:
    count = clamp_question_count(n)
    level = difficulty if difficulty in DIFFICULTIES else "medium"
    system_prompt = render_prompt("quiz.md", n=count, difficulty=level)
    user_text = f"Topic: {topic}"
    if source_text:
        user_text += f"\n\nSource text:\n{source_text}"
    draft = await structured_call("fast", QuizDraft, system_prompt, user_text)
    state = QuizState(f"q_{secrets.token_hex(4)}", topic, level, draft.questions[:count])
    session.quizzes[state.quiz_id] = state
    return state


def get_quiz(session: Session, quiz_id: str) -> QuizState:
    state = session.quizzes.get(quiz_id)
    if state is None:
        raise AppError("not_found", "That quiz no longer exists. Ask for a new one.", 404)
    return state


def public_view(state: QuizState) -> QuizPublic:
    questions = [
        QuizQuestionPublic(index=index, question=item.question, options=item.options)
        for index, item in enumerate(state.questions)
    ]
    return QuizPublic(
        quiz_id=state.quiz_id,
        topic=state.topic,
        difficulty=state.difficulty,
        questions=questions,
        submitted=state.result is not None,
        result=state.result,
    )


def score_answers(state: QuizState, answers: list[int | None]) -> list[QuizQuestionResult]:
    padded = list(answers) + [None] * (len(state.questions) - len(answers))
    results = []
    for index, question in enumerate(state.questions):
        chosen = padded[index]
        valid = chosen if isinstance(chosen, int) and 0 <= chosen < OPTIONS_PER_QUESTION else None
        results.append(
            QuizQuestionResult(
                index=index,
                chosen=valid,
                correct_option=question.correct_option,
                is_correct=valid == question.correct_option,
                explanation=question.explanation,
            )
        )
    return results


async def submit_quiz(session: Session, quiz_id: str, answers: list[int | None]) -> QuizResult:
    state = get_quiz(session, quiz_id)
    if state.result is not None:
        return state.result
    results = score_answers(state, answers)
    wrong = [state.questions[item.index] for item in results if not item.is_correct]
    queue_for_revision(session, wrong)
    state.result = QuizResult(
        quiz_id=quiz_id,
        score=sum(item.is_correct for item in results),
        total=len(results),
        results=results,
        reexplanations=await reexplain(wrong, results),
    )
    return state.result


async def reexplain(
    wrong: list[QuizQuestion], results: list[QuizQuestionResult]
) -> list[Reexplanation]:
    if not wrong:
        return []
    concepts = list(dict.fromkeys(question.concept for question in wrong))
    details = "\n".join(
        f"- Concept: {question.concept}. Question: {question.question}. "
        f"Correct: {question.options[question.correct_option]}."
        for question in wrong
    )
    try:
        draft = await structured_call(
            "fast", ReexplanationDraft, load_prompt("quiz_reexplain.md"), details
        )
        return draft.items[: len(concepts)] or _fallback(wrong)
    except ModelUnavailableError:
        logger.warning("re-explanation failed; using stored explanations")
        return _fallback(wrong)


def _fallback(wrong: list[QuizQuestion]) -> list[Reexplanation]:
    seen: dict[str, str] = {}
    for question in wrong:
        seen.setdefault(question.concept, question.explanation)
    return [Reexplanation(concept=concept, explanation=text) for concept, text in seen.items()]


def queue_for_revision(session: Session, wrong: list[QuizQuestion]) -> None:
    known = {question.question for question in session.revision_questions}
    session.revision_questions.extend(item for item in wrong if item.question not in known)
    if session.revision_questions and session.revision_due_turn is None:
        session.revision_due_turn = session.turns + REVISION_DELAY_TURNS


def revision_due(session: Session) -> bool:
    due = session.revision_due_turn
    return bool(session.revision_questions) and due is not None and session.turns >= due


def create_revision_quiz(session: Session) -> QuizState | None:
    if not session.revision_questions:
        return None
    questions = [_shuffled(question) for question in session.revision_questions]
    session.revision_questions = []
    session.revision_due_turn = None
    state = QuizState(
        f"q_{secrets.token_hex(4)}", "Revision of earlier mistakes", "medium", questions
    )
    session.quizzes[state.quiz_id] = state
    return state


def _shuffled(question: QuizQuestion) -> QuizQuestion:
    order = list(range(OPTIONS_PER_QUESTION))
    secrets.SystemRandom().shuffle(order)
    return question.model_copy(
        update={
            "options": [question.options[index] for index in order],
            "correct_option": order.index(question.correct_option),
        }
    )
