import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { api } from "../../api/client";
import { errorResponse, jsonResponse, mockFetch } from "../../test/fetchMock";
import { testUser } from "../../test/fixtures";
import { AuthProvider } from "../AuthProvider";
import { useAuth } from "../useAuth";

const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>;

describe("useAuth", () => {
  it("restores the session from /me", async () => {
    mockFetch({ "/api/auth/me": () => jsonResponse(testUser) });
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("authenticated"));
    expect(result.current.user?.username).toBe("student1");
  });

  it("logs in and out", async () => {
    mockFetch({
      "/api/auth/me": () => errorResponse(401, "unauthorized", "Log in."),
      "POST /api/auth/login": () => jsonResponse(testUser),
      "POST /api/auth/logout": () => jsonResponse({ ok: true }),
    });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.status).toBe("anonymous"));
    await act(() => result.current.login("student1", "demo123"));
    expect(result.current.user?.display_name).toBe("Aarav Kumar");
    await act(() => result.current.logout());
    expect(result.current.user).toBeNull();
  });

  it("signs out locally when any request gets a 401", async () => {
    let expired = false;
    mockFetch({
      "/api/auth/me": () => jsonResponse(testUser),
      "/api/health": () =>
        expired ? errorResponse(401, "unauthorized", "Expired.") : jsonResponse({}),
    });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.status).toBe("authenticated"));
    expired = true;
    await act(() => api.health().catch(() => undefined));
    expect(result.current.status).toBe("anonymous");
  });

  it("throws outside the provider", () => {
    expect(() => renderHook(() => useAuth())).toThrow(/AuthProvider/);
  });
});
