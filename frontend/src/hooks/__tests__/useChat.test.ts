import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AssistantMessage } from "../../chat/messages";
import {
  errorResponse,
  jsonResponse,
  mockFetch,
  requestBody,
  sseResponse,
} from "../../test/fetchMock";
import { useChat } from "../useChat";

function lastAssistant(messages: unknown[]): AssistantMessage {
  return messages.at(-1) as AssistantMessage;
}

describe("useChat", () => {
  it("streams text into the last assistant message", async () => {
    mockFetch({
      "POST /api/chat": () =>
        sseResponse([
          { type: "status", text: "Checking your question" },
          { type: "text", delta: "Let me look" },
          { type: "reset" },
          { type: "tool", name: "query_portal_data", status: "start" },
          { type: "tool", name: "query_portal_data", status: "end" },
          { type: "text", delta: "root = Answer([t])\n" },
          { type: "text", delta: 't = TextBlock("Hi")' },
          { type: "done", latency_ms: 50 },
        ]),
    });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.sendMessage("  hello  "));
    const [user, assistant] = result.current.messages;
    expect(user).toMatchObject({ role: "user", text: "hello" });
    expect(assistant).toMatchObject({
      role: "assistant",
      text: 'root = Answer([t])\nt = TextBlock("Hi")',
      isStreaming: false,
      latencyMs: 50,
    });
    expect(result.current.isAnswering).toBe(false);
  });

  it("ignores empty messages", async () => {
    const fetchMock = mockFetch({});
    const { result } = renderHook(() => useChat());
    await act(async () => {
      expect(await result.current.sendMessage("   ")).toBe(false);
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows refusals and stream errors", async () => {
    mockFetch({
      "POST /api/chat": () =>
        sseResponse([
          { type: "refusal", text: "I can only help with campus questions." },
          { type: "error", code: "model_error", message: "The model failed." },
          { type: "done" },
        ]),
    });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.sendMessage("build a website"));
    const assistant = lastAssistant(result.current.messages);
    expect(assistant.refusal).toBe("I can only help with campus questions.");
    expect(assistant.error?.message).toBe("The model failed.");
  });

  it("shows pre-stream errors such as busy", async () => {
    mockFetch({
      "POST /api/chat": () => errorResponse(409, "busy", "Still answering. Wait a moment."),
    });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.sendMessage("again"));
    const assistant = lastAssistant(result.current.messages);
    expect(assistant.error).toEqual({ code: "busy", message: "Still answering. Wait a moment." });
    expect(assistant.isStreaming).toBe(false);
  });

  it("prefixes the attached PDF", async () => {
    const fetchMock = mockFetch({ "POST /api/chat": () => sseResponse([{ type: "done" }]) });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.sendMessage("Quiz me", { fileId: "f1", filename: "notes.pdf" }));
    expect(requestBody(fetchMock.mock.calls[0]?.[1])).toEqual({
      message: "[Attached PDF file_id=f1 name=notes.pdf] Quiz me",
    });
    expect(result.current.messages[0]).toMatchObject({
      text: "Quiz me",
      attachmentLabel: "PDF: notes.pdf",
    });
  });

  it("prefixes the attached CSV table and columns", async () => {
    const fetchMock = mockFetch({ "POST /api/chat": () => sseResponse([{ type: "done" }]) });
    const { result } = renderHook(() => useChat());
    await act(() =>
      result.current.sendMessage("Average marks?", {
        tableName: "upload_marks",
        columns: ["roll_no", "marks"],
        rows: 2,
        filename: "marks.csv",
      }),
    );
    expect(requestBody(fetchMock.mock.calls[0]?.[1])).toEqual({
      message: "[Attached CSV table=upload_marks columns=roll_no,marks] Average marks?",
    });
    expect(result.current.messages[0]).toMatchObject({ attachmentLabel: "CSV: marks.csv" });
  });

  it("clears history on new chat", async () => {
    const fetchMock = mockFetch({
      "POST /api/chat": () => sseResponse([{ type: "done" }]),
      "POST /api/chat/reset": () => jsonResponse({ ok: true }),
    });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.sendMessage("hi"));
    await act(() => result.current.newChat());
    expect(result.current.messages).toEqual([]);
    expect(fetchMock).toHaveBeenCalledWith("/api/chat/reset", expect.anything());
  });

  it("reports a failed reset", async () => {
    mockFetch({
      "POST /api/chat/reset": () => errorResponse(503, "unavailable", "Server is busy."),
    });
    const { result } = renderHook(() => useChat());
    await act(() => result.current.newChat());
    expect(result.current.resetError).toBe("Server is busy.");
  });
});
