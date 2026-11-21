import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { AccessOverview } from "../../api/types";
import { errorResponse, jsonResponse, mockFetch, requestBody } from "../../test/fetchMock";
import AccessPage from "../AccessPage";

const overview: AccessOverview = {
  roles: [
    {
      name: "hod",
      description: "Head of department",
      grants: [{ domain: "academics", scope: "department" }],
      members: ["hod_cse"],
    },
  ],
  groups: [{ name: "exam_cell", description: "Exam staff", grants: [], members: [] }],
  users: [
    { username: "hod_cse", display_name: "Dr. Sharma", is_platform_admin: false },
    { username: "fac_ece", display_name: "Dr. Rao", is_platform_admin: false },
  ],
  domains: ["academics", "fees"],
  scopes: ["own", "department", "college"],
};

describe("AccessPage", () => {
  it("shows roles with grants and members", async () => {
    mockFetch({ "/api/access/overview": () => jsonResponse(overview) });
    render(<AccessPage />);
    expect(await screen.findByRole("heading", { name: "Hod" })).toBeInTheDocument();
    expect(screen.getByText("academics · department")).toBeInTheDocument();
    expect(screen.getByText("hod_cse")).toBeInTheDocument();
  });

  it("shows the backend's rejection in an error banner", async () => {
    const fetchMock = mockFetch({
      "/api/access/overview": () => jsonResponse(overview),
      "POST /api/access/grants": () =>
        errorResponse(400, "department_wall", "Group grants cannot cross the department wall."),
    });
    render(<AccessPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Groups" }));
    const card = screen.getByRole("heading", { name: "exam_cell" }).closest("section");
    if (!card) throw new Error("Group card not found");
    await userEvent.selectOptions(within(card).getByLabelText("Domain"), "fees");
    await userEvent.selectOptions(within(card).getByLabelText("Scope"), "college");
    await userEvent.click(within(card).getByRole("button", { name: "Add grant" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Group grants cannot cross the department wall.",
    );
    const grantCall = fetchMock.mock.calls.find(([url]) => url === "/api/access/grants");
    expect(requestBody(grantCall?.[1])).toEqual({
      kind: "group",
      target: "exam_cell",
      domain: "fees",
      scope: "college",
    });
  });

  it("creates a group and reloads", async () => {
    let created = false;
    mockFetch({
      "/api/access/overview": () =>
        jsonResponse(
          created
            ? {
                ...overview,
                groups: [
                  ...overview.groups,
                  { name: "tpo", description: "", grants: [], members: [] },
                ],
              }
            : overview,
        ),
      "POST /api/access/groups": () => {
        created = true;
        return jsonResponse({ ok: true });
      },
    });
    render(<AccessPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Groups" }));
    await userEvent.type(screen.getByLabelText("Name"), "tpo");
    await userEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(await screen.findByRole("heading", { name: "tpo" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Created group tpo.");
  });

  it("shows a user's effective access with sources", async () => {
    mockFetch({
      "/api/access/overview": () => jsonResponse(overview),
      "/api/access/users/hod_cse/effective": () =>
        jsonResponse({
          username: "hod_cse",
          roles: ["hod"],
          grants: [
            { domain: "academics", scope: "department", source: "role", name: "hod" },
            { domain: "fees", scope: "own", source: "group", name: "exam_cell" },
          ],
          views: ["department_marks", "my_fees"],
        }),
    });
    render(<AccessPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Users" }));
    const [firstViewButton] = screen.getAllByRole("button", { name: "View access" });
    if (!firstViewButton) throw new Error("No users listed");
    await userEvent.click(firstViewButton);
    expect(await screen.findByRole("heading", { name: "Access: hod_cse" })).toBeInTheDocument();
    expect(screen.getByText("exam_cell")).toBeInTheDocument();
    expect(screen.getByText("department_marks, my_fees")).toBeInTheDocument();
  });

  it("lists the audit log", async () => {
    mockFetch({
      "/api/access/overview": () => jsonResponse(overview),
      "/api/access/audit": () =>
        jsonResponse([
          {
            id: 1,
            changed_by: "admin",
            action: "grant_add",
            target: "group:exam_cell",
            details: "fees/own",
            changed_at: "2026-11-12 10:00",
          },
        ]),
    });
    render(<AccessPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Audit log" }));
    expect(await screen.findByText("grant_add")).toBeInTheDocument();
  });

  it("shows a load error with retry", async () => {
    mockFetch({
      "/api/access/overview": () =>
        errorResponse(403, "forbidden", "Only the platform admin can manage access."),
    });
    render(<AccessPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Only the platform admin can manage access.",
    );
  });
});
