import { errorMessage } from "../../api/client";
import { ErrorBanner, Spinner } from "../../components/ui";

interface ResultStatusProps {
  isLoading: boolean;
  error: unknown;
  loadingLabel: string;
  onRetry: () => void;
}

export function ResultStatus({ isLoading, error, loadingLabel, onRetry }: ResultStatusProps) {
  if (error) return <ErrorBanner message={errorMessage(error)} onRetry={onRetry} />;
  if (isLoading) return <Spinner label={loadingLabel} />;
  return null;
}
