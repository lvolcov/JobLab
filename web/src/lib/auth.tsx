// joblab — auth context
// Wraps GET /auth/me to derive session state on mount and after login/logout.

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, api, type Me } from "./api";

interface AuthState {
  me: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const next = await api.get<Me>("/auth/me");
      setMe(next);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setMe(null);
      } else {
        throw err;
      }
    }
  };

  useEffect(() => {
    void (async () => {
      await refresh().catch(() => setMe(null));
      setLoading(false);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const next = await api.post<Me>("/auth/login", { email, password });
    setMe(next);
  };

  const logout = async () => {
    await api.post("/auth/logout").catch(() => undefined);
    setMe(null);
  };

  return (
    <AuthContext.Provider value={{ me, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
