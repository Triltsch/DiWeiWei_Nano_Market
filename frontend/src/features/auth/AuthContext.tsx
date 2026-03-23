import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import {
  clearAuthSession,
  getRefreshToken,
  getStoredUser,
  setAuthSession,
} from "../../shared/api/authSession";
import type { AuthRole } from "../../shared/api/types";
import { loginUser, logoutUser, refreshToken } from "./api";
import type { AuthUser } from "./types";

const DEFAULT_AUTH_ROLE: AuthRole = "consumer";

const VALID_AUTH_ROLES: readonly AuthRole[] = ["consumer", "creator", "moderator", "admin"];

function parseAccessTokenClaims(token: string): { email?: string; role?: AuthRole } {
  try {
    const tokenParts = token.split(".");
    if (tokenParts.length < 2) {
      return {};
    }

    const payloadPart = tokenParts[1];
    const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const paddedBase64 = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const decodedPayload = atob(paddedBase64);
    const parsedPayload = JSON.parse(decodedPayload) as {
      email?: unknown;
      role?: unknown;
    };

    const email = typeof parsedPayload.email === "string" ? parsedPayload.email : undefined;
    const role =
      typeof parsedPayload.role === "string" &&
      VALID_AUTH_ROLES.includes(parsedPayload.role as AuthRole)
        ? (parsedPayload.role as AuthRole)
        : undefined;

    return { email, role };
  } catch {
    return {};
  }
}

function buildAuthUserFromTokens(tokens: { accessToken: string }, fallback?: AuthUser | null): AuthUser {
  const claims = parseAccessTokenClaims(tokens.accessToken);
  return {
    email: claims.email ?? fallback?.email ?? "",
    role: claims.role ?? fallback?.role ?? DEFAULT_AUTH_ROLE,
    username: fallback?.username,
    id: fallback?.id,
  };
}

export interface AuthContextValue {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren): JSX.Element {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  const resetAuthState = useCallback(() => {
    clearAuthSession();
    setIsAuthenticated(false);
    setUser(null);
  }, []);

  const refreshSession = useCallback(async () => {
    const currentRefreshToken = getRefreshToken();

    if (!currentRefreshToken) {
      setIsLoading(false);
      setIsAuthenticated(false);
      setUser(null);
      return;
    }

    const storedUser = getStoredUser();
    if (storedUser) {
      setUser(storedUser);
    }

    try {
      const refreshedTokens = await refreshToken(currentRefreshToken);
      const refreshedUser = buildAuthUserFromTokens(refreshedTokens, storedUser);

      setAuthSession(refreshedTokens, refreshedUser);
      setUser(refreshedUser);

      setIsAuthenticated(true);
    } catch {
      resetAuthState();
    } finally {
      setIsLoading(false);
    }
  }, [resetAuthState]);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  useEffect(() => {
    const handleUnauthorized = (): void => {
      resetAuthState();
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [resetAuthState]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginUser({ email, password });
    const authUser = buildAuthUserFromTokens(tokens, {
      email,
      role: DEFAULT_AUTH_ROLE,
    });
    setAuthSession(tokens, authUser);
    setUser(authUser);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    const currentRefreshToken = getRefreshToken();

    try {
      if (currentRefreshToken) {
        await logoutUser(currentRefreshToken);
      }
    } catch (error) {
      void error;
    } finally {
      resetAuthState();
    }
  }, [resetAuthState]);

  const value = useMemo<AuthContextValue>(
    () => ({
      isLoading,
      isAuthenticated,
      user,
      login,
      logout,
    }),
    [isLoading, isAuthenticated, user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

export { AuthContext };
