import { memo } from "react";
import type { StoredResult } from "../../api/types";
import { Card, EmptyState } from "../../components/ui";
import { useStoredResult } from "../useStoredResult";
import { ResultFooter, type PinTarget } from "./ResultFooter";
import { ResultStatus } from "./ResultStatus";
import { ResultTable } from "./ResultTable";

function tablePin(result: StoredResult, title: string | undefined): PinTarget {
  return { title: title ?? (result.explanation || "Pinned table"), kind: "table", x: "", y: [] };
}

export const DataTableView = memo(function DataTableView({
  resultId,
  title,
}: {
  resultId: string;
  title?: string;
}) {
  const { data, error, isLoading, reload } = useStoredResult(resultId);
  if (!data) {
    return (
      <Card title={title}>
        <ResultStatus
          isLoading={isLoading}
          error={error}
          loadingLabel="Loading table"
          onRetry={reload}
        />
      </Card>
    );
  }
  return (
    <Card title={title} footer={<ResultFooter result={data} pin={tablePin(data, title)} />}>
      {data.rows.length === 0 ? (
        <EmptyState title="No matching records" />
      ) : (
        <ResultTable result={data} title={title} />
      )}
    </Card>
  );
});
