import type { ButtonHTMLAttributes } from "react";
import { Spinner } from "./Spinner";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "on-primary";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: "small" | "medium";
  isLoading?: boolean;
}

export function Button({
  variant = "primary",
  size = "medium",
  isLoading = false,
  disabled,
  className,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  const classes = ["button", `button--${variant}`, `button--${size}`, className]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      {...rest}
    >
      {isLoading && <Spinner size="small" />}
      {children}
    </button>
  );
}
