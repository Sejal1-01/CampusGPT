import { Renderer, type OpenUIError, type ParseResult } from "@openuidev/react-lang";
import { memo, useCallback, useState } from "react";
import { Markdown } from "../components/Markdown";
import { library } from "./library";

interface AnswerRendererProps {
  text: string;
  isStreaming: boolean;
}

function hasBlockingErrors(errors: OpenUIError[]): boolean {
  return errors.some((error) => error.severity !== "warning");
}

export const AnswerRenderer = memo(function AnswerRenderer({
  text,
  isStreaming,
}: AnswerRendererProps) {
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [errors, setErrors] = useState<OpenUIError[]>([]);
  const handleErrors = useCallback((next: OpenUIError[]) => setErrors(next), []);

  const hasRoot = parseResult?.root != null;
  const showRawText = !isStreaming && !hasRoot && text.trim().length > 0;
  const showPartialNote = !isStreaming && hasRoot && hasBlockingErrors(errors);

  return (
    <div className="answer-renderer">
      <Renderer
        library={library}
        response={text}
        isStreaming={isStreaming}
        onParseResult={setParseResult}
        onError={handleErrors}
      />
      {showRawText && <Markdown text={text} />}
      {showPartialNote && <p className="muted small">Part of this answer couldn't be shown.</p>}
    </div>
  );
});
