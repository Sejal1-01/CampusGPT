import { useState } from "react";
import { api } from "../api/client";
import type { StoredResult } from "../api/types";
import { Button, Card, EmptyState, ErrorBanner } from "../components/ui";
import { ChartBody } from "../genui/components/DataChartView";
import { ResultFooter } from "../genui/components/ResultFooter";
import { ResultStatus } from "../genui/components/ResultStatus";
import { ResultTable } from "../genui/components/ResultTable";
import { useApi } from "../hooks/useApi";
import { loadPins, unpinTile, type PinnedTile } from "../lib/pinnedTiles";

interface TileProps {
  tile: PinnedTile;
  round: number;
  onRemove: () => void;
}

function TileBody({ tile, result }: { tile: PinnedTile; result: StoredResult }) {
  if (tile.kind !== "table") {
    return <ChartBody result={result} kind={tile.kind} x={tile.x} y={tile.y} title={tile.title} />;
  }
  if (result.rows.length === 0) return <EmptyState title="No matching records" />;
  return <ResultTable result={result} title={tile.title} />;
}

function DashboardTile({ tile, round, onRemove }: TileProps) {
  const result = useApi(`rerun:${tile.id}:${round}`, () =>
    api.rerunResult({ sql: tile.sql, explanation: tile.explanation }),
  );
  return (
    <Card
      title={tile.title}
      className="dashboard-tile"
      actions={
        <Button variant="ghost" size="small" onClick={onRemove}>
          Remove
        </Button>
      }
      footer={result.data ? <ResultFooter result={result.data} /> : undefined}
    >
      {result.data ? (
        <TileBody tile={tile} result={result.data} />
      ) : (
        <ResultStatus
          isLoading={result.isLoading}
          error={result.error}
          loadingLabel="Running query"
          onRetry={result.reload}
        />
      )}
    </Card>
  );
}

export default function DashboardPage({ username }: { username: string }) {
  const [tiles, setTiles] = useState(() => loadPins(username));
  const [round, setRound] = useState(0);
  const [removeError, setRemoveError] = useState<string | null>(null);

  const remove = (tileId: string) => {
    if (!unpinTile(username, tileId)) {
      setRemoveError("Couldn't remove the tile. Browser storage is blocked.");
      return;
    }
    setRemoveError(null);
    setTiles((current) => current.filter((tile) => tile.id !== tileId));
  };

  return (
    <main className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="page-title">Dashboard</h1>
        {tiles.length > 0 && (
          <Button variant="secondary" size="small" onClick={() => setRound((value) => value + 1)}>
            Refresh all
          </Button>
        )}
      </div>
      {removeError && <ErrorBanner message={removeError} onDismiss={() => setRemoveError(null)} />}
      {tiles.length === 0 ? (
        <EmptyState
          title="Nothing pinned yet"
          message="Use Pin under a chart or table in the chat to add it here."
        />
      ) : (
        <div className="dashboard-grid">
          {tiles.map((tile) => (
            <DashboardTile
              key={tile.id}
              tile={tile}
              round={round}
              onRemove={() => remove(tile.id)}
            />
          ))}
        </div>
      )}
    </main>
  );
}
