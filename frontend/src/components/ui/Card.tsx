import type { ReactNode } from "react";

interface CardProps {
  title?: ReactNode;
  actions?: ReactNode;
  footer?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function Card({ title, actions, footer, className, children }: CardProps) {
  return (
    <section className={["card", className].filter(Boolean).join(" ")}>
      {(title || actions) && (
        <header className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      <div className="card-body">{children}</div>
      {footer && <footer className="card-footer">{footer}</footer>}
    </section>
  );
}
