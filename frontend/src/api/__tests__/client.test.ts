import { describe, expect, it, vi } from "vitest";
import { errorResponse, jsonResponse, mockFetch } from "../../test/fetchMock";
import { ApiError, api, NETWORK_ERROR_CODE, setUnauthorizedHandler } from "../client";

describe("api client", () => {
  it("sends same-origin credentials and JSON", async () => {
    const fetchMock = mockFetch({ "POST /api/auth/login": () => jsonResponse({ username: "a" }) });
    await api.login({ username: "a", password: "b" });
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.credentials).toBe("same-origin");
    expect(init?.body).toBe(JSON.stringify({ username: "a", password: "b" }));
  });

  it("turns the error shape into an ApiError", async () => {
    mockFetch({ "/api/results/r_1": () => errorResponse(404, "not_found", "Result not found.") });
    await expect(api.result("r_1")).rejects.toMatchObject({
      code: "not_found",
      message: "Result not found.",
      status: 404,
    });
  });

  it("calls the unauthorized handler on 401", async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    mockFetch({ "/api/auth/me": () => errorResponse(401, "unauthorized", "Log in again.") });
    await expect(api.me()).rejects.toBeInstanceOf(ApiError);
    expect(handler).toHaveBeenCalledOnce();
  });

  it("handles responses that are not the error shape", async () => {
    mockFetch({ "/api/health": () => new Response("oops", { status: 500 }) });
    await expect(api.health()).rejects.toMatchObject({ code: "http_error", status: 500 });
  });

  it("reports network failures plainly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(api.me()).rejects.toMatchObject({ code: NETWORK_ERROR_CODE });
  });

  it("encodes path segments", async () => {
    const fetchMock = mockFetch({ "/api/quiz/a%2Fb": () => jsonResponse({}) });
    await api.quiz("a/b");
    expect(fetchMock).toHaveBeenCalledWith("/api/quiz/a%2Fb", expect.anything());
  });
});
