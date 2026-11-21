import { memo } from "react";
import { ErrorBanner, Spinner } from "../components/ui";
import { AnswerRenderer } from "../genui/AnswerRenderer";
import { toolLabel, type AssistantMessage, type ChatMessage } from "./messages";

function progressLabel(message: AssistantMessage): string | null {
  if (!message.isStreaming) return null;
  if (message.activeTool) return `${toolLabel(message.activeTool)}…`;
  if (message.text) return null;
  return message.status ?? "Thinking…";
}

function AssistantBubble({ message }: { message: AssistantMessage }) {
  const progress = progressLabel(message);
  return (
    <div className="message message--assistant">
      {message.refusal !== null && <p className="refusal">{message.refusal}</p>}
      {message.text && <AnswerRenderer text={message.text} isStreaming={message.isStreaming} />}
      {progress && <Spinner size="small" label={progress} />}
      {message.error && <ErrorBanner message={message.error.message} />}
    </div>
  );
}

export const MessageItem = memo(function MessageItem({ message }: { message: ChatMessage }) {
  if (message.role === "assistant") return <AssistantBubble message={message} />;
  return (
    <div className="message message--user">
      {message.attachmentLabel && (
        <span className="message-attachment">{message.attachmentLabel}</span>
      )}
      <p>{message.text}</p>
    </div>
  );
});
