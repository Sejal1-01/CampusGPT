import type { ChartKind } from "../genui/chartPlan";

export type TileKind = "table" | ChartKind;

export interface PinnedTile {
  id: string;
  title: string;
  kind: TileKind;
  x: string;
  y: string[];
  sql: string;
  explanation: string;
  pinnedAt: string;
}

export type TileSpec = Omit<PinnedTile, "id" | "pinnedAt">;

const TILE_KINDS: readonly string[] = ["table", "bar", "grouped_bar", "line", "pie"];

export function pinsKey(username: string): string {
  return `campusgpt:pins:${username}`;
}

function isPinnedTile(value: unknown): value is PinnedTile {
  if (typeof value !== "object" || value === null) return false;
  const tile = value as Record<string, unknown>;
  return (
    typeof tile.id === "string" &&
    typeof tile.title === "string" &&
    typeof tile.kind === "string" &&
    TILE_KINDS.includes(tile.kind) &&
    typeof tile.x === "string" &&
    Array.isArray(tile.y) &&
    tile.y.every((column) => typeof column === "string") &&
    typeof tile.sql === "string" &&
    typeof tile.explanation === "string" &&
    typeof tile.pinnedAt === "string"
  );
}

export function loadPins(username: string): PinnedTile[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(pinsKey(username)) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter(isPinnedTile) : [];
  } catch {
    return [];
  }
}

function savePins(username: string, pins: PinnedTile[]): boolean {
  try {
    localStorage.setItem(pinsKey(username), JSON.stringify(pins));
    return true;
  } catch {
    return false;
  }
}

function sameQuery(tile: TileSpec, spec: TileSpec): boolean {
  return (
    tile.sql === spec.sql &&
    tile.kind === spec.kind &&
    tile.x === spec.x &&
    JSON.stringify(tile.y) === JSON.stringify(spec.y)
  );
}

export function findPin(username: string, spec: TileSpec): PinnedTile | null {
  return loadPins(username).find((tile) => sameQuery(tile, spec)) ?? null;
}

function newTileId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function pinTile(username: string, spec: TileSpec): PinnedTile | null {
  const existing = findPin(username, spec);
  if (existing) return existing;
  const tile: PinnedTile = { ...spec, id: newTileId(), pinnedAt: new Date().toISOString() };
  return savePins(username, [...loadPins(username), tile]) ? tile : null;
}

export function unpinTile(username: string, tileId: string): boolean {
  return savePins(
    username,
    loadPins(username).filter((tile) => tile.id !== tileId),
  );
}
