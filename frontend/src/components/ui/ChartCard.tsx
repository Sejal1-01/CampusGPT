import type { ReactNode } from "react";
import { Card } from "./Card";

interface ChartCardProps {
  title?: string;
  footer?: ReactNode;
  children: ReactNode;
}

export function ChartCard({ title, footer, children }: ChartCardProps) {
  return (
    <Card title={title} footer={footer} className="chart-card">
      <div className="chart-area">{children}</div>
    </Card>
  );
}
