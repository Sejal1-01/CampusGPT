import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  message?: string;
  children?: ReactNode;
}

export function EmptyState({ title, message, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="empty-state-title">{title}</p>
      {message && <p className="empty-state-message">{message}</p>}
      {children}
    </div>
  );
}
