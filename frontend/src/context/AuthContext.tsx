import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

const TOKEN_KEY = "mubeen_access_token";

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  storeToken: (token: string) => void;
  clearToken: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY),
  );

  function storeToken(t: string) {
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: token !== null, storeToken, clearToken }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
