import csv
import io

from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from app.auth import ChatSession
from app.config import MAX_PDF_BYTES
from app.errors import AppError
from app.learning import flashcards, quiz
from app.learning.pdf import store_pdf
from app.schemas import (
    FlashcardSet,
    PdfUploadResponse,
    QuizPublic,
    QuizResult,
    QuizSubmitRequest,
    StoredResult,
)
from app.sessions import Session

router = APIRouter(prefix="/api", tags=["Content"])


def _result(session: Session, result_id: str) -> StoredResult:
    stored = session.results.get(result_id)
    if stored is None:
        raise AppError("not_found", "That result has expired. Ask the question again.", 404)
    return stored


@router.get("/results/{result_id}", response_model=StoredResult, tags=["Results"])
def result_route(result_id: str, session: ChatSession) -> StoredResult:
    """A stored query result with its SQL and explanation."""
    return _result(session, result_id)


@router.get("/results/{result_id}/csv", tags=["Results"], response_class=Response)
def result_csv_route(result_id: str, session: ChatSession) -> Response:
    """Download a stored result as CSV."""
    stored = _result(session, result_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(stored.columns)
    writer.writerows(stored.rows)
    headers = {"Content-Disposition": f'attachment; filename="campusgpt-{result_id}.csv"'}
    return Response(buffer.getvalue(), media_type="text/csv", headers=headers)


@router.get("/quiz/{quiz_id}", response_model=QuizPublic, tags=["Quiz"])
def quiz_route(quiz_id: str, session: ChatSession) -> QuizPublic:
    """Quiz questions without answers (answers come only after submit)."""
    return quiz.public_view(quiz.get_quiz(session, quiz_id))


@router.post("/quiz/{quiz_id}/submit", response_model=QuizResult, tags=["Quiz"])
async def quiz_submit_route(
    quiz_id: str, body: QuizSubmitRequest, session: ChatSession
) -> QuizResult:
    """Submit answers; returns score, per-question result and re-explanations."""
    return await quiz.submit_quiz(session, quiz_id, body.answers)


@router.get("/flashcards/{set_id}", response_model=FlashcardSet, tags=["Quiz"])
def flashcards_route(set_id: str, session: ChatSession) -> FlashcardSet:
    """A generated flashcard set."""
    return flashcards.get_flashcards(session, set_id)


@router.post("/files/pdf", response_model=PdfUploadResponse, tags=["Files"])
async def pdf_route(file: UploadFile, session: ChatSession) -> PdfUploadResponse:
    """Upload a PDF (max 10 MB) for quiz generation."""
    data = await file.read(MAX_PDF_BYTES + 1)
    return store_pdf(session, file.filename or "document.pdf", data)
