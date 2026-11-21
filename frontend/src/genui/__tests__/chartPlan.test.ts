import { describe, expect, it } from "vitest";
import { storedResult } from "../../test/fixtures";
import { planChart, X_KEY } from "../chartPlan";

describe("planChart", () => {
  it("builds points for numeric columns, accepting numeric strings", () => {
    const result = storedResult({
      rows: [
        ["DBMS", "41.3"],
        [null, 78],
      ],
    });
    expect(planChart(result, "bar", "subject_name", ["pass_percent"])).toEqual({
      mode: "chart",
      series: ["pass_percent"],
      points: [
        { [X_KEY]: "DBMS", pass_percent: 41.3 },
        { [X_KEY]: "—", pass_percent: 78 },
      ],
    });
  });

  it("keeps NULL values as gaps", () => {
    const plan = planChart(
      storedResult({
        rows: [
          ["A", null],
          ["B", 3],
        ],
      }),
      "line",
      "subject_name",
      ["pass_percent"],
    );
    expect(plan.mode).toBe("chart");
  });

  it("is empty for zero rows", () => {
    expect(planChart(storedResult({ rows: [] }), "bar", "subject_name", ["pass_percent"])).toEqual({
      mode: "empty",
    });
  });

  it("falls back to a table for text, all-NULL or missing columns", () => {
    expect(
      planChart(storedResult({ rows: [["A", "high"]] }), "bar", "subject_name", ["pass_percent"])
        .mode,
    ).toBe("table");
    expect(
      planChart(storedResult({ rows: [["A", null]] }), "bar", "subject_name", ["pass_percent"])
        .mode,
    ).toBe("table");
    expect(planChart(storedResult(), "bar", "missing", ["pass_percent"]).mode).toBe("table");
    expect(planChart(storedResult(), "bar", "subject_name", []).mode).toBe("table");
  });

  it("uses only the first y column for pie charts", () => {
    const result = storedResult({ columns: ["name", "a", "b"], rows: [["x", 1, 2]] });
    const plan = planChart(result, "pie", "name", ["a", "b"]);
    expect(plan.mode === "chart" && plan.series).toEqual(["a"]);
  });

  it("supports several series for grouped bars", () => {
    const result = storedResult({ columns: ["name", "a", "b"], rows: [["x", 1, 2]] });
    const plan = planChart(result, "grouped_bar", "name", ["a", "b"]);
    expect(plan.mode === "chart" && plan.series).toEqual(["a", "b"]);
  });
});
