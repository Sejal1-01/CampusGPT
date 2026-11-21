import secrets

from pydantic import BaseModel

from app.agent.prompt_files import render_prompt
from app.agent.structured import structured_call
from app.config import MAX_PAPER_MARKS
from app.errors import AppError
from app.schemas import PaperSection, QuestionPaper
from app.sessions import Session

DIFFICULTIES = ("easy", "medium", "hard", "mixed")
MINUTES_PER_MARK = 1.8


class QuestionPaperDraft(BaseModel):
    sections: list[PaperSection]


def paper_total(sections: list[PaperSection]) -> int:
    return sum(question.marks for section in sections for question in section.questions)


def _request_text(
    subject: str, units: str, total_marks: int, mark_split: str, difficulty: str
) -> str:
    return (
        f"Subject: {subject}\nSyllabus units: {units}\nTotal marks: {total_marks}\n"
        f"Mark split: {mark_split or 'choose a sensible split'}\nDifficulty: {difficulty}"
    )


async def create_question_paper(
    session: Session, subject: str, units: str, total_marks: int, mark_split: str, difficulty: str
) -> QuestionPaper:
    if "student" in session.user.roles and len(session.user.roles) == 1:
        raise AppError("forbidden", "Question papers are for faculty.", 403)
    marks = max(10, min(MAX_PAPER_MARKS, int(total_marks)))
    level = difficulty if difficulty in DIFFICULTIES else "mixed"
    prompt = render_prompt("question_paper.md", total_marks=marks)
    request = _request_text(subject, units, marks, mark_split, level)
    draft = await structured_call("fast", QuestionPaperDraft, prompt, request)
    if paper_total(draft.sections) != marks:
        retry = f"{request}\n\nYour last draft totalled {paper_total(draft.sections)} marks. It must total exactly {marks}."
        draft = await structured_call("fast", QuestionPaperDraft, prompt, retry)
    paper = QuestionPaper(
        paper_id=f"p_{secrets.token_hex(4)}",
        subject=subject,
        total_marks=paper_total(draft.sections),
        duration_minutes=int(round(marks * MINUTES_PER_MARK / 30) * 30) or 60,
        sections=draft.sections,
    )
    session.question_papers[paper.paper_id] = paper
    return paper


def get_question_paper(session: Session, paper_id: str) -> QuestionPaper:
    paper = session.question_papers.get(paper_id)
    if paper is None:
        raise AppError("not_found", "That question paper no longer exists. Ask for a new one.", 404)
    return paper
