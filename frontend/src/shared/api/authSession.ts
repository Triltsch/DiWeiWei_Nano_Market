import type { AuthTokens, AuthUser } from "../../features/auth/types";

const AUTH_REFRESH_TOKEN_KEY = "auth_refresh_token";
const AUTH_USER_KEY = "auth_user";

let inMemoryTokens: AuthTokens | null = null;

export function getAccessToken(): string | null {
  return inMemoryTokens?.accessToken ?? null;
}

export function getRefreshToken(): string | null {
  if (inMemoryTokens?.refreshToken) {
    return inMemoryTokens.refreshToken;
  }

  return localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const rawValue = localStorage.getItem(AUTH_USER_KEY);

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as AuthUser;
  } catch {
    return null;
  }
}

export function setAuthSession(tokens: AuthTokens, user: AuthUser): void {
  inMemoryTokens = tokens;
  localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, tokens.refreshToken);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function updateAuthTokens(tokens: AuthTokens): void {
  inMemoryTokens = tokens;
  localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, tokens.refreshToken);
}

export function clearAuthSession(): void {
  inMemoryTokens = null;
  localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}
