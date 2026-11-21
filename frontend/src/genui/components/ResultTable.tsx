import { memo, useMemo } from "react";
import type { StoredResult } from "../../api/types";
import { Table } from "../../components/ui";
import { formatCell } from "../../lib/format";

export const ResultTable = memo(function ResultTable({
  result,
  title,
}: {
  result: StoredResult;
  title?: string;
}) {
  const rows = useMemo(() => result.rows.map((row) => row.map(formatCell)), [result.rows]);
  return (
    <>
      <Table columns={result.columns} rows={rows} caption={title} />
      <p className="table-count">
        {result.truncated
          ? `Showing ${result.rows.length} of ${result.total_rows} rows`
          : `${result.rows.length} ${result.rows.length === 1 ? "row" : "rows"}`}
      </p>
    </>
  );
});
