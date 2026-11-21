import { useIsStreaming } from "@openuidev/react-lang";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";

export function useStoredResult(resultId: string) {
  const isStreaming = useIsStreaming();
  const key = isStreaming || !resultId ? null : `result:${resultId}`;
  const state = useApi(key, () => api.result(resultId), { cache: true });
  return { ...state, isLoading: state.isLoading || isStreaming };
}
