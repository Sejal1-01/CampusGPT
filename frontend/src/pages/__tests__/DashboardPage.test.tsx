import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { loadPins, pinsKey, type PinnedTile } from "../../lib/pinnedTiles";
import { errorResponse, jsonResponse, mockFetch, requestBody } from "../../test/fetchMock";
import { pinnedTile, storedResult } from "../../test/fixtures";
import DashboardPage from "../DashboardPage";

const chartTile = pinnedTile();
const tableTile = pinnedTile({
  id: "t2",
  title: "My marks",
  kind: "table",
  x: "",
  y: [],
  sql: "SELECT subject_name, marks FROM my_marks",
  explanation: "Your marks.",
});

function savePins(tiles: PinnedTile[]) {
  localStorage.setItem(pinsKey("student1"), JSON.stringify(tiles));
}

function rerunRoute() {
  return (init: RequestInit | undefined) => {
    const body = requestBody(init) as { sql: string };
    if (body.sql === tableTile.sql) {
      return jsonResponse(
        storedResult({
          result_id: "r_t2",
          columns: ["subject_name", "marks"],
          rows: [["DBMS", 71]],
          total_rows: 1,
          sql: tableTile.sql,
        }),
      );
    }
    return jsonResponse(storedResult());
  };
}

describe("DashboardPage", () => {
  beforeEach(() => localStorage.clear());

  it("shows an empty state when nothing is pinned", () => {
    const fetchMock = mockFetch({});
    render(<DashboardPage username="student1" />);
    expect(screen.getByText("Nothing pinned yet")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Refresh all" })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("re-runs each pinned query and renders the chart or table", async () => {
    savePins([chartTile, tableTile]);
    const fetchMock = mockFetch({ "POST /api/results/rerun": rerunRoute() });
    render(<DashboardPage username="student1" />);
    expect(screen.getByRole("heading", { name: "Pass % by subject" })).toBeInTheDocument();
    expect(
      await screen.findByTestId("result-chart-bar", {}, { timeout: 3000 }),
    ).toBeInTheDocument();
    const table = await screen.findByRole("table");
    expect(within(table).getByText("71")).toBeInTheDocument();
    expect(fetchMock.mock.calls.map(([, init]) => requestBody(init))).toEqual([
      { sql: chartTile.sql, explanation: chartTile.explanation },
      { sql: tableTile.sql, explanation: tableTile.explanation },
    ]);
  });

  it("shows a rejected query as an error on its tile only", async () => {
    savePins([chartTile, tableTile]);
    mockFetch({
      "POST /api/results/rerun": (init) => {
        const body = requestBody(init) as { sql: string };
        if (body.sql === chartTile.sql) {
          return errorResponse(400, "query_rejected", "You no longer have access to that data.");
        }
        return rerunRoute()(init);
      },
    });
    render(<DashboardPage username="student1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You no longer have access to that data.",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(await screen.findByRole("table")).toBeInTheDocument();
  });

  it("removes a tile and refreshes all tiles", async () => {
    savePins([chartTile, tableTile]);
    const fetchMock = mockFetch({ "POST /api/results/rerun": rerunRoute() });
    render(<DashboardPage username="student1" />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: "Refresh all" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    const tableCard = screen.getByRole("heading", { name: "My marks" }).closest("section");
    await userEvent.click(within(tableCard as HTMLElement).getByRole("button", { name: "Remove" }));
    expect(screen.queryByRole("heading", { name: "My marks" })).not.toBeInTheDocument();
    expect(loadPins("student1").map((tile) => tile.id)).toEqual(["t1"]);
  });
});
