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
          <Route element={<ProtectedRouteLayout />}>
            <Route path="/dashboard" element={<div>Dashboard page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("ProtectedRouteLayout", () => {
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
});
