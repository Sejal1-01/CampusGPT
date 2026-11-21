import { EMPTY_CELL } from "../config";

const MAX_FRACTION_DIGITS = 2;

export function formatNumber(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return value.toLocaleString("en-IN", { maximumFractionDigits: MAX_FRACTION_DIGITS });
}

export function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") return EMPTY_CELL;
  if (typeof value === "number") return formatNumber(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function formatRole(role: string): string {
  return role
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function toIsoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export function formatDay(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
}
