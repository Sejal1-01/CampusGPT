import { Button } from "./Button";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorBanner({ message, onRetry, onDismiss }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-banner-message">{message}</span>
      {onRetry && (
        <Button variant="secondary" size="small" onClick={onRetry}>
          Retry
        </Button>
      )}
      {onDismiss && (
        <Button variant="ghost" size="small" onClick={onDismiss} aria-label="Dismiss">
          ×
        </Button>
      )}
    </div>
  );
}
