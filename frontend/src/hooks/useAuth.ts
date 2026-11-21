import { createContext, useContext } from "react";
import type { Me } from "../api/types";

export type AuthStatus = "loading" | "anonymous" | "authenticated";

export interface AuthContextValue {
  status: AuthStatus;
  user: Me | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function useCurrentUser(): Me | null {
  return useContext(AuthContext)?.user ?? null;
}
