from typing import Any

from strands import tool

from app.agent.structured import ModelUnavailableError
from app.agent.tools.stretch import build_stretch_tools
from app.learning import flashcards, quiz
from app.learning.pdf import pdf_text
from app.services import at_risk, portal_data, search
from app.services.drafting import draft_message_text
from app.sessions import Session

MODEL_BUSY = {"error": "The AI service is busy. Ask the user to try again in a minute."}


def build_tools(session: Session) -> list[Any]:
    """Tools bound to one server-side session; identity never comes from model arguments."""

    @tool
    def list_views() -> str:
        """List the data views this user may query, with one-line descriptions."""
        return portal_data.list_views_text(session.user.views)

    @tool
    def describe_view(name: str) -> str:
        """Describe one view: columns, allowed values, join keys and example SQL.

        Args:
            name: The view name, e.g. my_attendance.
        """
        return portal_data.describe_view(session, name)

    @tool
    def query_portal_data(sql: str, explanation: str = "") -> str:
        """Run one read-only MySQL SELECT over the user's views.

        Args:
            sql: A single SELECT statement using only the user's views.
            explanation: One plain-English line describing what the query computes.
        """
        return portal_data.to_json(portal_data.run_portal_query(session, sql, explanation))

    @tool
    async def web_search(query: str) -> str:
        """Search the web for current events or general and academic facts.

        Args:
            query: The search query.
        """
        return portal_data.to_json(await search.web_search(query))

    @tool
    async def generate_quiz(topic: str, n: int = 5, difficulty: str = "medium") -> str:
        """Create an interactive multiple-choice quiz and return its quiz_id.

        Args:
            topic: The topic to quiz on.
            n: Number of questions (1-15).
            difficulty: easy, medium or hard.
        """
        try:
            state = await quiz.create_quiz(session, topic, n, difficulty)
        except ModelUnavailableError:
            return portal_data.to_json(MODEL_BUSY)
        return portal_data.to_json({"quiz_id": state.quiz_id, "questions": len(state.questions)})

    @tool
    async def quiz_from_pdf(file_id: str, n: int = 5) -> str:
        """Create a quiz from a PDF the user uploaded, and return its quiz_id.

        Args:
            file_id: The id from the "[Attached PDF file_id=...]" note in the message.
            n: Number of questions (1-15).
        """
        text = pdf_text(session, file_id)
        if text is None:
            return portal_data.to_json({"error": "No uploaded PDF with that file_id."})
        try:
            state = await quiz.create_quiz(session, "the uploaded document", n, "medium", text)
        except ModelUnavailableError:
            return portal_data.to_json(MODEL_BUSY)
        return portal_data.to_json({"quiz_id": state.quiz_id, "questions": len(state.questions)})

    @tool
    async def grade_quiz(quiz_id: str, answers: list[int]) -> str:
        """Grade answers typed in chat for a quiz (0-based option indexes, -1 if skipped).

        Args:
            quiz_id: The quiz id.
            answers: Chosen option index per question.
        """
        choices = [answer if answer >= 0 else None for answer in answers]
        result = await quiz.submit_quiz(session, quiz_id, choices)
        return result.model_dump_json()

    @tool
    async def generate_flashcards(topic: str, n: int = 8) -> str:
        """Create a set of study flashcards and return its set_id.

        Args:
            topic: The topic.
            n: Number of cards (1-20).
        """
        try:
            created = await flashcards.create_flashcards(session, topic, n)
        except ModelUnavailableError:
            return portal_data.to_json(MODEL_BUSY)
        return portal_data.to_json({"set_id": created.set_id, "cards": len(created.cards)})

    @tool
    def find_at_risk_students() -> str:
        """List at-risk students in the user's scope with the rules each one breaks."""
        return portal_data.to_json(at_risk.find_at_risk(session))

    @tool
    async def draft_message(student_ref: str, reason: str) -> str:
        """Draft (never send) a supportive message from the teacher/advisor to a student.

        Args:
            student_ref: Student name and roll number.
            reason: Why the student is at risk, in one line.
        """
        try:
            draft = await draft_message_text(session.user.display_name, student_ref, reason)
        except ModelUnavailableError:
            return portal_data.to_json(MODEL_BUSY)
        return draft.model_dump_json()

    return [
        list_views,
        describe_view,
        query_portal_data,
        web_search,
        generate_quiz,
        quiz_from_pdf,
        grade_quiz,
        generate_flashcards,
        find_at_risk_students,
        draft_message,
        *build_stretch_tools(session),
    ]
