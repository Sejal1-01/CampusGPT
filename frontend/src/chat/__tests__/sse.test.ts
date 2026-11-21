import { describe, expect, it } from "vitest";
import { readChatEvents, splitSseBuffer } from "../sse";

function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

describe("splitSseBuffer", () => {
  it("returns complete events and keeps the partial rest", () => {
    const { events, rest } = splitSseBuffer(
      'data: {"type":"text","delta":"a"}\n\ndata: {"type":"te',
    );
    expect(events).toEqual([{ type: "text", delta: "a" }]);
    expect(rest).toBe('data: {"type":"te');
  });

  it("handles CRLF line endings", () => {
    const { events } = splitSseBuffer('data: {"type":"reset"}\r\n\r\n');
    expect(events).toEqual([{ type: "reset" }]);
  });

  it("ignores comments, malformed JSON and unknown types", () => {
    const { events } = splitSseBuffer(': ping\n\ndata: {nope\n\ndata: {"type":"other"}\n\n');
    expect(events).toEqual([]);
  });
});

describe("readChatEvents", () => {
  it("parses events split across chunks", async () => {
    const stream = streamOf([
      'data: {"type":"status","text":"Checking"}\n\ndata: {"type":"te',
      'xt","delta":"root = "}\n',
      '\ndata: {"type":"done","latency_ms":12}\n\n',
    ]);
    const events = [];
    for await (const event of readChatEvents(stream)) events.push(event);
    expect(events).toEqual([
      { type: "status", text: "Checking" },
      { type: "text", delta: "root = " },
      { type: "done", latency_ms: 12 },
    ]);
  });

  it("reads a final event without a trailing blank line", async () => {
    const events = [];
    for await (const event of readChatEvents(streamOf(['data: {"type":"done"}'])))
      events.push(event);
    expect(events).toEqual([{ type: "done" }]);
  });
});
