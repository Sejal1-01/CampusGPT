import { useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from "react";
import { api, errorMessage } from "../api/client";
import { Button, ErrorBanner } from "../components/ui";
import {
  MAX_CSV_BYTES,
  MAX_MESSAGE_CHARS,
  MAX_PDF_BYTES,
  MESSAGE_LENGTH_WARNING_CHARS,
} from "../config";
import type { ChatAttachment } from "../hooks/useChat";

interface ComposerProps {
  isAnswering: boolean;
  onSend: (text: string, attachment: ChatAttachment | null) => Promise<boolean>;
}

function validatePdf(file: File): string | null {
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    return "That file is not a PDF.";
  }
  if (file.size > MAX_PDF_BYTES) return "PDF is over 10 MB. Choose a smaller file.";
  return null;
}

function validateCsv(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) return "That file is not a CSV.";
  if (file.size > MAX_CSV_BYTES) return "CSV is over 5 MB. Choose a smaller file.";
  return null;
}

async function uploadPdf(file: File): Promise<ChatAttachment> {
  const uploaded = await api.uploadPdf(file);
  return { fileId: uploaded.file_id, filename: uploaded.filename };
}

async function uploadCsv(file: File): Promise<ChatAttachment> {
  const uploaded = await api.uploadCsv(file);
  return {
    tableName: uploaded.table_name,
    columns: uploaded.columns,
    rows: uploaded.rows,
    filename: file.name,
  };
}

type UploadKind = "pdf" | "csv";

const UPLOADERS: Record<
  UploadKind,
  { validate: (file: File) => string | null; upload: (file: File) => Promise<ChatAttachment> }
> = {
  pdf: { validate: validatePdf, upload: uploadPdf },
  csv: { validate: validateCsv, upload: uploadCsv },
};

function chipText(attachment: ChatAttachment): string {
  if ("tableName" in attachment) {
    const rows = `${attachment.rows.toLocaleString("en-IN")} ${attachment.rows === 1 ? "row" : "rows"}`;
    return `${attachment.tableName} · ${rows}`;
  }
  return `PDF: ${attachment.filename}`;
}

export function Composer({ isAnswering, onSend }: ComposerProps) {
  const [text, setText] = useState("");
  const [attachment, setAttachment] = useState<ChatAttachment | null>(null);
  const [uploading, setUploading] = useState<UploadKind | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const csvRef = useRef<HTMLInputElement>(null);

  const isUploading = uploading !== null;
  const length = text.length;
  const isTooLong = length > MAX_MESSAGE_CHARS;
  const canSend = text.trim().length > 0 && !isTooLong && !isAnswering && !isUploading;

  const submit = async () => {
    if (!canSend) return;
    const message = text;
    const sentAttachment = attachment;
    setText("");
    setAttachment(null);
    inputRef.current?.focus();
    await onSend(message, sentAttachment);
    inputRef.current?.focus();
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    void submit();
  };

  const attach = async (event: ChangeEvent<HTMLInputElement>, kind: UploadKind) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const { validate, upload } = UPLOADERS[kind];
    const problem = validate(file);
    setUploadError(problem);
    if (problem) return;
    setUploading(kind);
    try {
      setAttachment(await upload(file));
    } catch (error) {
      setUploadError(errorMessage(error));
    } finally {
      setUploading(null);
      inputRef.current?.focus();
    }
  };

  return (
    <form className="composer" onSubmit={handleSubmit}>
      {uploadError && <ErrorBanner message={uploadError} onDismiss={() => setUploadError(null)} />}
      {attachment && (
        <div className="attachment-chip">
          <span>{chipText(attachment)}</span>
          <button
            type="button"
            className="chip-remove"
            aria-label="Remove attachment"
            onClick={() => setAttachment(null)}
          >
            ×
          </button>
        </div>
      )}
      <div className="composer-row">
        <input
          ref={fileRef}
          type="file"
          accept="application/pdf,.pdf"
          className="visually-hidden"
          aria-label="PDF file"
          tabIndex={-1}
          onChange={(event) => void attach(event, "pdf")}
        />
        <input
          ref={csvRef}
          type="file"
          accept=".csv,text/csv"
          className="visually-hidden"
          aria-label="CSV file"
          tabIndex={-1}
          onChange={(event) => void attach(event, "csv")}
        />
        <Button
          variant="secondary"
          onClick={() => fileRef.current?.click()}
          isLoading={uploading === "pdf"}
          disabled={isAnswering || isUploading}
        >
          Attach PDF
        </Button>
        <Button
          variant="secondary"
          onClick={() => csvRef.current?.click()}
          isLoading={uploading === "csv"}
          disabled={isAnswering || isUploading}
        >
          Attach CSV
        </Button>
        <label htmlFor="chat-input" className="visually-hidden">
          Message
        </label>
        <textarea
          id="chat-input"
          ref={inputRef}
          className={`composer-input${isTooLong ? " composer-input--invalid" : ""}`}
          rows={2}
          value={text}
          placeholder="Ask about your campus data…"
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          aria-invalid={isTooLong || undefined}
          aria-describedby="chat-input-hint"
          autoFocus
        />
        <Button type="submit" disabled={!canSend}>
          Send
        </Button>
      </div>
      <p
        id="chat-input-hint"
        className={`composer-hint${isTooLong ? " composer-hint--error" : ""}`}
      >
        {isTooLong
          ? `Too long: ${length.toLocaleString("en-IN")} / ${MAX_MESSAGE_CHARS.toLocaleString("en-IN")} characters. Shorten your message.`
          : length >= MESSAGE_LENGTH_WARNING_CHARS
            ? `${length.toLocaleString("en-IN")} / ${MAX_MESSAGE_CHARS.toLocaleString("en-IN")} characters`
            : "Enter to send · Shift+Enter for a new line"}
      </p>
    </form>
  );
}
