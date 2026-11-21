import { accessApi, errorMessage } from "../api/client";
import { Button, Card, EmptyState, ErrorBanner, Spinner, Table } from "../components/ui";
import { formatCell } from "../lib/format";
import { useApi } from "../hooks/useApi";

export function AuditSection() {
  const audit = useApi("access-audit", accessApi.audit);
  const actions = (
    <Button variant="ghost" size="small" onClick={audit.reload} isLoading={audit.isLoading}>
      Refresh
    </Button>
  );

  if (audit.error)
    return <ErrorBanner message={errorMessage(audit.error)} onRetry={audit.reload} />;
  if (!audit.data) return <Spinner label="Loading audit log" />;
  if (audit.data.length === 0) return <EmptyState title="No changes yet" />;

  const rows = audit.data.map((entry) => [
    entry.changed_at,
    formatCell(entry.changed_by),
    entry.action,
    entry.target,
    entry.details,
  ]);
  return (
    <Card title="Audit log" actions={actions}>
      <Table columns={["When", "By", "Action", "Target", "Details"]} rows={rows} />
    </Card>
  );
}
