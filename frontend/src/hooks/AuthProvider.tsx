import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setUnauthorizedHandler } from "../api/client";
import type { Me } from "../api/types";
import { clearApiCache } from "./useApi";
import { AuthContext, type AuthContextValue, type AuthStatus } from "./useAuth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const signOutLocally = useCallback(() => {
    clearApiCache();
    setUser(null);
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(signOutLocally);
    let active = true;
    api.me().then(
      (me) => {
        if (!active) return;
        setUser(me);
        setStatus("authenticated");
      },
      () => active && setStatus("anonymous"),
    );
    return () => {
      active = false;
      setUnauthorizedHandler(null);
    };
  }, [signOutLocally]);

  const login = useCallback(async (username: string, password: string) => {
    const me = await api.login({ username, password });
    setUser(me);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      signOutLocally();
    }
  }, [signOutLocally]);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, login, logout }),
    [status, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
