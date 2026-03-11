/**
 * Tests for landing page/navigation wiring in Story 8.2.
 * Scope: verify logo rendering, home-link behavior, and global navigation
 * functionality for both authenticated and unauthenticated users.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { HomePage } from "./pages";

function renderHomeWithAuth(authValue: AuthContextValue): void {
  render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={["/"]}>
        <HomePage />
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("HomePage", () => {
  it("renders the logo image in navigation", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const logoImages = screen.getAllByAltText("DiWeiWei Nano Market Logo");
    expect(logoImages.length).toBeGreaterThanOrEqual(1);
    expect(logoImages[0].getAttribute("src")).toBe("/logo.png");
  });

  it("links the header logo to the home route", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const logoLink = screen.getByRole("link", { name: "DiWeiWei Nano Market Home" });
    expect(logoLink.getAttribute("href")).toBe("/");
  });

  it("displays Login and Register for unauthenticated users", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const loginLink = screen.getByRole("link", { name: "Login" });
    const registerLinks = screen.getAllByRole("link", { name: "Register" });
    expect(loginLink).toBeTruthy();
    expect(registerLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("displays Dashboard, Profile, and Logout for authenticated users", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: { id: "1", username: "testuser", email: "test@example.com" },
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const dashboardLink = screen.getByRole("link", { name: "Dashboard" });
    const profileLink = screen.getByRole("link", { name: "Profile" });
    const logoutButton = screen.getByRole("button", { name: "Logout" });
    expect(dashboardLink).toBeTruthy();
    expect(profileLink).toBeTruthy();
    expect(logoutButton).toBeTruthy();
  });

  it("displays value proposition and CTA buttons", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const heading = screen.getByRole("heading", { name: "DiWeiWei Nano Market" });
    expect(heading).toBeTruthy();

    const registerCtas = screen.getAllByRole("link", { name: "Jetzt Registrieren" });
    const discoverCta = screen.getByRole("link", { name: "Lerneinheiten Entdecken" });
    expect(registerCtas.length).toBeGreaterThanOrEqual(1);
    expect(discoverCta).toBeTruthy();
  });

  it("provides accessible mobile menu button", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const buttons = screen.getAllByRole("button");
    const menuButton = buttons.find((btn) => btn.getAttribute("aria-label")?.includes("menu"));
    expect(menuButton).toBeTruthy();
    expect(menuButton?.getAttribute("aria-expanded")).toBe("false");
  });

  it("displays language selector", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const languageSelects = screen.getAllByRole("combobox", {
      name: /select language/i,
    });
    expect(languageSelects.length).toBeGreaterThanOrEqual(1);
    expect(languageSelects[0].getAttribute("value")).toBe("de");
  });

  it("displays feature cards section", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const featureHeading = screen.getByRole("heading", { name: "Warum DiWeiWei?" });
    expect(featureHeading).toBeTruthy();

    const hochwertigeInhalte = screen.getByText("Hochwertige Inhalte");
    const einfachTeilbar = screen.getByText("Einfach Teilbar");
    const schnellerZugriff = screen.getByText("Schneller Zugriff");

    expect(hochwertigeInhalte).toBeTruthy();
    expect(einfachTeilbar).toBeTruthy();
    expect(schnellerZugriff).toBeTruthy();
  });

  it("displays creator CTA section", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const creatorHeading = screen.getByRole("heading", {
      name: "Sie sind Inhalts-Creator oder Trainer?",
    });
    expect(creatorHeading).toBeTruthy();

    const creatorCTA = screen.getByRole("link", { name: "Als Creator Beitreten" });
    expect(creatorCTA).toBeTruthy();
  });

  it("displays footer links", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const termsLink = screen.getByRole("link", { name: "Nutzungsbedingungen" });
    const privacyLink = screen.getByRole("link", { name: "Datenschutz" });
    expect(termsLink).toBeTruthy();
    expect(privacyLink).toBeTruthy();
  });
});
