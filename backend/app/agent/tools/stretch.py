from typing import Any

from strands import tool

from app.agent.structured import ModelUnavailableError
from app.errors import AppError
from app.learning import quiz, study_plan
from app.services import accreditation, question_paper, uploads
from app.services.portal_data import to_json
from app.sessions import Session

MODEL_BUSY = {"error": "The AI service is busy. Ask the user to try again in a minute."}
TOOL_HELP = {
    "make_study_plan": "- make_study_plan(hours_per_day): day-by-day plan from the student's exam dates and weakest subjects; show it with StudyPlanCard.",
    "revision_quiz": "- revision_quiz(): a quiz of the questions the student got wrong earlier in this chat; show it with QuizCard.",
    "generate_question_paper": "- generate_question_paper(subject, units, total_marks, mark_split, difficulty): exam paper with CO mapping; show it with QuestionPaperCard.",
    "draft_accreditation_report": "- draft_accreditation_report(): NAAC/NBA-style draft from pass %, results, attendance and feedback; show it with ReportDraftCard.",
    "list_uploaded_data": '- list_uploaded_data(): tables from CSV files the user uploaded in this chat (message starts with "[Attached CSV table=...]").',
    "query_uploaded_data": "- query_uploaded_data(sql, explanation): SELECT over uploaded CSV tables only; returns result_id like query_portal_data.",
}


async def _safely(action: Any) -> str:
    try:
        return await action()
    except ModelUnavailableError:
        return to_json(MODEL_BUSY)
    except AppError as error:
        return to_json({"error": error.message})


def build_stretch_tools(session: Session) -> list[Any]:
    views = set(session.user.views)

    @tool
    async def make_study_plan(hours_per_day: float = 4.0) -> str:
        """Create a day-by-day study plan from the student's exam dates and weakest subjects.

        Args:
            hours_per_day: Study hours available per day.
        """

        async def run() -> str:
            plan = await study_plan.create_study_plan(session, hours_per_day)
            return to_json({"plan_id": plan.plan_id, "days": len(plan.days)})

        return await _safely(run)

    @tool
    def revision_quiz() -> str:
        """Create a quiz from questions the student answered wrongly earlier in this chat."""
        state = quiz.create_revision_quiz(session)
        if state is None:
            return to_json({"error": "No wrong answers to revise yet."})
        return to_json({"quiz_id": state.quiz_id, "questions": len(state.questions)})

    @tool
    async def generate_question_paper(
        subject: str,
        units: str,
        total_marks: int = 100,
        mark_split: str = "",
        difficulty: str = "mixed",
    ) -> str:
        """Generate an exam question paper with course-outcome (CO) mapping.

        Args:
            subject: Subject name.
            units: Syllabus units to cover, e.g. "Unit 1: ER model; Unit 2: SQL".
            total_marks: Total marks of the paper.
            mark_split: Optional split, e.g. "10 x 2 marks, 4 x 10 marks".
            difficulty: easy, medium, hard or mixed.
        """

        async def run() -> str:
            paper = await question_paper.create_question_paper(
                session, subject, units, total_marks, mark_split, difficulty
            )
            return to_json({"paper_id": paper.paper_id, "total_marks": paper.total_marks})

        return await _safely(run)

    @tool
    async def draft_accreditation_report() -> str:
        """Draft NAAC/NBA-style narrative sections from the user's pass %, results, attendance and feedback."""

        async def run() -> str:
            report = await accreditation.create_report(session)
            return to_json({"report_id": report.report_id, "sections": len(report.sections)})

        return await _safely(run)

    @tool
    def list_uploaded_data() -> str:
        """List tables created from CSV files the user uploaded in this chat."""
        return uploads.describe_uploads(session)

    @tool
    def query_uploaded_data(sql: str, explanation: str = "") -> str:
        """Run one SELECT over the user's uploaded CSV tables (not portal data).

        Args:
            sql: A single SELECT using only uploaded table names.
            explanation: One plain-English line describing what the query computes.
        """
        return to_json(uploads.query_uploads(session, sql, explanation))

    selected: list[Any] = [revision_quiz, list_uploaded_data, query_uploaded_data]
    if set(study_plan.NEEDED_VIEWS) <= views:
        selected.append(make_study_plan)
    if session.user.roles and set(session.user.roles) != {"student"}:
        selected.append(generate_question_paper)
    if accreditation.pick_scope(views) is not None:
        selected.append(draft_accreditation_report)
    return selected


def stretch_tool_help(tools: list[Any]) -> str:
    names = {getattr(item, "tool_name", getattr(item, "__name__", "")) for item in tools}
    return "\n".join(text for name, text in TOOL_HELP.items() if name in names)
