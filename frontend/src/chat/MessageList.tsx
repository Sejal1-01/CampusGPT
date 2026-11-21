import { useEffect, useRef } from "react";
import type { ChatMessage } from "./messages";
import { MessageItem } from "./MessageItem";

const STICK_TO_BOTTOM_PX = 120;

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const last = messages.at(-1);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    if (distance < STICK_TO_BOTTOM_PX || last?.role === "user") {
      element.scrollTop = element.scrollHeight;
    }
  }, [last]);

  return (
    <div ref={scrollRef} className="message-list" aria-live="polite">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
}
