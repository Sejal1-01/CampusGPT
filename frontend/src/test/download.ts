import { vi } from "vitest";

export function captureDownloads() {
  const createObjectURL = vi.fn<(blob: Blob | MediaSource) => string>(() => "blob:download");
  URL.createObjectURL = createObjectURL;
  URL.revokeObjectURL = vi.fn();
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  return {
    click,
    lastFileName: () => (click.mock.contexts.at(-1) as HTMLAnchorElement | undefined)?.download,
    lastText: async () => {
      const blob = createObjectURL.mock.calls.at(-1)?.[0];
      return blob instanceof Blob ? blob.text() : "";
    },
  };
}
