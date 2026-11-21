import type { ChatEvent } from "../api/types";

const CHAT_EVENT_TYPES: ReadonlySet<string> = new Set([
  "status",
  "tool",
  "text",
  "reset",
  "refusal",
  "error",
  "done",
]);

function isChatEvent(value: unknown): value is ChatEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof value.type === "string" &&
    CHAT_EVENT_TYPES.has(value.type)
  );
}

function parseEventBlock(block: string): ChatEvent | null {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""))
    .join("\n");
  if (!data) return null;
  try {
    const parsed: unknown = JSON.parse(data);
    return isChatEvent(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function splitSseBuffer(buffer: string): { events: ChatEvent[]; rest: string } {
  const normalised = buffer.replace(/\r\n?/g, "\n");
  const blocks = normalised.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events = blocks.map(parseEventBlock).filter((event) => event !== null);
  return { events, rest };
}

export async function* readChatEvents(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<ChatEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const { events, rest } = splitSseBuffer(done ? `${buffer}\n\n` : buffer);
      buffer = rest;
      yield* events;
      if (done) return;
    }
  } finally {
    reader.releaseLock();
  }
}
