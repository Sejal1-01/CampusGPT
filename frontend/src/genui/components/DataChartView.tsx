import { lazy, memo, Suspense, useMemo } from "react";
import type { StoredResult } from "../../api/types";
import { ChartCard, EmptyState, Spinner } from "../../components/ui";
import { planChart, type ChartKind } from "../chartPlan";
import { useStoredResult } from "../useStoredResult";
import { ResultFooter } from "./ResultFooter";
import { ResultStatus } from "./ResultStatus";
import { ResultTable } from "./ResultTable";

const ResultChart = lazy(() => import("./ResultChart"));

interface DataChartViewProps {
  resultId: string;
  kind: ChartKind;
  x: string;
  y: string[];
  title?: string;
}

export function ChartBody({
  result,
  kind,
  x,
  y,
  title,
}: Omit<DataChartViewProps, "resultId"> & { result: StoredResult }) {
  const plan = useMemo(() => planChart(result, kind, x, y), [result, kind, x, y]);
  if (plan.mode === "empty") return <EmptyState title="No matching records" />;
  if (plan.mode === "table") return <ResultTable result={result} title={title} />;
  return (
    <Suspense fallback={<Spinner label="Loading chart" />}>
      <ResultChart kind={kind} points={plan.points} series={plan.series} xLabel={x} />
    </Suspense>
  );
}

export const DataChartView = memo(function DataChartView(props: DataChartViewProps) {
  const { data, error, isLoading, reload } = useStoredResult(props.resultId);
  const pin = {
    title: props.title ?? `${props.y.join(", ")} by ${props.x}`,
    kind: props.kind,
    x: props.x,
    y: props.y,
  };
  return (
    <ChartCard
      title={props.title}
      footer={data ? <ResultFooter result={data} pin={pin} /> : undefined}
    >
      {data ? (
        <ChartBody result={data} kind={props.kind} x={props.x} y={props.y} title={props.title} />
      ) : (
        <ResultStatus
          isLoading={isLoading}
          error={error}
          loadingLabel="Loading chart"
          onRetry={reload}
        />
      )}
    </ChartCard>
  );
});
