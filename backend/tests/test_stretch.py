from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.errors import AppError
from app.learning import quiz
from app.learning.quiz import QuizDraft, QuizQuestion, ReexplanationDraft
from app.learning.study_plan import StudyPlanDraft, create_study_plan, keep_window, plan_window
from app.main import app
from app.schemas import PaperQuestion, PaperSection, ReportSection, StudyPlanDay
from app.services import accreditation, question_paper, uploads
from app.services.chat import with_revision_note
from tests.integration_helpers import login_session


def question(concept: str, correct: int = 0) -> QuizQuestion:
    return QuizQuestion(
        question=f"About {concept}?",
        options=["A", "B", "C", "D"],
        correct_option=correct,
        explanation="Because.",
        concept=concept,
    )


def section(marks: list[int]) -> PaperSection:
    questions = [
        PaperQuestion(
            number=str(index + 1),
            text="Explain.",
            marks=value,
            course_outcome="CO1",
            difficulty="medium",
        )
        for index, value in enumerate(marks)
    ]
    return PaperSection(title="Section A", instructions="Answer all.", questions=questions)


def test_plan_window_stops_before_last_exam_and_caps_length() -> None:
    today = date(2026, 11, 11)
    assert plan_window(today, ["2026-11-24", "2026-12-01"]) == (today, date(2026, 11, 30))
    assert plan_window(today, ["2027-03-01"])[1] == date(2026, 12, 1)
    assert plan_window(today, []) == (today, today)


def test_plan_days_outside_window_or_invalid_are_dropped() -> None:
    days = [
        StudyPlanDay(date="2026-11-12", subject="OS", hours=4, tasks=["x"]),
        StudyPlanDay(date="2026-12-25", subject="OS", hours=4, tasks=["x"]),
        StudyPlanDay(date="tomorrow", subject="OS", hours=4, tasks=["x"]),
    ]
    kept = keep_window(days, date(2026, 11, 11), date(2026, 11, 30))
    assert [day.date for day in kept] == ["2026-11-12"]


async def test_study_plan_uses_only_own_data(fake_models) -> None:
    session = login_session("student1")
    fake_models["fast"].structured = [
        StudyPlanDraft(
            title="Plan",
            days=[StudyPlanDay(date="2026-11-12", subject="DBMS", hours=4, tasks=["a"])],
            notes="n",
        )
    ]
    plan = await create_study_plan(session)
    prompt = fake_models["fast"].calls[0]["prompt"][0]["content"][0]["text"]
    assert "Database Management Systems" in prompt
    assert plan.plan_id in session.study_plans


async def test_study_plan_refused_for_faculty(fake_models) -> None:
    with pytest.raises(AppError):
        await create_study_plan(login_session("faculty1"))


async def test_wrong_answers_come_back_after_two_turns(session, fake_models) -> None:
    fake_models["fast"].structured = [
        QuizDraft(questions=[question("paging", 1), question("mutex", 2)]),
        ReexplanationDraft(items=[]),
    ]
    state = await quiz.create_quiz(session, "OS", 2, "easy")
    await quiz.submit_quiz(session, state.quiz_id, [1, 0])
    assert with_revision_note(session, "hi") == "hi"
    assert "revision_quiz()" in with_revision_note(session, "next")
    revision = quiz.create_revision_quiz(session)
    assert revision is not None and len(revision.questions) == 1
    assert revision.questions[0].options[revision.questions[0].correct_option] == "C"
    assert quiz.create_revision_quiz(session) is None


async def test_question_paper_retries_until_marks_add_up(fake_models) -> None:
    session = login_session("faculty1")
    fake_models["fast"].structured = [
        question_paper.QuestionPaperDraft(sections=[section([10, 10])]),
        question_paper.QuestionPaperDraft(sections=[section([20, 30])]),
    ]
    paper = await question_paper.create_question_paper(session, "DBMS", "Unit 1", 50, "", "mixed")
    assert paper.total_marks == 50
    assert len(fake_models["fast"].calls) == 2


async def test_question_paper_refused_for_students(fake_models) -> None:
    with pytest.raises(AppError):
        await question_paper.create_question_paper(
            login_session("student1"), "DBMS", "U1", 50, "", "easy"
        )


async def test_accreditation_report_is_scoped(fake_models) -> None:
    fake_models["fast"].structured = [
        accreditation.AccreditationDraft(sections=[ReportSection(heading="h", body="b")])
    ]
    session = login_session("hod_cse")
    report = await accreditation.create_report(session)
    assert report.scope == "CSE" and len(report.result_ids) == 4
    sent = fake_models["fast"].calls[0]["prompt"][0]["content"][0]["text"]
    assert '"ECE"' not in sent and '"ME"' not in sent


async def test_accreditation_refused_for_students(fake_models) -> None:
    with pytest.raises(AppError):
        await accreditation.create_report(login_session("student1"))


CSV = b"Name,Marks,City\nAsha,81,Patna\nRavi,67.5,Gaya\nMeena,,Patna\n"


def test_csv_upload_and_query() -> None:
    session = login_session("student1")
    response = uploads.store_csv(session, "My Marks.csv", CSV)
    assert response.table_name == "upload_my_marks" and response.rows == 3
    result = uploads.query_uploads(
        session,
        f"SELECT city, AVG(marks) AS avg_marks FROM {response.table_name} GROUP BY city",
        "x",
    )
    assert sorted(result["rows"]) == [["Gaya", 67.5], ["Patna", 81.0]]


def test_csv_queries_cannot_reach_portal_data() -> None:
    session = login_session("student1")
    uploads.store_csv(session, "data.csv", CSV)
    assert "error" in uploads.query_uploads(session, "SELECT * FROM my_marks", "x")
    assert "error" in uploads.query_uploads(session, "SELECT * FROM sqlite_master", "x")
    assert "error" in uploads.query_uploads(session, "DROP TABLE upload_data", "x")


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"only,header\n", "csv_empty"),
        (b"\xff\xfe\x00bad", "csv_encoding"),
        (b"a\n" + b"1\n" * 20_001, "csv_too_big"),
    ],
)
def test_csv_rejections(data: bytes, code: str) -> None:
    with pytest.raises(AppError) as error:
        uploads.parse_csv(data)
    assert error.value.code == code


def test_csv_column_names_are_cleaned_and_unique() -> None:
    session = login_session("student1")
    response = uploads.store_csv(session, "x.csv", b"Roll No,roll no,2024 Marks,\n1,2,3,4\n")
    assert response.columns == ["roll_no", "roll_no_2", "c_2024_marks", "column_4"]


def test_dashboard_rerun_applies_current_users_scope() -> None:
    with TestClient(app) as client:
        client.post("/api/auth/login", json={"username": "student1", "password": "demo123"})
        ok = client.post(
            "/api/results/rerun", json={"sql": "SELECT DISTINCT student_id FROM my_marks"}
        )
        assert ok.status_code == 200 and len(ok.json()["rows"]) == 1
        denied = client.post("/api/results/rerun", json={"sql": "SELECT roll_no FROM students"})
        assert denied.status_code == 400
        assert denied.json()["error"]["code"] == "query_rejected"
