import { lazy, Suspense } from "react";
import { AppHeader } from "./components/AppHeader";
import { Spinner } from "./components/ui";
import { useAuth } from "./hooks/useAuth";
import { ChatScreen } from "./pages/ChatScreen";
import { LoginPage } from "./pages/LoginPage";

const AccessPage = lazy(() => import("./access/AccessPage"));

function FullPageSpinner({ label }: { label: string }) {
  return (
    <div className="full-page-center">
      <Spinner size="large" label={label} />
    </div>
  );
}

export function App() {
  const { status, user, logout } = useAuth();
  if (status === "loading") return <FullPageSpinner label="Loading" />;
  if (!user) return <LoginPage />;
  if (!user.is_platform_admin) return <ChatScreen user={user} onLogout={logout} />;
  return (
    <div className="app-shell">
      <AppHeader user={user} onLogout={logout} />
      <Suspense fallback={<FullPageSpinner label="Loading access" />}>
        <AccessPage />
      </Suspense>
    </div>
  );
}
