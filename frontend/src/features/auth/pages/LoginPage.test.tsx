/**
 * Tests for login redirect behavior.
 * Scope: validates role-aware fallback routing after successful login.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getStoredUser } from "../../../shared/api/authSession";
import { LanguageProvider } from "../../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../AuthContext";
import { LoginPage } from "./LoginPage";

vi.mock("../../../shared/api/authSession", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api/authSession")>(
    "../../../shared/api/authSession"
  );
  return {
    ...actual,
    getStoredUser: vi.fn(),
  };
});

const mockedGetStoredUser = vi.mocked(getStoredUser);

function renderLoginPage(authValue: AuthContextValue, initialEntry: string): void {
  render(
    <LanguageProvider>
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={[initialEntry]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/search" element={<div>search-destination</div>} />
            <Route path="/dashboard" element={<div>dashboard-destination</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </LanguageProvider>
  );
}

async function fillAndSubmitLoginForm(): Promise<void> {
  fireEvent.change(screen.getByLabelText("E-Mail"), {
    target: { value: "consumer@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Passwort"), {
    target: { value: "SecurePass123!" },
  });
  const submitButton = screen.getByRole("button", { name: "Anmelden" });
  await waitFor(() => expect(submitButton).toBeEnabled());
  fireEvent.click(submitButton);
}

describe("LoginPage", () => {
  const loginMock = vi.fn(async () => Promise.resolve());

  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: loginMock,
    logout: async () => Promise.resolve(),
  };

  beforeEach(() => {
    loginMock.mockClear();
    mockedGetStoredUser.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
  });

  it("redirects consumers to search when no redirect query is provided", async () => {
    mockedGetStoredUser.mockReturnValue({
      id: "user-1",
      email: "consumer@example.com",
      username: "consumer",
      role: "consumer",
    });

    renderLoginPage(authValue, "/login");
    await fillAndSubmitLoginForm();

    await waitFor(() => expect(loginMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("search-destination")).toBeInTheDocument();
  });

  it("falls back to search for consumers when redirect query is invalid", async () => {
    mockedGetStoredUser.mockReturnValue({
      id: "user-2",
      email: "consumer@example.com",
      username: "consumer",
      role: "consumer",
    });

    renderLoginPage(authValue, "/login?redirect=https://example.com");
    await fillAndSubmitLoginForm();

    await waitFor(() => expect(loginMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("search-destination")).toBeInTheDocument();
  });
});
