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
  updateAuthTokens,
} from "../../shared/api/authSession";
import { loginUser, logoutUser, refreshToken } from "./api";
import type { AuthUser } from "./types";

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

      if (storedUser) {
        setAuthSession(refreshedTokens, storedUser);
      } else {
        updateAuthTokens(refreshedTokens);
      }

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
    const authUser: AuthUser = { email };
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
