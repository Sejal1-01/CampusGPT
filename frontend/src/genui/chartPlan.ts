import type { StoredResult } from "../api/types";
import { EMPTY_CELL } from "../config";

export const X_KEY = "__x";

export type ChartKind = "bar" | "grouped_bar" | "line" | "pie";
export type ChartPoint = Record<string, string | number | null>;

export type ChartPlan =
  { mode: "empty" } | { mode: "table" } | { mode: "chart"; points: ChartPoint[]; series: string[] };

const NOT_NUMERIC = Symbol("not numeric");

function toNumber(value: unknown): number | null | typeof NOT_NUMERIC {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : NOT_NUMERIC;
  if (typeof value === "string") {
    const parsed = Number(value.trim());
    return Number.isFinite(parsed) ? parsed : NOT_NUMERIC;
  }
  return NOT_NUMERIC;
}

function xLabel(value: unknown): string {
  if (value === null || value === undefined || value === "") return EMPTY_CELL;
  return String(value);
}

function buildPoints(result: StoredResult, xIndex: number, series: string[]): ChartPoint[] | null {
  const seriesIndexes = series.map((name) => result.columns.indexOf(name));
  const points: ChartPoint[] = [];
  for (const row of result.rows) {
    const point: ChartPoint = { [X_KEY]: xLabel(row[xIndex]) };
    for (const [position, name] of series.entries()) {
      const number = toNumber(row[seriesIndexes[position] ?? -1]);
      if (number === NOT_NUMERIC) return null;
      point[name] = number;
    }
    points.push(point);
  }
  const hasNumbers = series.every((name) => points.some((point) => point[name] !== null));
  return hasNumbers ? points : null;
}

export function planChart(
  result: StoredResult,
  kind: ChartKind,
  x: string,
  y: string[],
): ChartPlan {
  if (result.rows.length === 0) return { mode: "empty" };
  const xIndex = result.columns.indexOf(x);
  const series = kind === "pie" ? y.slice(0, 1) : y;
  const columnsExist =
    xIndex >= 0 && series.length > 0 && series.every((name) => result.columns.includes(name));
  if (!columnsExist) return { mode: "table" };
  const points = buildPoints(result, xIndex, series);
  return points ? { mode: "chart", points, series } : { mode: "table" };
}
