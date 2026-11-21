from typing import Any, Literal

from pydantic import BaseModel, Field

from app.config import MAX_MESSAGE_CHARS


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class OkResponse(BaseModel):
    ok: bool = True


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class StarterQuestion(BaseModel):
    text: str


class Me(BaseModel):
    username: str
    display_name: str
    roles: list[str]
    department: str | None
    is_platform_admin: bool
    allowed_areas: list[str]
    starter_questions: list[str]


class DemoAccount(BaseModel):
    username: str
    role: str
    note: str


class ChatRequest(BaseModel):
    message: str = Field(max_length=MAX_MESSAGE_CHARS * 2)


class ChatEvent(BaseModel):
    """One Server-Sent Event payload on /api/chat."""

    type: Literal["status", "tool", "text", "reset", "refusal", "error", "done"]
    text: str | None = None
    delta: str | None = None
    name: str | None = None
    status: Literal["start", "end"] | None = None
    code: str | None = None
    message: str | None = None
    latency_ms: int | None = None


class StoredResult(BaseModel):
    result_id: str
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int
    truncated: bool
    sql: str
    explanation: str


class QuizQuestionPublic(BaseModel):
    index: int
    question: str
    options: list[str]


class QuizQuestionResult(BaseModel):
    index: int
    chosen: int | None
    correct_option: int
    is_correct: bool
    explanation: str


class Reexplanation(BaseModel):
    concept: str
    explanation: str


class QuizSubmitRequest(BaseModel):
    answers: list[int | None]


class QuizResult(BaseModel):
    quiz_id: str
    score: int
    total: int
    results: list[QuizQuestionResult]
    reexplanations: list[Reexplanation]


class QuizPublic(BaseModel):
    quiz_id: str
    topic: str
    difficulty: str
    questions: list[QuizQuestionPublic]
    submitted: bool
    result: QuizResult | None = None


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardSet(BaseModel):
    set_id: str
    topic: str
    cards: list[Flashcard]


class PdfUploadResponse(BaseModel):
    file_id: str
    filename: str
    pages: int
    characters: int


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: bool


class GrantRow(BaseModel):
    domain: str
    scope: str


class RoleSummary(BaseModel):
    name: str
    description: str
    grants: list[GrantRow]
    members: list[str]


class GroupSummary(BaseModel):
    name: str
    description: str
    grants: list[GrantRow]
    members: list[str]


class UserSummary(BaseModel):
    username: str
    display_name: str
    is_platform_admin: bool


class AccessOverview(BaseModel):
    roles: list[RoleSummary]
    groups: list[GroupSummary]
    users: list[UserSummary]
    domains: list[str]
    scopes: list[str]


class GrantSourceRow(BaseModel):
    domain: str
    scope: str
    source: Literal["role", "group", "user"]
    name: str


class EffectiveAccessResponse(BaseModel):
    username: str
    roles: list[str]
    grants: list[GrantSourceRow]
    views: list[str]


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=255)


class MemberRequest(BaseModel):
    username: str


class GrantRequest(BaseModel):
    kind: Literal["role", "group", "user"]
    target: str
    domain: str
    scope: str


class RoleAssignRequest(BaseModel):
    role: str


class PasswordRequest(BaseModel):
    password: str = Field(min_length=6, max_length=200)


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=200)
    student_id: int | None = None
    faculty_id: int | None = None
    dept_id: int | None = None


class AuditEntry(BaseModel):
    id: int
    changed_by: str | None
    action: str
    target: str
    details: str
    changed_at: str


class StudyPlanDay(BaseModel):
    date: str
    subject: str
    hours: float
    tasks: list[str]


class StudyPlan(BaseModel):
    plan_id: str
    title: str
    days: list[StudyPlanDay]
    notes: str


class PaperQuestion(BaseModel):
    number: str
    text: str
    marks: int
    course_outcome: str
    difficulty: Literal["easy", "medium", "hard"]


class PaperSection(BaseModel):
    title: str
    instructions: str
    questions: list[PaperQuestion]


class QuestionPaper(BaseModel):
    paper_id: str
    subject: str
    total_marks: int
    duration_minutes: int
    sections: list[PaperSection]


class ReportSection(BaseModel):
    heading: str
    body: str


class AccreditationReport(BaseModel):
    report_id: str
    scope: str
    result_ids: list[str]
    sections: list[ReportSection]


class RerunRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=8000)
    explanation: str = Field(default="", max_length=500)


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    table_name: str
    columns: list[str]
    rows: int
