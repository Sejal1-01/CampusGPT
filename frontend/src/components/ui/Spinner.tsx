interface SpinnerProps {
  label?: string;
  size?: "small" | "medium" | "large";
}

export function Spinner({ label, size = "medium" }: SpinnerProps) {
  return (
    <span className="spinner-wrapper" role="status" aria-live="polite">
      <span className={`spinner spinner--${size}`} aria-hidden="true" />
      {label ? (
        <span className="spinner-label">{label}</span>
      ) : (
        <span className="visually-hidden">Loading</span>
      )}
    </span>
  );
}
