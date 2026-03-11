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
  /**
   * Verifies that the shared brand asset is rendered in the page and remains
   * available from the expected public path.
   */
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

  /**
   * Verifies that the brand link in the header remains the canonical entry
   * point back to the home route.
   */
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

  /**
   * Verifies that unauthenticated visitors are offered the expected auth entry
   * points in navigation and that search is rendered disabled.
   */
  it("displays Login and Register for unauthenticated users", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const searchButtons = screen.getAllByRole("button", { name: "Search" });
    const loginLink = screen.getByRole("link", { name: "Login" });
    const registerLinks = screen.getAllByRole("link", { name: "Register" });
    expect(searchButtons[0].getAttribute("aria-disabled")).toBe("true");
    expect(loginLink).toBeTruthy();
    expect(registerLinks.length).toBeGreaterThanOrEqual(1);
  });

  /**
   * Verifies that authenticated users see the protected navigation targets and
   * logout action in the header.
   */
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

  /**
   * Verifies that the landing page hero presents the key value proposition and
   * primary calls to action.
   */
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

  /**
   * Verifies that the mobile menu control is exposed with the required ARIA
   * state for accessibility.
   */
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

  /**
   * Verifies that the language selector placeholder is visible and defaults to
   * German.
   */
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
    expect((languageSelects[0] as HTMLSelectElement).value).toBe("de");
  });

  /**
   * Verifies that the feature-card section renders the three marketed value
   * propositions for the landing page.
   */
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

  /**
   * Verifies that the creator-focused secondary call to action is present and
   * actionable.
   */
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

  /**
   * Verifies that the legal footer navigation is present for terms and privacy
   * discovery.
   */
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
