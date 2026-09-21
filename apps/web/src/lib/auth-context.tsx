"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  api,
  type TokenPair,
  type User,
  type UserRole,
} from "@/lib/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  register: (input: {
    email: string;
    password: string;
    full_name: string;
    role?: UserRole;
  }) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

function storeTokens({ access_token, refresh_token }: TokenPair) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadSession = useCallback(async () => {
    const access = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.me(access));
    } catch {
      // Access token expired — try the refresh token once before signing out.
      if (refresh) {
        try {
          const tokens = await api.refresh(refresh);
          storeTokens(tokens);
          setUser(await api.me(tokens.access_token));
        } catch {
          clearTokens();
          setUser(null);
        }
      } else {
        clearTokens();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      register: async (input) => {
        storeTokens(await api.register(input));
        await loadSession();
      },
      login: async (email, password) => {
        storeTokens(await api.login({ email, password }));
        await loadSession();
      },
      logout: async () => {
        const access = localStorage.getItem(ACCESS_TOKEN_KEY);
        if (access) await api.logout(access).catch(() => undefined);
        clearTokens();
        setUser(null);
      },
      hasRole: (...roles) => (user ? roles.includes(user.role) : false),
    }),
    [user, loading, loadSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
