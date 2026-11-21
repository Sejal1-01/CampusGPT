import type { ReactNode } from "react";
import { isSafeUrl } from "../../lib/url";

export function SourceLinkView({ title, url }: { title: string; url: string }) {
  if (!isSafeUrl(url)) return <li className="source-link">{title}</li>;
  return (
    <li className="source-link">
      <a href={url} target="_blank" rel="noopener noreferrer">
        {title}
      </a>
      <span className="source-host">{new URL(url).hostname}</span>
    </li>
  );
}

export function SourcesView({ children }: { children: ReactNode }) {
  return (
    <div className="sources">
      <h4 className="sources-title">Sources</h4>
      <ol className="sources-list">{children}</ol>
    </div>
  );
}
