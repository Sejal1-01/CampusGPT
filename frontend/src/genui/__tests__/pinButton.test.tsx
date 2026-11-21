import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Me } from "../../api/types";
import { AuthContext } from "../../hooks/useAuth";
import { loadPins } from "../../lib/pinnedTiles";
import { jsonResponse, mockFetch } from "../../test/fetchMock";
import { adminUser, storedResult, testUser } from "../../test/fixtures";
import { AnswerRenderer } from "../AnswerRenderer";

const CHART_PROGRAM =
  'root = Answer([c])\nc = DataChart("r_ab12cd34", "bar", "subject_name", ["pass_percent"], "Pass % by subject")';
const TABLE_PROGRAM = 'root = Answer([d])\nd = DataTable("r_ab12cd34")';

function renderAsUser(program: string, user: Me | null = testUser) {
  mockFetch({ "/api/results/r_ab12cd34": () => jsonResponse(storedResult()) });
  return render(
    <AuthContext.Provider
      value={{ status: "authenticated", user, login: vi.fn(), logout: vi.fn() }}
    >
      <AnswerRenderer text={program} isStreaming={false} />
    </AuthContext.Provider>,
  );
}

describe("Pin", () => {
  beforeEach(() => localStorage.clear());

  it("pins and unpins a chart with its query", async () => {
    renderAsUser(CHART_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Pin" }));
    expect(loadPins("student1")).toEqual([
      expect.objectContaining({
        title: "Pass % by subject",
        kind: "bar",
        x: "subject_name",
        y: ["pass_percent"],
        sql: "SELECT subject_name, pass_percent FROM subject_results",
        explanation: "Pass percentage per subject this semester.",
      }),
    ]);
    const unpin = screen.getByRole("button", { name: "Unpin" });
    expect(unpin).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(unpin);
    expect(loadPins("student1")).toEqual([]);
    expect(screen.getByRole("button", { name: "Pin" })).toBeInTheDocument();
  });

  it("pins a table using the explanation as its title", async () => {
    renderAsUser(TABLE_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Pin" }));
    expect(loadPins("student1")[0]).toMatchObject({
      kind: "table",
      title: "Pass percentage per subject this semester.",
    });
  });

  it("shows Unpin for an answer that is already pinned", async () => {
    const first = renderAsUser(CHART_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Pin" }));
    first.unmount();
    renderAsUser(CHART_PROGRAM);
    expect(await screen.findByRole("button", { name: "Unpin" })).toBeInTheDocument();
  });

  it("says so when the browser blocks storage", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Blocked", "SecurityError");
    });
    renderAsUser(CHART_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Pin" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Can't save pins in this browser.");
    expect(screen.getByRole("button", { name: "Pin" })).toBeInTheDocument();
  });

  it("is hidden without a signed-in user or for the platform admin", async () => {
    const view = renderAsUser(CHART_PROGRAM, null);
    await screen.findByText("How I got this");
    expect(screen.queryByRole("button", { name: "Pin" })).not.toBeInTheDocument();
    view.unmount();
    renderAsUser(CHART_PROGRAM, adminUser);
    await screen.findByText("How I got this");
    expect(screen.queryByRole("button", { name: "Pin" })).not.toBeInTheDocument();
  });
});
