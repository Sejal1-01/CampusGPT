import { useIsStreaming } from "@openuidev/react-lang";
import { useApi } from "../hooks/useApi";

export function useAnswerData<T>(key: string, load: () => Promise<T>) {
  const isStreaming = useIsStreaming();
  return useApi(isStreaming ? null : key, load, { cache: true });
}
