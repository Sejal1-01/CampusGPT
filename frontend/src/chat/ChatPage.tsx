import { ErrorBanner } from "../components/ui";
import type { ChatState } from "../hooks/useChat";
import { Composer } from "./Composer";
import { MessageList } from "./MessageList";
import { StarterQuestions } from "./StarterQuestions";

interface ChatPageProps {
  chat: ChatState;
  starterQuestions: string[];
}

export function ChatPage({ chat, starterQuestions }: ChatPageProps) {
  const isEmpty = chat.messages.length === 0;
  return (
    <main className="chat-page">
      {chat.resetError && <ErrorBanner message={chat.resetError} />}
      {isEmpty ? (
        <StarterQuestions
          questions={starterQuestions}
          disabled={chat.isAnswering}
          onPick={(question) => void chat.sendMessage(question)}
        />
      ) : (
        <MessageList messages={chat.messages} />
      )}
      <Composer isAnswering={chat.isAnswering} onSend={chat.sendMessage} />
    </main>
  );
}
