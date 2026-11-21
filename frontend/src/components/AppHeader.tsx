import { useState } from "react";
import type { Me } from "../api/types";
import { formatRole } from "../lib/format";
import { Button } from "./ui";

export type AppView = "chat" | "dashboard";

interface AppHeaderProps {
  user: Me;
  onLogout: () => Promise<void>;
  onNewChat?: () => void;
  view?: AppView;
  onViewChange?: (view: AppView) => void;
}

function roleLabel(user: Me): string {
  if (user.is_platform_admin) return "Platform Admin";
  return user.roles.map(formatRole).join(", ") || "User";
}

export function AppHeader({ user, onLogout, onNewChat, view, onViewChange }: AppHeaderProps) {
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const logout = async () => {
    setIsLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <header className="app-header">
      <div className="app-brand">
        <img src="/iiitbh-logo.png" alt="IIIT Bhagalpur logo" className="app-logo" />
        <span className="app-title">IIIT Bhagalpur · CampusGPT</span>
      </div>
      <div className="app-user">
        <span className="app-user-name">{user.display_name}</span>
        <span className="role-badge">{roleLabel(user)}</span>
        {onViewChange && (
          <Button
            variant="on-primary"
            size="small"
            onClick={() => onViewChange(view === "dashboard" ? "chat" : "dashboard")}
          >
            {view === "dashboard" ? "Chat" : "Dashboard"}
          </Button>
        )}
        {onNewChat && (
          <Button variant="on-primary" size="small" onClick={onNewChat}>
            New chat
          </Button>
        )}
        <Button variant="on-primary" size="small" onClick={logout} isLoading={isLoggingOut}>
          Logout
        </Button>
      </div>
    </header>
  );
}
