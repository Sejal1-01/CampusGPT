import pytest

from app.errors import AppError
from app.learning import quiz
from app.learning.quiz import QuizDraft, QuizQuestion, ReexplanationDraft
from app.schemas import Reexplanation


def make_question(concept: str, correct: int = 0) -> QuizQuestion:
    return QuizQuestion(
        question=f"Question about {concept}?",
        options=["A", "B", "C", "D"],
        correct_option=correct,
        explanation=f"Because of {concept}.",
        concept=concept,
    )


async def test_create_quiz_hides_answers(session, fake_models) -> None:
    fake_models["fast"].structured = [QuizDraft(questions=[make_question("deadlock", 2)])]
    state = await quiz.create_quiz(session, "Deadlock", 1, "medium")
    public = quiz.public_view(state).model_dump()
    assert "correct_option" not in str(public["questions"])
    assert "explanation" not in str(public["questions"])
    assert public["submitted"] is False


async def test_grading_scores_and_reexplains_wrong(session, fake_models) -> None:
    fake_models["fast"].structured = [
        QuizDraft(questions=[make_question("mutex", 1), make_question("paging", 3)]),
        ReexplanationDraft(
            items=[Reexplanation(concept="paging", explanation="Paging splits memory.")]
        ),
    ]
    state = await quiz.create_quiz(session, "OS", 2, "easy")
    result = await quiz.submit_quiz(session, state.quiz_id, [1, 0])
    assert (result.score, result.total) == (1, 2)
    assert [item.is_correct for item in result.results] == [True, False]
    assert result.reexplanations[0].concept == "paging"


async def test_unanswered_counts_as_wrong(session, fake_models) -> None:
    fake_models["fast"].structured = [QuizDraft(questions=[make_question("a"), make_question("b")])]
    state = await quiz.create_quiz(session, "Topic", 2, "easy")
    fake_models["fast"].structured = [ReexplanationDraft(items=[])]
    result = await quiz.submit_quiz(session, state.quiz_id, [0])
    assert result.score == 1
    assert result.results[1].chosen is None
    assert result.reexplanations[0].concept == "b"


async def test_submit_twice_is_idempotent(session, fake_models) -> None:
    fake_models["fast"].structured = [QuizDraft(questions=[make_question("a")])]
    state = await quiz.create_quiz(session, "Topic", 1, "easy")
    first = await quiz.submit_quiz(session, state.quiz_id, [0])
    second = await quiz.submit_quiz(session, state.quiz_id, [3])
    assert first == second


async def test_unknown_quiz_is_404(session) -> None:
    with pytest.raises(AppError) as error:
        await quiz.submit_quiz(session, "q_missing", [0])
    assert error.value.status_code == 404


async def test_reexplanation_falls_back_when_model_fails(session, fake_models, monkeypatch) -> None:
    fake_models["fast"].structured = [QuizDraft(questions=[make_question("stack", 0)])]
    state = await quiz.create_quiz(session, "DS", 1, "easy")
    monkeypatch.setattr("app.agent.structured.MODEL_MAX_RETRIES", 1)
    result = await quiz.submit_quiz(session, state.quiz_id, [2])
    assert result.reexplanations[0].explanation == "Because of stack."


def test_out_of_range_answer_is_treated_as_unanswered(session) -> None:
    state = quiz.QuizState("q_x", "t", "easy", [make_question("a")])
    assert quiz.score_answers(state, [7])[0].chosen is None


def test_question_count_is_clamped() -> None:
    assert quiz.clamp_question_count(0) == 1
    assert quiz.clamp_question_count(100) == 15
