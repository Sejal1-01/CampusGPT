import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { errorResponse, jsonResponse, mockFetch } from "../../test/fetchMock";
import { storedResult } from "../../test/fixtures";
import { AnswerRenderer } from "../AnswerRenderer";

function renderAnswer(program: string, isStreaming = false) {
  return render(<AnswerRenderer text={program} isStreaming={isStreaming} />);
}

const CHART_PROGRAM = [
  "root = Answer([t, c, i])",
  't = TextBlock("Pass percentage by subject")',
  'c = DataChart("r_ab12cd34", "bar", "subject_name", ["pass_percent"], "Pass % by subject")',
  'i = Insight("DBMS has the lowest pass rate at 41.3%.")',
].join("\n");

describe("DataChart", () => {
  it("renders the brief's example program as text, chart and insight", async () => {
    mockFetch({ "/api/results/r_ab12cd34": () => jsonResponse(storedResult()) });
    renderAnswer(CHART_PROGRAM);
    expect(screen.getByText("Pass percentage by subject")).toBeInTheDocument();
    expect(screen.getByText("DBMS has the lowest pass rate at 41.3%.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pass % by subject" })).toBeInTheDocument();
    await screen.findByText("How I got this");
    expect(
      await screen.findByTestId("result-chart-bar", {}, { timeout: 3000 }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("SELECT subject_name, pass_percent FROM subject_results"),
    ).toBeInTheDocument();
    expect(screen.getByText("Pass percentage per subject this semester.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download CSV" })).toHaveAttribute(
      "href",
      "/api/results/r_ab12cd34/csv",
    );
  });

  it("does not fetch while the answer is still streaming", () => {
    const fetchMock = mockFetch({});
    renderAnswer(CHART_PROGRAM, true);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows an empty state for zero rows", async () => {
    mockFetch({
      "/api/results/r_ab12cd34": () => jsonResponse(storedResult({ rows: [], total_rows: 0 })),
    });
    renderAnswer(CHART_PROGRAM);
    expect(await screen.findByText("No matching records")).toBeInTheDocument();
    expect(screen.queryByTestId("result-chart-bar")).not.toBeInTheDocument();
  });

  it("falls back to a table when y is not numeric, showing NULL as a dash", async () => {
    mockFetch({
      "/api/results/r_ab12cd34": () =>
        jsonResponse(
          storedResult({
            rows: [
              ["DBMS", "high"],
              ["OS", null],
            ],
          }),
        ),
    });
    renderAnswer(CHART_PROGRAM);
    const table = await screen.findByRole("table");
    expect(within(table).getByText("high")).toBeInTheDocument();
    expect(within(table).getByText("—")).toBeInTheDocument();
  });

  it("falls back to a table when the columns do not exist", async () => {
    mockFetch({
      "/api/results/r_ab12cd34": () => jsonResponse(storedResult({ columns: ["name", "value"] })),
    });
    renderAnswer(CHART_PROGRAM);
    expect(await screen.findByRole("table")).toBeInTheDocument();
  });

  it("shows a retryable error when the result is missing", async () => {
    mockFetch({
      "/api/results/r_ab12cd34": () => errorResponse(404, "not_found", "Result expired."),
    });
    renderAnswer(CHART_PROGRAM);
    expect(await screen.findByRole("alert")).toHaveTextContent("Result expired.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});

describe("DataTable", () => {
  it("renders rows, NULLs and the truncation note", async () => {
    mockFetch({
      "/api/results/r_t1": () =>
        jsonResponse(
          storedResult({
            result_id: "r_t1",
            rows: [
              ["DBMS", null],
              ["OS", 78.5],
            ],
            total_rows: 812,
            truncated: true,
          }),
        ),
    });
    renderAnswer('root = Answer([d])\nd = DataTable("r_t1", "Results")');
    const table = await screen.findByRole("table");
    expect(within(table).getByText("—")).toBeInTheDocument();
    expect(within(table).getByText("78.5")).toBeInTheDocument();
    expect(screen.getByText("Showing 2 of 812 rows")).toBeInTheDocument();
    expect(screen.getByText("How I got this")).toBeInTheDocument();
  });

  it("shows the empty state for zero rows", async () => {
    mockFetch({
      "/api/results/r_t1": () =>
        jsonResponse(storedResult({ result_id: "r_t1", rows: [], total_rows: 0 })),
    });
    renderAnswer('root = Answer([d])\nd = DataTable("r_t1")');
    expect(await screen.findByText("No matching records")).toBeInTheDocument();
  });

  it("fetches a result once when two components share it", async () => {
    const fetchMock = mockFetch({ "/api/results/r_ab12cd34": () => jsonResponse(storedResult()) });
    renderAnswer(
      `${CHART_PROGRAM.replace("[t, c, i]", "[t, c, i, d]")}\nd = DataTable("r_ab12cd34")`,
    );
    await screen.findByRole("table");
    await screen.findAllByText("How I got this");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("StatCards", () => {
  it("renders each card", () => {
    renderAnswer(
      'root = Answer([s])\ns = StatCards([a, b])\na = StatCard("Attendance", "68%", "below 75%")\nb = StatCard("Classes", "34")',
    );
    expect(screen.getByText("Attendance")).toBeInTheDocument();
    expect(screen.getByText("68%")).toBeInTheDocument();
    expect(screen.getByText("below 75%")).toBeInTheDocument();
    expect(screen.getByText("34")).toBeInTheDocument();
  });
});
