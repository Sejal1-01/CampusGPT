import { useState } from "react";
import { Button, Card } from "../../components/ui";

interface MessageDraftViewProps {
  to: string;
  subject: string;
  body: string;
}

type CopyState = "idle" | "copied" | "failed";

const COPY_LABELS: Record<CopyState, string> = {
  idle: "Copy",
  copied: "Copied",
  failed: "Copy failed",
};

export function MessageDraftView({ to, subject, body }: MessageDraftViewProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`To: ${to}\nSubject: ${subject}\n\n${body}`);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  };

  return (
    <Card
      title="Message draft"
      actions={
        <Button variant="secondary" size="small" onClick={copy}>
          {COPY_LABELS[copyState]}
        </Button>
      }
      footer={<span className="draft-note">Draft only – not sent</span>}
    >
      <dl className="draft-fields">
        <dt>To</dt>
        <dd>{to}</dd>
        <dt>Subject</dt>
        <dd>{subject}</dd>
      </dl>
      <p className="draft-body">{body}</p>
    </Card>
  );
}
