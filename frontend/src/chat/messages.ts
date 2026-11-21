import type { ChatEvent } from "../api/types";

export interface ChatErrorInfo {
  code: string;
  message: string;
}

export interface UserMessage {
  id: string;
  role: "user";
  text: string;
  attachmentLabel: string | null;
}

export interface AssistantMessage {
  id: string;
  role: "assistant";
  text: string;
  refusal: string | null;
  error: ChatErrorInfo | null;
  status: string | null;
  activeTool: string | null;
  isStreaming: boolean;
  latencyMs: number | null;
}

export type ChatMessage = UserMessage | AssistantMessage;

const TOOL_LABELS: Record<string, string> = {
  query_portal_data: "Querying portal data",
  list_views: "Checking available data",
  describe_view: "Reading data layout",
  web_search: "Searching the web",
  generate_quiz: "Making a quiz",
  grade_quiz: "Grading quiz",
  generate_flashcards: "Making flashcards",
  quiz_from_pdf: "Reading your PDF",
  find_at_risk_students: "Finding at-risk students",
  draft_message: "Drafting message",
  make_study_plan: "Making a study plan",
  revision_quiz: "Making a revision quiz",
  generate_question_paper: "Writing a question paper",
  draft_accreditation_report: "Drafting the report",
  list_uploaded_data: "Checking uploaded data",
  query_uploaded_data: "Querying uploaded data",
};

export function toolLabel(toolName: string): string {
  return TOOL_LABELS[toolName] ?? "Working";
}

export function createAssistantMessage(id: string): AssistantMessage {
  return {
    id,
    role: "assistant",
    text: "",
    refusal: null,
    error: null,
    status: null,
    activeTool: null,
    isStreaming: true,
    latencyMs: null,
  };
}

export function applyChatEvent(message: AssistantMessage, event: ChatEvent): AssistantMessage {
  switch (event.type) {
    case "status":
      return { ...message, status: event.text ?? null };
    case "tool":
      return {
        ...message,
        activeTool: event.status === "start" && event.name ? event.name : null,
      };
    case "text":
      return { ...message, text: message.text + (event.delta ?? ""), activeTool: null };
    case "reset":
      return { ...message, text: "" };
    case "refusal":
      return { ...message, text: "", refusal: event.text ?? "" };
    case "error":
      return {
        ...message,
        error: {
          code: event.code ?? "error",
          message: event.message ?? "Something went wrong. Try again.",
        },
      };
    case "done":
      return finishMessage({ ...message, latencyMs: event.latency_ms ?? null });
  }
}

export function finishMessage(message: AssistantMessage): AssistantMessage {
  return { ...message, isStreaming: false, status: null, activeTool: null };
}
