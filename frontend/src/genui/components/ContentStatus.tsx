import { ApiError, errorMessage } from "../../api/client";
import { EmptyState, ErrorBanner, Spinner } from "../../components/ui";

interface ContentStatusProps {
  error: unknown;
  loadingLabel: string;
  notFoundTitle: string;
  onRetry: () => void;
}

export function ContentStatus({ error, loadingLabel, notFoundTitle, onRetry }: ContentStatusProps) {
  if (error instanceof ApiError && error.status === 404) {
    return (
      <EmptyState
        title={notFoundTitle}
        message="It may have expired. Ask again to make a new one."
      />
    );
  }
  if (error) return <ErrorBanner message={errorMessage(error)} onRetry={onRetry} />;
  return <Spinner label={loadingLabel} />;
}
