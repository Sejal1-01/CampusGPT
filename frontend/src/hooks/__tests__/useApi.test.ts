import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useApi } from "../useApi";

describe("useApi", () => {
  it("loads data", async () => {
    const { result } = renderHook(() => useApi("key", () => Promise.resolve(42)));
    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.data).toBe(42));
    expect(result.current.isLoading).toBe(false);
  });

  it("exposes errors", async () => {
    const failure = new Error("boom");
    const { result } = renderHook(() => useApi("key", () => Promise.reject(failure)));
    await waitFor(() => expect(result.current.error).toBe(failure));
    expect(result.current.data).toBeNull();
  });

  it("stays idle with a null key", () => {
    const load = vi.fn(() => Promise.resolve(1));
    const { result } = renderHook(() => useApi(null, load));
    expect(result.current.isLoading).toBe(false);
    expect(load).not.toHaveBeenCalled();
  });

  it("shares one request between cached users of the same key", async () => {
    const load = vi.fn(() => Promise.resolve("value"));
    const first = renderHook(() => useApi("shared", load, { cache: true }));
    const second = renderHook(() => useApi("shared", load, { cache: true }));
    await waitFor(() => expect(first.result.current.data).toBe("value"));
    await waitFor(() => expect(second.result.current.data).toBe("value"));
    expect(load).toHaveBeenCalledOnce();
  });

  it("reloads on demand and keeps the old data meanwhile", async () => {
    let count = 0;
    const { result } = renderHook(() => useApi("count", () => Promise.resolve(++count)));
    await waitFor(() => expect(result.current.data).toBe(1));
    act(() => result.current.reload());
    expect(result.current.data).toBe(1);
    await waitFor(() => expect(result.current.data).toBe(2));
  });
});
