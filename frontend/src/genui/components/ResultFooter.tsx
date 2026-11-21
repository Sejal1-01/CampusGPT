import { api } from "../../api/client";
import type { StoredResult } from "../../api/types";
import type { TileSpec } from "../../lib/pinnedTiles";
import { PinButton } from "./PinButton";

export type PinTarget = Omit<TileSpec, "sql" | "explanation">;

export function ResultFooter({ result, pin }: { result: StoredResult; pin?: PinTarget }) {
  return (
    <div className="result-footer">
      <details className="how-i-got-this">
        <summary>How I got this</summary>
        {result.explanation && <p className="how-i-got-this-explanation">{result.explanation}</p>}
        <pre className="sql-block">
          <code>{result.sql}</code>
        </pre>
      </details>
      <div className="result-footer-actions">
        {pin && <PinButton spec={{ ...pin, sql: result.sql, explanation: result.explanation }} />}
        <a className="csv-link" href={api.resultCsvUrl(result.result_id)} download>
          Download CSV
        </a>
      </div>
    </div>
  );
}
