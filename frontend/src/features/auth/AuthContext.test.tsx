/**
 * Auth Context Tests
 *
 * Tests for the AuthContext component that manages authentication state and session lifecycle.
 * Verifies login/logout flows, custom hook behavior, and integration with API and session storage.
 */

import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as authApi from "./api";
import * as authSessionModule from "../../shared/api/authSession";
import type { AuthTokens } from "../../shared/api/types";
import { AuthProvider, useAuth } from "./AuthContext";

// Mock dependencies
vi.mock("./api");
vi.mock("../../shared/api/authSession");

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);
  });

  /**
   * Verifies successful login flow: credentials sent to API, tokens stored,
   * and context state updated to authenticated.
   */
  it("login updates context with tokens", async () => {
    const mockTokens: AuthTokens = {
      accessToken: "new-access",
      refreshToken: "new-refresh",
      expiresIn: 900,
    };

    (authApi.loginUser as any).mockResolvedValue(mockTokens);
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    expect(result.current.isAuthenticated).toBe(false);

    await act(async () => {
      await result.current.login("user@example.com", "password123");
    });

    expect(authApi.loginUser as any).toHaveBeenCalledWith({
      email: "user@example.com",
      password: "password123",
    });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe("user@example.com");
  });

  /**
   * Verifies logout clears auth session and resets context.
    * After logout, authentication state should be cleared and context is unauthenticated.
   */
  it("logout clears session and context", async () => {
    const mockTokens: AuthTokens = {
      accessToken: "new-access",
      refreshToken: "new-refresh",
      expiresIn: 900,
    };

    (authApi.loginUser as any).mockResolvedValue(mockTokens);
    (authApi.logoutUser as any).mockResolvedValue(undefined);
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await act(async () => {
      await result.current.login("user@example.com", "password123");
    });

    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      await result.current.logout();
    });

    expect(authSessionModule.clearAuthSession as any).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  /**
   * Verifies session bootstrap on mount from stored refresh token.
   * If a refresh token exists in storage at mount time, context should
   * automatically restore the session without requiring re-login.
   */
  it("bootstrap session on mount from stored refresh token", async () => {
    const refreshedTokens: AuthTokens = {
      accessToken: "bootstrapped-access",
      refreshToken: "bootstrapped-refresh",
      expiresIn: 900,
    };

    (authSessionModule.getRefreshToken as any).mockReturnValue("stored-refresh-token");
    (authSessionModule.getStoredUser as any).mockReturnValue({ email: "user@example.com" });
    (authApi.refreshToken as any).mockResolvedValue(refreshedTokens);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(authApi.refreshToken as any).toHaveBeenCalledWith("stored-refresh-token");
    expect(result.current.isAuthenticated).toBe(true);
  });

  /**
   * Verifies unauthorized events clear the active session immediately.
   * When the interceptor dispatches `auth:unauthorized`, context should reset user
   * state so the UI can redirect or prompt for re-authentication.
   */
  it("clears session when auth:unauthorized is dispatched", async () => {
    const mockTokens: AuthTokens = {
      accessToken: "new-access",
      refreshToken: "new-refresh",
      expiresIn: 900,
    };

    (authApi.loginUser as any).mockResolvedValue(mockTokens);
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await act(async () => {
      await result.current.login("user@example.com", "password123");
    });

    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  /**
   * Verifies login error handling: API errors are caught and propagated.
   * Failed login attempts should keep context unauthenticated.
   */
  it("handles login errors gracefully", async () => {
    const loginError = new Error("Invalid credentials");
    (authApi.loginUser as any).mockRejectedValue(loginError);
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await expect(
      act(async () => {
        await result.current.login("user@example.com", "wrongpassword");
      })
    ).rejects.toThrow("Invalid credentials");

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  /**
   * Verifies session bootstrap handles missing stored session gracefully.
   * If no refresh token exists at mount, context should be unauthenticated.
   */
  it("handles missing stored session during bootstrap", async () => {
    (authSessionModule.getRefreshToken as any).mockReturnValue(null);
    (authSessionModule.getStoredUser as any).mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(authApi.refreshToken as any).not.toHaveBeenCalled();
  });
});

