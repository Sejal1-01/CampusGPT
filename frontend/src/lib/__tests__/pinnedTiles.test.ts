import { beforeEach, describe, expect, it, vi } from "vitest";
import { pinnedTile } from "../../test/fixtures";
import { findPin, loadPins, pinTile, pinsKey, unpinTile, type TileSpec } from "../pinnedTiles";

const spec: TileSpec = {
  title: "Pass % by subject",
  kind: "bar",
  x: "subject_name",
  y: ["pass_percent"],
  sql: "SELECT subject_name, pass_percent FROM subject_results",
  explanation: "Pass percentage per subject.",
};

function throwQuota(): never {
  throw new DOMException("Storage is full.", "QuotaExceededError");
}

describe("pinned tiles", () => {
  beforeEach(() => localStorage.clear());

  it("pins a tile under a key that includes the username", () => {
    const tile = pinTile("student1", spec);
    expect(tile).toMatchObject(spec);
    expect(tile?.id).toBeTruthy();
    expect(Number.isNaN(Date.parse(tile?.pinnedAt ?? ""))).toBe(false);
    expect(pinsKey("student1")).toContain("student1");
    expect(loadPins("student1")).toEqual([tile]);
    expect(loadPins("faculty1")).toEqual([]);
  });

  it("does not pin the same query twice", () => {
    const first = pinTile("student1", spec);
    const second = pinTile("student1", { ...spec, title: "Renamed" });
    expect(second?.id).toBe(first?.id);
    expect(loadPins("student1")).toHaveLength(1);
    expect(findPin("student1", { ...spec, kind: "line" })).toBeNull();
  });

  it("unpins by id", () => {
    const tile = pinTile("student1", spec);
    pinTile("student1", { ...spec, kind: "table", x: "", y: [] });
    expect(unpinTile("student1", tile?.id ?? "")).toBe(true);
    expect(loadPins("student1").map((item) => item.kind)).toEqual(["table"]);
  });

  it("ignores corrupt or malformed stored data", () => {
    localStorage.setItem(pinsKey("student1"), "{not json");
    expect(loadPins("student1")).toEqual([]);
    localStorage.setItem(
      pinsKey("student1"),
      JSON.stringify([pinnedTile(), { id: "t2", kind: "scatter" }, null]),
    );
    expect(loadPins("student1")).toEqual([pinnedTile()]);
  });

  it("returns nothing when reading storage throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(throwQuota);
    expect(loadPins("student1")).toEqual([]);
    expect(findPin("student1", spec)).toBeNull();
  });

  it("reports failure when writing storage throws", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(throwQuota);
    expect(pinTile("student1", spec)).toBeNull();
    expect(unpinTile("student1", "t1")).toBe(false);
  });
});
