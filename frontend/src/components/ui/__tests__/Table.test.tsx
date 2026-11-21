import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Table } from "..";

function makeRows(count: number): string[][] {
  return Array.from({ length: count }, (_, index) => [`row ${index}`, String(index)]);
}

describe("Table", () => {
  it("renders every row when small", () => {
    render(<Table columns={["Name", "Value"]} rows={makeRows(5)} />);
    expect(screen.getAllByRole("columnheader").map((cell) => cell.textContent)).toEqual([
      "Name",
      "Value",
    ]);
    expect(screen.getByText("row 4")).toBeInTheDocument();
    expect(document.querySelectorAll("tr[data-row-index]")).toHaveLength(5);
  });

  it("highlights the chosen row", () => {
    render(<Table columns={["Name", "Value"]} rows={makeRows(3)} highlightedRow={1} />);
    const rows = document.querySelectorAll("tr[data-row-index]");
    expect(rows[1]).toHaveClass("table-row--highlight");
    expect(rows[0]).not.toHaveClass("table-row--highlight");
  });

  it("virtualises when there are more than 100 rows", () => {
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(440);
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(800);
    render(<Table columns={["Name", "Value"]} rows={makeRows(500)} />);
    const rendered = document.querySelectorAll("tr[data-row-index]");
    expect(rendered.length).toBeGreaterThan(0);
    expect(rendered.length).toBeLessThan(100);
    expect(screen.getByText("row 0")).toBeInTheDocument();
    expect(screen.queryByText("row 499")).not.toBeInTheDocument();
  });
});
