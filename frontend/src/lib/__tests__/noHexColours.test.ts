import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

const SOURCE_ROOT = join(import.meta.dirname, "..", "..");
const ALLOWED_FILE = "theme.css";
const HEX_COLOUR = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b/g;
const CHECKED_EXTENSIONS = /\.(tsx?|css)$/;

function listFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) return listFiles(path);
    return CHECKED_EXTENSIONS.test(name) ? [path] : [];
  });
}

describe("theme colours", () => {
  it("only theme.css contains hex colour literals", () => {
    const offenders = listFiles(SOURCE_ROOT)
      .filter((path) => relative(SOURCE_ROOT, path) !== ALLOWED_FILE)
      .flatMap((path) =>
        (readFileSync(path, "utf8").match(HEX_COLOUR) ?? []).map(
          (match) => `${relative(SOURCE_ROOT, path)}: ${match}`,
        ),
      );
    expect(offenders).toEqual([]);
  });

  it("theme.css defines every required token", () => {
    const theme = readFileSync(join(SOURCE_ROOT, ALLOWED_FILE), "utf8");
    const tokens = [
      "--color-primary",
      "--color-primary-hover",
      "--color-accent",
      "--color-danger",
      "--color-bg",
      "--color-surface",
      "--color-border",
      "--color-text",
      "--color-text-muted",
      "--chart-series-1",
      "--chart-series-5",
    ];
    for (const token of tokens) expect(theme).toContain(`${token}:`);
  });
});
