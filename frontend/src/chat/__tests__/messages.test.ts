import { describe, expect, it } from "vitest";
import { applyChatEvent, createAssistantMessage, toolLabel } from "../messages";

const start = createAssistantMessage("a1");

describe("applyChatEvent", () => {
  it("appends text deltas", () => {
    const once = applyChatEvent(start, { type: "text", delta: "root = " });
    const twice = applyChatEvent(once, { type: "text", delta: "Answer([])" });
    expect(twice.text).toBe("root = Answer([])");
  });

  it("discards interim text on reset", () => {
    const withText = applyChatEvent(start, { type: "text", delta: "Let me check" });
    expect(applyChatEvent(withText, { type: "reset" }).text).toBe("");
  });

  it("tracks status and tool progress", () => {
    const status = applyChatEvent(start, { type: "status", text: "Checking your question" });
    expect(status.status).toBe("Checking your question");
    const running = applyChatEvent(status, {
      type: "tool",
      name: "query_portal_data",
      status: "start",
    });
    expect(running.activeTool).toBe("query_portal_data");
    expect(
      applyChatEvent(running, { type: "tool", name: "query_portal_data", status: "end" })
        .activeTool,
    ).toBeNull();
  });

  it("stores refusals as plain text", () => {
    const refused = applyChatEvent(start, {
      type: "refusal",
      text: "I can only help with campus questions.",
    });
    expect(refused.refusal).toBe("I can only help with campus questions.");
    expect(refused.text).toBe("");
  });

  it("stores errors", () => {
    const failed = applyChatEvent(start, {
      type: "error",
      code: "timeout",
      message: "Took too long.",
    });
    expect(failed.error).toEqual({ code: "timeout", message: "Took too long." });
  });

  it("finishes on done", () => {
    const done = applyChatEvent(start, { type: "done", latency_ms: 900 });
    expect(done.isStreaming).toBe(false);
    expect(done.latencyMs).toBe(900);
  });
});

describe("toolLabel", () => {
  it("names known tools and falls back for others", () => {
    expect(toolLabel("query_portal_data")).toBe("Querying portal data");
    expect(toolLabel("something_new")).toBe("Working");
  });
});
