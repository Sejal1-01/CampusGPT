import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { App } from "../../App";
import { AuthProvider } from "../../hooks/AuthProvider";
import {
  errorResponse,
  jsonResponse,
  mockFetch,
  requestBody,
  sseResponse,
} from "../../test/fetchMock";
import { adminUser, testUser } from "../../test/fixtures";

const demoAccounts = [
  { username: "student1", role: "student", note: "CSE, 3rd semester" },
  { username: "admin", role: "platform_admin", note: "Access only" },
];

function renderApp() {
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>,
  );
}

describe("login flow", () => {
  it("fills a demo account, logs in and shows starter questions", async () => {
    const fetchMock = mockFetch({
      "/api/auth/me": () => errorResponse(401, "unauthorized", "Log in."),
      "/api/auth/demo-accounts": () => jsonResponse(demoAccounts),
      "POST /api/auth/login": () => jsonResponse(testUser),
    });
    renderApp();
    expect(
      await screen.findByText("Indian Institute of Information Technology Bhagalpur"),
    ).toBeInTheDocument();
    expect(screen.getByText("चारित्र्यं मम जीवनम्")).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: /student1/ }));
    expect(screen.getByLabelText("Username")).toHaveValue("student1");
    expect(screen.getByLabelText("Password")).toHaveValue("demo123");
    await userEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("IIIT Bhagalpur · CampusGPT")).toBeInTheDocument();
    expect(screen.getByText("Aarav Kumar")).toBeInTheDocument();
    expect(screen.getByText("Student")).toHaveClass("role-badge");
    expect(screen.getByRole("button", { name: "What is my attendance?" })).toBeInTheDocument();
    const loginCall = fetchMock.mock.calls.find(([url]) => url === "/api/auth/login");
    expect(requestBody(loginCall?.[1])).toEqual({ username: "student1", password: "demo123" });
  });

  it("shows the server message for a wrong password", async () => {
    mockFetch({
      "/api/auth/me": () => errorResponse(401, "unauthorized", "Log in."),
      "/api/auth/demo-accounts": () => jsonResponse([]),
      "POST /api/auth/login": () =>
        errorResponse(401, "invalid_login", "Wrong username or password."),
    });
    renderApp();
    await userEvent.type(await screen.findByLabelText("Username"), "student1");
    await userEvent.type(screen.getByLabelText("Password"), "nope");
    await userEvent.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Wrong username or password.");
  });

  it("asks a starter question and renders the streamed answer", async () => {
    mockFetch({
      "/api/auth/me": () => jsonResponse(testUser),
      "POST /api/chat": () =>
        sseResponse([
          { type: "text", delta: "root = Answer([t])\n" },
          { type: "text", delta: 't = TextBlock("Your attendance is 82%.")' },
          { type: "done", latency_ms: 10 },
        ]),
    });
    renderApp();
    await userEvent.click(await screen.findByRole("button", { name: "What is my attendance?" }));
    expect(await screen.findByText("Your attendance is 82%.")).toBeInTheDocument();
    expect(screen.getByText("What is my attendance?")).toHaveTextContent("What is my attendance?");
  });

  it("returns to login when the session expires", async () => {
    mockFetch({
      "/api/auth/me": () => jsonResponse(testUser),
      "/api/auth/demo-accounts": () => jsonResponse([]),
      "POST /api/chat": () => errorResponse(401, "unauthorized", "Session expired."),
    });
    renderApp();
    await userEvent.type(await screen.findByLabelText("Message"), "hi{Enter}");
    expect(await screen.findByRole("button", { name: "Log in" })).toBeInTheDocument();
  });

  it("logs out", async () => {
    mockFetch({
      "/api/auth/me": () => jsonResponse(testUser),
      "/api/auth/demo-accounts": () => jsonResponse([]),
      "POST /api/auth/logout": () => jsonResponse({ ok: true }),
    });
    renderApp();
    await userEvent.click(await screen.findByRole("button", { name: "Logout" }));
    expect(await screen.findByRole("button", { name: "Log in" })).toBeInTheDocument();
  });

  it("shows only the Access page to the platform admin", async () => {
    mockFetch({
      "/api/auth/me": () => jsonResponse(adminUser),
      "/api/access/overview": () =>
        jsonResponse({ roles: [], groups: [], users: [], domains: [], scopes: [] }),
    });
    renderApp();
    expect(await screen.findByRole("heading", { name: "Access" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "New chat" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Dashboard" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Message")).not.toBeInTheDocument();
    expect(screen.getByText("Platform Admin", { selector: ".role-badge" })).toBeInTheDocument();
  });

  it("hides the Access page from other users", async () => {
    mockFetch({ "/api/auth/me": () => jsonResponse(testUser) });
    renderApp();
    await screen.findByLabelText("Message");
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Access" })).not.toBeInTheDocument(),
    );
  });

  it("opens the dashboard from the header and returns to the chat", async () => {
    localStorage.clear();
    mockFetch({ "/api/auth/me": () => jsonResponse(testUser) });
    renderApp();
    await userEvent.click(await screen.findByRole("button", { name: "Dashboard" }));
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Nothing pinned yet")).toBeInTheDocument();
    expect(screen.queryByLabelText("Message")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Chat" }));
    expect(await screen.findByLabelText("Message")).toBeInTheDocument();
  });
});
