import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api } from "../api/client";
import { API_AUTH_REQUIRED } from "../api/runtime";
import { clearStoredSession, getStoredSession } from "../api/session";
import type { MagicLinkStartResponse, UserProfile } from "../api/types";

interface AuthContextValue {
  authRequired: boolean;
  loading: boolean;
  user: UserProfile | null;
  requestedEmail: string;
  lastMagicLink: string;
  requestMagicLink: (email: string) => Promise<MagicLinkStartResponse>;
  completeMagicLink: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(API_AUTH_REQUIRED);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [requestedEmail, setRequestedEmail] = useState("");
  const [lastMagicLink, setLastMagicLink] = useState("");

  const refreshUser = useCallback(async () => {
    if (!API_AUTH_REQUIRED) {
      setUser(null);
      setLoading(false);
      return;
    }

    const session = getStoredSession();
    if (!session?.token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await api.me();
      setUser(response.user);
    } catch {
      clearStoredSession();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const value = useMemo<AuthContextValue>(
    () => ({
      authRequired: API_AUTH_REQUIRED,
      loading,
      user,
      requestedEmail,
      lastMagicLink,
      requestMagicLink: async (email: string) => {
        const response = await api.startMagicLink(email);
        setRequestedEmail(email);
        setLastMagicLink(response.dev_magic_link_token ?? "");
        return response;
      },
      completeMagicLink: async (token: string) => {
        setLoading(true);
        try {
          const response = await api.exchangeMagicLink(token);
          setUser(response.user);
        } finally {
          setLoading(false);
        }
      },
      logout: async () => {
        await api.logout();
        setUser(null);
        setRequestedEmail("");
        setLastMagicLink("");
      },
      refreshUser,
    }),
    [lastMagicLink, loading, refreshUser, requestedEmail, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
