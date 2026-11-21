import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, api, errorMessage } from "../api/client";
import {
  applyChatEvent,
  createAssistantMessage,
  finishMessage,
  type AssistantMessage,
  type ChatMessage,
} from "../chat/messages";
import { readChatEvents } from "../chat/sse";

export interface PdfAttachment {
  fileId: string;
  filename: string;
}

export interface CsvAttachment {
  tableName: string;
  columns: string[];
  rows: number;
  filename: string;
}

export type ChatAttachment = PdfAttachment | CsvAttachment;

export function attachmentPrefix(attachment: ChatAttachment): string {
  if ("tableName" in attachment) {
    return `[Attached CSV table=${attachment.tableName} columns=${attachment.columns.join(",")}] `;
  }
  return `[Attached PDF file_id=${attachment.fileId} name=${attachment.filename}] `;
}

export function attachmentLabel(attachment: ChatAttachment): string {
  return `${"tableName" in attachment ? "CSV" : "PDF"}: ${attachment.filename}`;
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function toChatError(error: unknown): { code: string; message: string } {
  if (error instanceof ApiError) return { code: error.code, message: error.message };
  return { code: "error", message: errorMessage(error) };
}

export interface ChatState {
  messages: ChatMessage[];
  isAnswering: boolean;
  resetError: string | null;
  sendMessage: (text: string, attachment?: ChatAttachment | null) => Promise<boolean>;
  newChat: () => Promise<void>;
}

export function useChat(): ChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAnswering, setIsAnswering] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const messageCounterRef = useRef(0);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const updateLastAssistant = useCallback(
    (update: (message: AssistantMessage) => AssistantMessage) => {
      setMessages((previous) => {
        const last = previous.at(-1);
        if (!last || last.role !== "assistant") return previous;
        return [...previous.slice(0, -1), update(last)];
      });
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string, attachment: ChatAttachment | null = null) => {
      const trimmed = text.trim();
      if (!trimmed || controllerRef.current) return false;
      const controller = new AbortController();
      controllerRef.current = controller;
      messageCounterRef.current += 1;
      const id = String(messageCounterRef.current);
      setIsAnswering(true);
      setResetError(null);
      setMessages((previous) => [
        ...previous,
        {
          id: `user-${id}`,
          role: "user",
          text: trimmed,
          attachmentLabel: attachment ? attachmentLabel(attachment) : null,
        },
        createAssistantMessage(`assistant-${id}`),
      ]);
      const payload = attachment ? attachmentPrefix(attachment) + trimmed : trimmed;
      try {
        const response = await api.openChatStream(payload, controller.signal);
        if (!response.body) throw new ApiError("empty_reply", "No reply received. Try again.", 0);
        for await (const event of readChatEvents(response.body)) {
          updateLastAssistant((message) => applyChatEvent(message, event));
        }
      } catch (error) {
        if (!isAbort(error)) {
          updateLastAssistant((message) => ({ ...message, error: toChatError(error) }));
        }
      } finally {
        if (controllerRef.current === controller) {
          controllerRef.current = null;
          updateLastAssistant(finishMessage);
          setIsAnswering(false);
        }
      }
      return true;
    },
    [updateLastAssistant],
  );

  const newChat = useCallback(async () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setMessages([]);
    setIsAnswering(false);
    setResetError(null);
    try {
      await api.resetChat();
    } catch (error) {
      setResetError(errorMessage(error));
    }
  }, []);

  return { messages, isAnswering, resetError, sendMessage, newChat };
}
