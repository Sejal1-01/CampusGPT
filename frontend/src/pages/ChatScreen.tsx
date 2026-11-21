import { lazy, Suspense, useState } from "react";
import type { Me } from "../api/types";
import { ChatPage } from "../chat/ChatPage";
import { AppHeader, type AppView } from "../components/AppHeader";
import { Spinner } from "../components/ui";
import { useChat } from "../hooks/useChat";

const DashboardPage = lazy(() => import("./DashboardPage"));

export function ChatScreen({ user, onLogout }: { user: Me; onLogout: () => Promise<void> }) {
  const chat = useChat();
  const [view, setView] = useState<AppView>("chat");
  return (
    <div className="app-shell">
      <AppHeader
        user={user}
        onLogout={onLogout}
        onNewChat={view === "chat" ? () => void chat.newChat() : undefined}
        view={view}
        onViewChange={setView}
      />
      {view === "chat" ? (
        <ChatPage chat={chat} starterQuestions={user.starter_questions} />
      ) : (
        <Suspense
          fallback={
            <div className="full-page-center">
              <Spinner size="large" label="Loading dashboard" />
            </div>
          }
        >
          <DashboardPage username={user.username} />
        </Suspense>
      )}
    </div>
  );
}
