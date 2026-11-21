import { useCallback, useEffect, useRef, useState } from "react";

const responseCache = new Map<string, Promise<unknown>>();

export function clearApiCache(): void {
  responseCache.clear();
}

function loadWithCache<T>(key: string, load: () => Promise<T>): Promise<T> {
  const cached = responseCache.get(key);
  if (cached) return cached as Promise<T>;
  const promise = load();
  responseCache.set(key, promise);
  promise.catch(() => responseCache.delete(key));
  return promise;
}

interface Settled<T> {
  key: string;
  version: number;
  data: T | null;
  error: unknown;
}

export interface ApiState<T> {
  data: T | null;
  error: unknown;
  isLoading: boolean;
  reload: () => void;
}

export function useApi<T>(
  key: string | null,
  load: () => Promise<T>,
  options: { cache?: boolean } = {},
): ApiState<T> {
  const useCache = options.cache ?? false;
  const loadRef = useRef(load);
  const [version, setVersion] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);

  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    if (key === null) return;
    let active = true;
    if (useCache && version > 0) responseCache.delete(key);
    const promise = useCache ? loadWithCache(key, () => loadRef.current()) : loadRef.current();
    promise.then(
      (data) => active && setSettled({ key, version, data, error: null }),
      (error: unknown) => active && setSettled({ key, version, data: null, error }),
    );
    return () => {
      active = false;
    };
  }, [key, version, useCache]);

  const reload = useCallback(() => setVersion((current) => current + 1), []);
  const sameKey = settled !== null && settled.key === key;
  const isCurrent = sameKey && settled.version === version;

  return {
    data: sameKey ? settled.data : null,
    error: isCurrent ? settled.error : null,
    isLoading: key !== null && !isCurrent,
    reload,
  };
}
