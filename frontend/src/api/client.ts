import type {
  AccessOverview,
  AccreditationReport,
  ApiErrorBody,
  AuditEntry,
  CsvUpload,
  DemoAccount,
  EffectiveAccess,
  FlashcardSet,
  GrantRequest,
  GroupCreateRequest,
  HealthResponse,
  LoginRequest,
  Me,
  OkResponse,
  PdfUpload,
  QuestionPaper,
  QuizPublic,
  QuizResult,
  RerunRequest,
  StoredResult,
  StudyPlan,
  UserCreateRequest,
} from "./types";

export const NETWORK_ERROR_CODE = "network_error";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value)) return false;
  const detail = value.error;
  return (
    typeof detail === "object" &&
    detail !== null &&
    "code" in detail &&
    "message" in detail &&
    typeof detail.code === "string" &&
    typeof detail.message === "string"
  );
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  if (isErrorBody(body)) {
    return new ApiError(body.error.code, body.error.message, response.status);
  }
  return new ApiError(
    "http_error",
    `Request failed (${response.status}). Try again.`,
    response.status,
  );
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  json?: unknown;
  formData?: FormData;
  signal?: AbortSignal;
}

export async function send(path: string, options: RequestOptions = {}): Promise<Response> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  } else if (options.formData) {
    body = options.formData;
  }

  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method ?? "GET",
      credentials: "same-origin",
      headers,
      body,
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(NETWORK_ERROR_CODE, "Can't reach the server. Check it is running.", 0);
  }

  if (response.ok) return response;
  if (response.status === 401) unauthorizedHandler?.();
  throw await toApiError(response);
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options);
  return (await response.json()) as T;
}

const segment = encodeURIComponent;

export const api = {
  demoAccounts: () => request<DemoAccount[]>("/api/auth/demo-accounts"),
  login: (credentials: LoginRequest) =>
    request<Me>("/api/auth/login", { method: "POST", json: credentials }),
  logout: () => request<OkResponse>("/api/auth/logout", { method: "POST" }),
  me: () => request<Me>("/api/auth/me"),
  health: () => request<HealthResponse>("/api/health"),
  resetChat: () => request<OkResponse>("/api/chat/reset", { method: "POST" }),
  openChatStream: (message: string, signal: AbortSignal) =>
    send("/api/chat", { method: "POST", json: { message }, signal }),
  result: (resultId: string) => request<StoredResult>(`/api/results/${segment(resultId)}`),
  resultCsvUrl: (resultId: string) => `/api/results/${segment(resultId)}/csv`,
  rerunResult: (query: RerunRequest) =>
    request<StoredResult>("/api/results/rerun", { method: "POST", json: query }),
  quiz: (quizId: string) => request<QuizPublic>(`/api/quiz/${segment(quizId)}`),
  submitQuiz: (quizId: string, answers: (number | null)[]) =>
    request<QuizResult>(`/api/quiz/${segment(quizId)}/submit`, {
      method: "POST",
      json: { answers },
    }),
  flashcards: (setId: string) => request<FlashcardSet>(`/api/flashcards/${segment(setId)}`),
  uploadPdf: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<PdfUpload>("/api/files/pdf", { method: "POST", formData });
  },
  uploadCsv: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<CsvUpload>("/api/files/csv", { method: "POST", formData });
  },
  studyPlan: (planId: string) => request<StudyPlan>(`/api/study-plans/${segment(planId)}`),
  questionPaper: (paperId: string) =>
    request<QuestionPaper>(`/api/question-papers/${segment(paperId)}`),
  report: (reportId: string) => request<AccreditationReport>(`/api/reports/${segment(reportId)}`),
};

export const accessApi = {
  overview: () => request<AccessOverview>("/api/access/overview"),
  effective: (username: string) =>
    request<EffectiveAccess>(`/api/access/users/${segment(username)}/effective`),
  audit: () => request<AuditEntry[]>("/api/access/audit"),
  createGroup: (group: GroupCreateRequest) =>
    request<OkResponse>("/api/access/groups", { method: "POST", json: group }),
  deleteGroup: (name: string) =>
    request<OkResponse>(`/api/access/groups/${segment(name)}`, { method: "DELETE" }),
  addGroupMember: (group: string, username: string) =>
    request<OkResponse>(`/api/access/groups/${segment(group)}/members`, {
      method: "POST",
      json: { username },
    }),
  removeGroupMember: (group: string, username: string) =>
    request<OkResponse>(`/api/access/groups/${segment(group)}/members/${segment(username)}`, {
      method: "DELETE",
    }),
  addGrant: (grant: GrantRequest) =>
    request<OkResponse>("/api/access/grants", { method: "POST", json: grant }),
  revokeGrant: (grant: GrantRequest) =>
    request<OkResponse>("/api/access/grants/revoke", { method: "POST", json: grant }),
  assignRole: (username: string, role: string) =>
    request<OkResponse>(`/api/access/users/${segment(username)}/roles`, {
      method: "POST",
      json: { role },
    }),
  removeRole: (username: string, role: string) =>
    request<OkResponse>(`/api/access/users/${segment(username)}/roles/${segment(role)}`, {
      method: "DELETE",
    }),
  createUser: (user: UserCreateRequest) =>
    request<OkResponse>("/api/access/users", { method: "POST", json: user }),
  resetPassword: (username: string, password: string) =>
    request<OkResponse>(`/api/access/users/${segment(username)}/password`, {
      method: "POST",
      json: { password },
    }),
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Try again.";
}
