import { api } from "../../api/client";
import type { AccreditationReport } from "../../api/types";
import { Markdown } from "../../components/Markdown";
import { Button, Card } from "../../components/ui";
import { downloadTextFile } from "../../lib/download";
import { reportMarkdown } from "../markdownExport";
import { useAnswerData } from "../useAnswerData";
import { ContentStatus } from "./ContentStatus";
import { DataTableView } from "./DataTableView";

function ReportBody({ report }: { report: AccreditationReport }) {
  return (
    <Card
      title="Accreditation report"
      actions={
        <>
          <span className="badge badge--draft">Draft – for committee review</span>
          <Button
            variant="secondary"
            size="small"
            onClick={() =>
              downloadTextFile(`report-${report.report_id}.md`, reportMarkdown(report))
            }
          >
            Download
          </Button>
        </>
      }
    >
      <p className="report-scope">
        <span className="muted">Scope:</span> {report.scope}
      </p>
      {report.sections.map((section, index) => (
        <section key={`${index}-${section.heading}`} className="report-section">
          <h4 className="report-heading">{section.heading}</h4>
          <Markdown text={section.body} />
        </section>
      ))}
      {report.result_ids.map((resultId) => (
        <DataTableView key={resultId} resultId={resultId} />
      ))}
    </Card>
  );
}

export function ReportDraftView({ reportId }: { reportId: string }) {
  const report = useAnswerData(`report:${reportId}`, () => api.report(reportId));
  if (report.data) return <ReportBody report={report.data} />;
  return (
    <Card title="Accreditation report">
      <ContentStatus
        error={report.error}
        loadingLabel="Loading report"
        notFoundTitle="Report not found"
        onRetry={report.reload}
      />
    </Card>
  );
}
