/**
 * Protected Route Layout Tests
 *
 * Tests for the ProtectedRouteLayout component that guards routes based on authentication state.
 * Verifies that protected routes are accessible to authenticated users and redirect
 * unauthenticated users to the login page.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { ProtectedRouteLayout } from "./ProtectedRouteLayout";

function renderWithAuth(value: AuthContextValue, initialPath = "/dashboard"): void {
  render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route path="/forbidden" element={<div>Forbidden page</div>} />
          <Route element={<ProtectedRouteLayout />}>
            <Route path="/dashboard" element={<div>Dashboard page</div>} />
          </Route>
          <Route element={<ProtectedRouteLayout requiredRoles={["admin"]} />}>
            <Route path="/admin" element={<div>Admin page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("ProtectedRouteLayout", () => {
  /**
   * Verifies that protected routes render their content when user is authenticated.
   * When isAuthenticated=true, the child route (dashboard) should be rendered.
   */
  it("renders protected content when authenticated", () => {
    renderWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: { email: "user@example.com" },
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    expect(screen.getByText("Dashboard page")).toBeTruthy();
  });

  /**
   * Verifies that unauthenticated users are redirected to the login page.
   * When isAuthenticated=false, attempting to access a protected route should
   * redirect to the login page instead of rendering the protected content.
   */
  it("redirects to login when unauthenticated", () => {
    renderWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    expect(screen.getByText("Login page")).toBeTruthy();
  });

  /**
   * Verifies that an authenticated user is redirected to forbidden when their
   * role is insufficient for a role-protected route.
   */
  it("redirects authenticated user to forbidden when role is not permitted", () => {
    renderWithAuth(
      {
        isLoading: false,
        isAuthenticated: true,
        user: { email: "creator@example.com", role: "creator" },
        login: async () => Promise.resolve(),
        logout: async () => Promise.resolve(),
      },
      "/admin"
    );

    expect(screen.getByText("Forbidden page")).toBeTruthy();
  });

  /**
   * Verifies that an authenticated user with the required role can access a role-protected route.
   * When isAuthenticated=true and the user's role satisfies requiredRoles (admin in this case),
   * the protected admin route should render its content instead of redirecting to forbidden.
   */
  it("allows authenticated user when role requirement is met", () => {
    renderWithAuth(
      {
        isLoading: false,
        isAuthenticated: true,
        user: { email: "admin@example.com", role: "admin" },
        login: async () => Promise.resolve(),
        logout: async () => Promise.resolve(),
      },
      "/admin"
    );

    expect(screen.getByText("Admin page")).toBeTruthy();
  });
});
