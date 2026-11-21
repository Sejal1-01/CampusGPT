from fastapi import APIRouter, UploadFile

from app.auth import ChatSession
from app.config import MAX_CSV_BYTES
from app.learning.study_plan import get_study_plan
from app.schemas import (
    AccreditationReport,
    DatasetUploadResponse,
    QuestionPaper,
    RerunRequest,
    StoredResult,
    StudyPlan,
)
from app.services.accreditation import get_report
from app.services.portal_data import rerun_saved_query
from app.services.question_paper import get_question_paper
from app.services.uploads import store_csv

router = APIRouter(prefix="/api", tags=["Content"])


@router.get("/study-plans/{plan_id}", response_model=StudyPlan, tags=["Quiz"])
def study_plan_route(plan_id: str, session: ChatSession) -> StudyPlan:
    """A generated exam study plan."""
    return get_study_plan(session, plan_id)


@router.get("/question-papers/{paper_id}", response_model=QuestionPaper, tags=["Quiz"])
def question_paper_route(paper_id: str, session: ChatSession) -> QuestionPaper:
    """A generated question paper with CO mapping."""
    return get_question_paper(session, paper_id)


@router.get("/reports/{report_id}", response_model=AccreditationReport, tags=["Results"])
def report_route(report_id: str, session: ChatSession) -> AccreditationReport:
    """An accreditation report draft with the result ids of its metric tables."""
    return get_report(session, report_id)


@router.post("/results/rerun", response_model=StoredResult, tags=["Results"])
def rerun_route(body: RerunRequest, session: ChatSession) -> StoredResult:
    """Re-run a pinned dashboard query for the current user (same guard and scope)."""
    return rerun_saved_query(session, body.sql, body.explanation)


@router.post("/files/csv", response_model=DatasetUploadResponse, tags=["Files"])
async def csv_route(file: UploadFile, session: ChatSession) -> DatasetUploadResponse:
    """Upload a CSV (max 5 MB) as a private table for this chat."""
    data = await file.read(MAX_CSV_BYTES + 1)
    return store_csv(session, file.filename or "data.csv", data)
