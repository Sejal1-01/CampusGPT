import { useMemo } from "react";
import { api } from "../../api/client";
import type { StudyPlan, StudyPlanDay } from "../../api/types";
import { Button, Card, EmptyState, Table } from "../../components/ui";
import { downloadTextFile } from "../../lib/download";
import { formatDay, formatNumber, toIsoDate } from "../../lib/format";
import { studyPlanMarkdown } from "../markdownExport";
import { useAnswerData } from "../useAnswerData";
import { ContentStatus } from "./ContentStatus";

const COLUMNS = ["Date", "Subject", "Hours", "Tasks"];

function DayCell({
  day,
  isCurrent,
  today,
}: {
  day: StudyPlanDay;
  isCurrent: boolean;
  today: string;
}) {
  return (
    <span className="plan-day">
      {formatDay(day.date)}
      {isCurrent && <span className="badge">{day.date === today ? "Today" : "Next"}</span>}
    </span>
  );
}

function StudyPlanBody({ plan }: { plan: StudyPlan }) {
  const today = toIsoDate(new Date());
  const current = plan.days.findIndex((day) => day.date >= today);
  const rows = useMemo(
    () =>
      plan.days.map((day, index) => [
        <DayCell key="date" day={day} isCurrent={index === current} today={today} />,
        day.subject,
        formatNumber(day.hours),
        <ul key="tasks" className="plan-tasks">
          {day.tasks.map((task, taskIndex) => (
            <li key={taskIndex}>{task}</li>
          ))}
        </ul>,
      ]),
    [plan.days, current, today],
  );

  return (
    <Card
      title={plan.title}
      className="study-plan"
      actions={
        <Button
          variant="secondary"
          size="small"
          onClick={() => downloadTextFile(`study-plan-${plan.plan_id}.md`, studyPlanMarkdown(plan))}
        >
          Download
        </Button>
      }
    >
      {plan.notes && <p className="plan-notes">{plan.notes}</p>}
      {plan.days.length === 0 ? (
        <EmptyState title="No study days" message="There are no upcoming exams to plan for." />
      ) : (
        <Table
          columns={COLUMNS}
          rows={rows}
          caption={plan.title}
          highlightedRow={current >= 0 ? current : undefined}
        />
      )}
    </Card>
  );
}

export function StudyPlanView({ planId }: { planId: string }) {
  const plan = useAnswerData(`study-plan:${planId}`, () => api.studyPlan(planId));
  if (plan.data) return <StudyPlanBody plan={plan.data} />;
  return (
    <Card title="Study plan">
      <ContentStatus
        error={plan.error}
        loadingLabel="Loading study plan"
        notFoundTitle="Study plan not found"
        onRetry={plan.reload}
      />
    </Card>
  );
}
