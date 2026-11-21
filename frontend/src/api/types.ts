import type { components } from "./schema";

type Schemas = components["schemas"];

export type OkResponse = Schemas["OkResponse"];
export type LoginRequest = Schemas["LoginRequest"];
export type Me = Schemas["Me"];
export type DemoAccount = Schemas["DemoAccount"];
export type ChatEvent = Schemas["ChatEvent"];
export type StoredResult = Schemas["StoredResult"];
export type QuizPublic = Schemas["QuizPublic"];
export type QuizQuestion = Schemas["QuizQuestionPublic"];
export type QuizResult = Schemas["QuizResult"];
export type QuizSubmitRequest = Schemas["QuizSubmitRequest"];
export type Flashcard = Schemas["Flashcard"];
export type FlashcardSet = Schemas["FlashcardSet"];
export type PdfUpload = Schemas["PdfUploadResponse"];
export type HealthResponse = Schemas["HealthResponse"];
export type AccessOverview = Schemas["AccessOverview"];
export type RoleSummary = Schemas["RoleSummary"];
export type GroupSummary = Schemas["GroupSummary"];
export type UserSummary = Schemas["UserSummary"];
export type GrantRow = Schemas["GrantRow"];
export type GrantRequest = Schemas["GrantRequest"];
export type GrantKind = GrantRequest["kind"];
export type EffectiveAccess = Schemas["EffectiveAccessResponse"];
export type UserCreateRequest = Schemas["UserCreateRequest"];
export type GroupCreateRequest = Schemas["GroupCreateRequest"];
export type AuditEntry = Schemas["AuditEntry"];
export type StudyPlan = Schemas["StudyPlan"];
export type StudyPlanDay = Schemas["StudyPlanDay"];
export type QuestionPaper = Schemas["QuestionPaper"];
export type PaperSection = Schemas["PaperSection"];
export type PaperQuestion = Schemas["PaperQuestion"];
export type AccreditationReport = Schemas["AccreditationReport"];
export type ReportSection = Schemas["ReportSection"];
export type RerunRequest = Schemas["RerunRequest"];
export type CsvUpload = Schemas["DatasetUploadResponse"];

// The backend's error shape is not declared in its OpenAPI schema, so it is typed here.
export interface ApiErrorBody {
  error: { code: string; message: string };
}
