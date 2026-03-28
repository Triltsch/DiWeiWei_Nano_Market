/**
 * Tests for landing page/navigation wiring in Story 8.2.
 * Scope: verify logo rendering, home-link behavior, and global navigation
 * functionality for both authenticated and unauthenticated users.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as sharedApi from "../../shared/api";
import { LanguageProvider } from "../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { HomePage, NanoDetailsPage, NotFoundPage, SearchPage } from "./pages";
import { PrivacyPage, TermsPage } from "../legal/pages";

vi.mock("../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../shared/api")>("../../shared/api");
  return {
    ...actual,
    createNanoComment: vi.fn(),
    createNanoRating: vi.fn(),
    searchNanos: vi.fn(),
    getNanoComments: vi.fn(),
    getNanoDetail: vi.fn(),
    getNanoDownloadInfo: vi.fn(),
    getNanoRatings: vi.fn(),
    updateMyNanoRating: vi.fn(),
  };
});

const mockedCreateNanoComment = vi.mocked(sharedApi.createNanoComment);
const mockedCreateNanoRating = vi.mocked(sharedApi.createNanoRating);
const mockedGetNanoComments = vi.mocked(sharedApi.getNanoComments);
const mockedSearchNanos = vi.mocked(sharedApi.searchNanos);
const mockedGetNanoDetail = vi.mocked(sharedApi.getNanoDetail);
const mockedGetNanoDownloadInfo = vi.mocked(sharedApi.getNanoDownloadInfo);
const mockedGetNanoRatings = vi.mocked(sharedApi.getNanoRatings);
const mockedUpdateMyNanoRating = vi.mocked(sharedApi.updateMyNanoRating);

function LocationProbe(): JSX.Element {
  const location = useLocation();
  return <div data-testid="location-probe">{`${location.pathname}${location.search}`}</div>;
}

function renderHomeWithAuth(authValue: AuthContextValue): void {
  render(
    <LanguageProvider>
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={["/"]}>
          <HomePage />
        </MemoryRouter>
      </AuthContext.Provider>
    </LanguageProvider>
  );
}

describe("HomePage", () => {
  beforeEach(() => {
    mockedCreateNanoComment.mockReset();
    mockedCreateNanoRating.mockReset();
    mockedGetNanoComments.mockReset();
    mockedSearchNanos.mockReset();
    mockedGetNanoDetail.mockReset();
    mockedGetNanoDownloadInfo.mockReset();
    mockedGetNanoRatings.mockReset();
    mockedUpdateMyNanoRating.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
  });

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
  * points in navigation and that search remains available for discovery.
   */
  it("displays Login and Register for unauthenticated users", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const searchLinks = screen.getAllByRole("link", { name: "Suche" });
    const loginLink = screen.getByRole("link", { name: "Anmelden" });
    const registerLinks = screen.getAllByRole("link", { name: "Registrieren" });
    expect(searchLinks.length).toBeGreaterThanOrEqual(1);
    expect(searchLinks[0].getAttribute("href")).toBe("/search");
    expect(loginLink).toBeTruthy();
    expect(registerLinks.length).toBeGreaterThanOrEqual(1);
  });

  /**
   * Verifies that authenticated users see the protected navigation targets and
   * logout action in the header.
   */
  it("displays Übersicht, Profil, and Abmelden for authenticated users", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: { id: "1", username: "testuser", email: "test@example.com", role: "creator" },
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const dashboardLink = screen.getByRole("link", { name: "Übersicht" });
    const profileLink = screen.getByRole("link", { name: "Profil" });
    const logoutButton = screen.getByRole("button", { name: "Abmelden" });
    expect(dashboardLink).toBeTruthy();
    expect(profileLink).toBeTruthy();
    expect(logoutButton).toBeTruthy();
  });

  /**
   * Ensures that authenticated users with the consumer role only see consumer
   * navigation (e.g. Profil) and that creator, moderator, and admin-specific
   * navigation links are not visible.
   */
  it("hides creator and moderator/admin links for authenticated consumer role", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: { id: "2", username: "consumer", email: "consumer@example.com", role: "consumer" },
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    expect(screen.queryByRole("link", { name: "Übersicht" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Hochladen" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Moderations-Queue" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Admin" })).toBeNull();
    expect(screen.getByRole("link", { name: "Profil" })).toBeTruthy();
  });

  /**
   * Ensures that authenticated moderator users see dashboard, upload, and
   * moderation queue navigation links, but do not see the admin navigation
   * entry.
   */
  it("shows moderation link for moderator role and hides admin link", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: true,
      user: {
        id: "3",
        username: "moderator",
        email: "moderator@example.com",
        role: "moderator",
      },
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    expect(screen.getByRole("link", { name: "Übersicht" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Hochladen" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Moderations-Queue" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Admin" })).toBeNull();
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
    const menuButton = buttons.find((btn) => btn.getAttribute("aria-label")?.includes("Menü"));
    expect(menuButton).toBeTruthy();
    expect(menuButton?.getAttribute("aria-expanded")).toBe("false");
  });

  /**
   * Verifies that clicking the logo/home link while the mobile menu is open
   * closes the menu. This prevents the UI from getting stuck in an open-menu
   * state after navigating home.
   */
  it("closes the mobile menu when the logo home link is clicked", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    // Open the mobile menu via the hamburger button
    const menuButton = screen
      .getAllByRole("button")
      .find((btn) => btn.getAttribute("aria-label")?.includes("Menü"));
    expect(menuButton).toBeTruthy();
    fireEvent.click(menuButton!);
    expect(menuButton?.getAttribute("aria-expanded")).toBe("true");

    // Click the logo home link – this should close the menu
    const logoLink = screen.getByRole("link", { name: "DiWeiWei Nano Market Home" });
    fireEvent.click(logoLink);
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
      name: /sprache ausw\u00e4hlen/i,
    });
    expect(languageSelects.length).toBeGreaterThanOrEqual(1);
    expect((languageSelects[0] as HTMLSelectElement).value).toBe("de");
  });

  it("switches logo image from German to English when language is changed", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const logoImages = screen.getAllByAltText("DiWeiWei Nano Market Logo");
    expect(logoImages[0].getAttribute("src")).toBe("/logo.png");

    const languageSelect = screen.getAllByRole("combobox", {
      name: /sprache ausw\u00e4hlen/i,
    })[0] as HTMLSelectElement;

    fireEvent.change(languageSelect, { target: { value: "en" } });

    const updatedLogoImages = screen.getAllByAltText("DiWeiWei Nano Market Logo");
    expect(updatedLogoImages[0].getAttribute("src")).toBe("/logo_en.png");
  });

  it("switches navigation labels to English when language is changed", () => {
    renderHomeWithAuth({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      login: async () => Promise.resolve(),
      logout: async () => Promise.resolve(),
    });

    const languageSelect = screen.getAllByRole("combobox", {
      name: /sprache ausw\u00e4hlen/i,
    })[0] as HTMLSelectElement;

    fireEvent.change(languageSelect, { target: { value: "en" } });

    expect(screen.getAllByRole("link", { name: "Search" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("link", { name: "Login" })).toBeTruthy();
    expect(screen.getAllByRole("link", { name: "Register" }).length).toBeGreaterThanOrEqual(1);
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

describe("SearchPage", () => {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  function renderSearch(initialEntry = "/search"): void {
    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={[initialEntry]}>
            <Routes>
              <Route
                path="/search"
                element={
                  <>
                    <SearchPage />
                    <LocationProbe />
                  </>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );
  }

  beforeEach(() => {
    mockedSearchNanos.mockReset();
    mockedGetNanoDetail.mockReset();
    mockedGetNanoDownloadInfo.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("uses URL query/filter params as initial state and requests first page", async () => {
    mockedSearchNanos.mockResolvedValue({
      items: [
        {
          id: "nano-1",
          title: "React Basics",
          creator: "Alice",
          averageRating: 4.5,
          durationMinutes: 15,
        },
      ],
      total: 1,
      page: 1,
      pageSize: 20,
      totalPages: 1,
      hasNextPage: false,
      hasPrevPage: false,
    });

    renderSearch("/search?q=react&level=beginner&language=en");

    await waitFor(() => {
      expect(mockedSearchNanos).toHaveBeenCalledWith({
        query: "react",
        filters: {
          category: "",
          level: "1",
          duration: "",
          language: "en",
        },
        limit: 20,
        page: 1,
      });
    });

    expect(screen.getByDisplayValue("react")).toBeTruthy();
    expect(screen.getByText("React Basics")).toBeTruthy();
  });

  it("updates URL and triggers debounced search input", async () => {
    mockedSearchNanos.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
      hasNextPage: false,
      hasPrevPage: false,
    });

    renderSearch();

    await waitFor(() => {
      expect(mockedSearchNanos).toHaveBeenCalledWith({
        query: "",
        filters: {
          category: "",
          level: "",
          duration: "",
          language: "",
        },
        limit: 20,
        page: 1,
      });
    });

    const keywordInput = screen.getByLabelText("Suchbegriff");
    fireEvent.change(keywordInput, { target: { value: "python" } });

    expect(screen.getByTestId("location-probe").textContent).toBe("/search?q=python");

    await waitFor(() => {
      expect(mockedSearchNanos).toHaveBeenCalledTimes(2);
      expect(mockedSearchNanos).toHaveBeenLastCalledWith({
        query: "python",
        filters: {
          category: "",
          level: "",
          duration: "",
          language: "",
        },
        limit: 20,
        page: 1,
      });
    });
  });

  it("shows configured empty state message when no nanos are found", async () => {
    mockedSearchNanos.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
      hasNextPage: false,
      hasPrevPage: false,
    });

    renderSearch();

    const emptyState = await screen.findByText(
      "Keine Nano-Lerneinheiten gefunden. Bitte versuchen Sie andere Suchbegriffe."
    );
    expect(emptyState).toBeTruthy();
    expect(mockedSearchNanos).toHaveBeenCalledTimes(1);
  });

  it("shows a localized error state when the search API request fails", async () => {
    mockedSearchNanos
      .mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        pageSize: 20,
        totalPages: 0,
        hasNextPage: false,
        hasPrevPage: false,
      })
      .mockRejectedValueOnce(new Error("Search backend unavailable"));

    renderSearch();

    const keywordInput = screen.getByLabelText("Suchbegriff");
    fireEvent.change(keywordInput, { target: { value: "python" } });

    const errorMessage = await screen.findByText(
      "Suche fehlgeschlagen. Bitte versuchen Sie es erneut."
    );
    expect(errorMessage).toBeTruthy();

    await waitFor(() => {
      expect(mockedSearchNanos).toHaveBeenCalledTimes(2);
      expect(mockedSearchNanos).toHaveBeenLastCalledWith({
        query: "python",
        filters: {
          category: "",
          level: "",
          duration: "",
          language: "",
        },
        limit: 20,
        page: 1,
      });
    });
  });

  it("loads additional pages when load more is clicked", async () => {
    mockedSearchNanos
      .mockResolvedValueOnce({
        items: [
          {
            id: "nano-1",
            title: "First Nano",
            creator: "Alice",
            averageRating: 4.8,
            durationMinutes: 10,
          },
        ],
        total: 2,
        page: 1,
        pageSize: 20,
        totalPages: 2,
        hasNextPage: true,
        hasPrevPage: false,
      })
      .mockResolvedValueOnce({
        items: [
          {
            id: "nano-2",
            title: "Second Nano",
            creator: "Bob",
            averageRating: 4.2,
            durationMinutes: 20,
          },
        ],
        total: 2,
        page: 2,
        pageSize: 20,
        totalPages: 2,
        hasNextPage: false,
        hasPrevPage: true,
      });

    renderSearch("/search?q=nano");

    await screen.findByText("First Nano");

    const loadMoreButton = screen.getByRole("button", { name: "Mehr laden" });
    fireEvent.click(loadMoreButton);

    await waitFor(() => {
      expect(mockedSearchNanos).toHaveBeenNthCalledWith(2, {
        query: "nano",
        filters: {
          category: "",
          level: "",
          duration: "",
          language: "",
        },
        limit: 20,
        page: 2,
      });
    });

    expect(screen.getByText("Second Nano")).toBeTruthy();
  });

  it("supports Discovery -> Detail -> Auth-Gating flow", async () => {
    mockedSearchNanos.mockResolvedValue({
      items: [
        {
          id: "nano-1",
          title: "React Basics",
          creator: "Alice",
          averageRating: 4.8,
          durationMinutes: 12,
        },
      ],
      total: 1,
      page: 1,
      pageSize: 20,
      totalPages: 1,
      hasNextPage: false,
      hasPrevPage: false,
    });

    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: false,
        downloadPath: null,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/search"]}>
            <Routes>
              <Route
                path="/search"
                element={
                  <>
                    <SearchPage />
                    <LocationProbe />
                  </>
                }
              />
              <Route
                path="/nano/:id"
                element={
                  <>
                    <NanoDetailsPage />
                    <LocationProbe />
                  </>
                }
              />
              <Route
                path="/login"
                element={
                  <>
                    <div>Login page</div>
                    <LocationProbe />
                  </>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    const keywordInput = screen.getByLabelText("Suchbegriff");
    fireEvent.change(keywordInput, { target: { value: "react" } });

    const detailLink = await screen.findByRole("link", { name: "React Basics" });
    fireEvent.click(detailLink);

    await screen.findByRole("heading", { name: "React Basics" });
    expect(mockedGetNanoDetail).toHaveBeenCalledWith("nano-1");

    fireEvent.click(screen.getByRole("button", { name: "Jetzt herunterladen" }));

    await waitFor(() => {
      expect(screen.getByTestId("location-probe").textContent).toBe(
        "/login?redirect=%2Fnano%2Fnano-1"
      );
    });
  });
});

describe("NanoDetailsPage", () => {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  beforeEach(() => {
    mockedCreateNanoComment.mockReset();
    mockedCreateNanoRating.mockReset();
    mockedGetNanoComments.mockReset();
    mockedGetNanoDetail.mockReset();
    mockedGetNanoDownloadInfo.mockReset();
    mockedGetNanoRatings.mockReset();
    mockedUpdateMyNanoRating.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders detail metadata, ratings and chat sections", async () => {
    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: false,
        downloadPath: null,
      },
    });
    mockedGetNanoRatings.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 11,
        distribution: [],
      },
      currentUserRating: null,
    });
    mockedGetNanoComments.mockResolvedValue({
      comments: [
        {
          commentId: "comment-1",
          nanoId: "nano-1",
          userId: "user-2",
          username: "bob",
          content: "Sehr hilfreich und klar strukturiert.",
          moderationStatus: "approved",
          createdAt: "2026-03-20T11:00:00Z",
          updatedAt: "2026-03-20T11:00:00Z",
          isEdited: false,
        },
      ],
      pagination: {
        current_page: 1,
        page_size: 5,
        total_results: 1,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/nano/nano-1"]}>
            <Routes>
              <Route path="/nano/:id" element={<NanoDetailsPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    await screen.findByRole("heading", { name: "React Basics" });

    expect(screen.getByText("Download")).toBeTruthy();
    expect(screen.getByText("Bewertungen und Nutzung")).toBeTruthy();
    expect(screen.getByText("Feedback und Austausch")).toBeTruthy();
    expect(screen.getByText("Kommentare")).toBeTruthy();
    expect(screen.getByText("Frontend")).toBeTruthy();
    expect(screen.getByText("CC-BY")).toBeTruthy();
    expect(screen.getByText("Sehr hilfreich und klar strukturiert.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Anmelden, um den Chat zu öffnen" })).toBeTruthy();
  });

  it("redirects unauthenticated users to login when download is clicked", async () => {
    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: false,
        downloadPath: null,
      },
    });
    mockedGetNanoRatings.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 11,
        distribution: [],
      },
      currentUserRating: null,
    });
    mockedGetNanoComments.mockResolvedValue({
      comments: [],
      pagination: {
        current_page: 1,
        page_size: 5,
        total_results: 0,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/nano/nano-1"]}>
            <Routes>
              <Route
                path="/nano/:id"
                element={
                  <>
                    <NanoDetailsPage />
                    <LocationProbe />
                  </>
                }
              />
              <Route
                path="/login"
                element={
                  <>
                    <div>Login page</div>
                    <LocationProbe />
                  </>
                }
              />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    await screen.findByRole("heading", { name: "React Basics" });
    fireEvent.click(screen.getByRole("button", { name: "Jetzt herunterladen" }));

    await waitFor(() => {
      expect(screen.getByTestId("location-probe").textContent).toBe(
        "/login?redirect=%2Fnano%2Fnano-1"
      );
    });

    expect(mockedGetNanoDownloadInfo).not.toHaveBeenCalled();
  });

  /**
   * Verifies that unauthenticated feedback actions follow the same redirect
   * contract as downloads and send the user to login with a return target.
   */
  it("redirects unauthenticated users to login when they try to rate", async () => {
    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: false,
        downloadPath: null,
      },
    });
    mockedGetNanoRatings.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 11,
        distribution: [],
      },
      currentUserRating: null,
    });
    mockedGetNanoComments.mockResolvedValue({
      comments: [],
      pagination: {
        current_page: 1,
        page_size: 5,
        total_results: 0,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/nano/nano-1"]}>
            <Routes>
              <Route
                path="/nano/:id"
                element={
                  <>
                    <NanoDetailsPage />
                    <LocationProbe />
                  </>
                }
              />
              <Route path="/login" element={<LocationProbe />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    await screen.findByRole("heading", { name: "React Basics" });
    fireEvent.click(screen.getByRole("button", { name: "Bewertung auswählen: 5" }));

    await waitFor(() => {
      expect(screen.getByTestId("location-probe").textContent).toBe(
        "/login?redirect=%2Fnano%2Fnano-1"
      );
    });

    expect(mockedCreateNanoRating).not.toHaveBeenCalled();
  });

  it("navigates to the presigned download URL returned by the API", async () => {
    const locationAssignSpy = vi.fn();
    const originalLocation = window.location;

    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalLocation,
        assign: locationAssignSpy,
      },
    });

    try {
      mockedGetNanoDetail.mockResolvedValue({
        nanoId: "nano-1",
        title: "React Basics",
        metadata: {
          description: "Intro course",
          durationMinutes: 12,
          competencyLevel: "beginner",
          language: "en",
          format: "video",
          status: "published",
          version: "1.0.0",
          categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
          license: "CC-BY",
          thumbnailUrl: null,
          uploadedAt: "2026-03-20T10:00:00Z",
          publishedAt: "2026-03-20T11:00:00Z",
          updatedAt: "2026-03-20T12:00:00Z",
        },
        creator: {
          id: "creator-1",
          username: "alice",
        },
        ratingSummary: {
          averageRating: 4.8,
          ratingCount: 11,
          downloadCount: 34,
        },
        downloadInfo: {
          requiresAuthentication: true,
          canDownload: true,
          downloadPath: "nanos/react-basics.mp4",
        },
      });
      mockedGetNanoRatings.mockResolvedValue({
        nanoId: "nano-1",
        aggregation: {
          averageRating: 4.8,
          medianRating: 5,
          ratingCount: 11,
          distribution: [],
        },
        currentUserRating: {
          ratingId: "rating-1",
          score: 4,
          moderationStatus: "approved",
          updatedAt: "2026-03-20T11:30:00Z",
        },
      });
      mockedGetNanoComments.mockResolvedValue({
        comments: [],
        pagination: {
          current_page: 1,
          page_size: 5,
          total_results: 0,
          total_pages: 1,
          has_next_page: false,
          has_prev_page: false,
        },
      });
      mockedGetNanoDownloadInfo.mockResolvedValue({
        nanoId: "nano-1",
        canDownload: true,
        downloadUrl: "https://storage.example.com/nanos/react-basics.mp4?signature=test",
      });

      render(
        <LanguageProvider>
          <AuthContext.Provider
            value={{
              ...authValue,
              isAuthenticated: true,
              user: {
                id: "user-1",
                email: "user@example.com",
                username: "user",
                role: "creator",
              },
            }}
          >
            <MemoryRouter initialEntries={["/nano/nano-1"]}>
              <Routes>
                <Route path="/nano/:id" element={<NanoDetailsPage />} />
              </Routes>
            </MemoryRouter>
          </AuthContext.Provider>
        </LanguageProvider>
      );

      await screen.findByRole("heading", { name: "React Basics" });
      fireEvent.click(screen.getByRole("button", { name: "Jetzt herunterladen" }));

      await waitFor(() => {
        expect(mockedGetNanoDownloadInfo).toHaveBeenCalledWith("nano-1");
        expect(locationAssignSpy).toHaveBeenCalledWith(
          "https://storage.example.com/nanos/react-basics.mp4?signature=test"
        );
      });
    } finally {
      Object.defineProperty(window, "location", {
        configurable: true,
        value: originalLocation,
      });
    }
  });

  /**
   * Verifies that authenticated users can submit a rating and a comment while
   * the UI keeps public moderation semantics explicit.
   */
  it("submits feedback and shows pending moderation state", async () => {
    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: true,
        downloadPath: "nanos/react-basics.mp4",
      },
    });
    mockedGetNanoRatings.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 11,
        distribution: [],
      },
      currentUserRating: null,
    });
    mockedGetNanoComments.mockResolvedValue({
      comments: [],
      pagination: {
        current_page: 1,
        page_size: 5,
        total_results: 0,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });
    mockedCreateNanoRating.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 12,
        distribution: [],
      },
      userRating: {
        ratingId: "rating-1",
        score: 5,
        moderationStatus: "pending",
        updatedAt: "2026-03-21T10:00:00Z",
      },
    });
    mockedCreateNanoComment.mockResolvedValue({
      comment: {
        commentId: "comment-2",
        nanoId: "nano-1",
        userId: "user-1",
        username: "user",
        content: "Bitte noch Beispiele fuer Hooks ergaenzen.",
        moderationStatus: "pending",
        createdAt: "2026-03-21T10:00:00Z",
        updatedAt: "2026-03-21T10:00:00Z",
        isEdited: false,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider
          value={{
            ...authValue,
            isAuthenticated: true,
            user: {
              id: "user-1",
              email: "user@example.com",
              username: "user",
              role: "creator",
            },
          }}
        >
          <MemoryRouter initialEntries={["/nano/nano-1"]}>
            <Routes>
              <Route path="/nano/:id" element={<NanoDetailsPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    await screen.findByRole("heading", { name: "React Basics" });

    fireEvent.click(screen.getByRole("button", { name: "Bewertung auswählen: 5" }));

    await screen.findByText(
      "Ihre Bewertung wurde gespeichert und wartet auf Moderation, bevor sie öffentlich gezählt wird."
    );
    expect(screen.getByText("Ihre Bewertung:")).toBeTruthy();
    expect(screen.getByText("In Moderation")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Eigenen Kommentar verfassen"), {
      target: {
        value: "Bitte noch Beispiele fuer Hooks ergaenzen.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Kommentar absenden" }));

    await screen.findByText(
      "Ihr Kommentar wurde gespeichert und wartet auf Moderation, bevor er öffentlich erscheint."
    );
    expect(screen.getByText("Ihr Kommentar wartet auf Moderation")).toBeTruthy();
    expect(screen.getByText("Bitte noch Beispiele fuer Hooks ergaenzen.")).toBeTruthy();
  });

  it("shows neutral preview title when submitted comment is already approved", async () => {
    mockedGetNanoDetail.mockResolvedValue({
      nanoId: "nano-1",
      title: "React Basics",
      metadata: {
        description: "Intro course",
        durationMinutes: 12,
        competencyLevel: "beginner",
        language: "en",
        format: "video",
        status: "published",
        version: "1.0.0",
        categories: [{ categoryId: "cat-1", categoryName: "Frontend" }],
        license: "CC-BY",
        thumbnailUrl: null,
        uploadedAt: "2026-03-20T10:00:00Z",
        publishedAt: "2026-03-20T11:00:00Z",
        updatedAt: "2026-03-20T12:00:00Z",
      },
      creator: {
        id: "creator-1",
        username: "alice",
      },
      ratingSummary: {
        averageRating: 4.8,
        ratingCount: 11,
        downloadCount: 34,
      },
      downloadInfo: {
        requiresAuthentication: true,
        canDownload: true,
        downloadPath: "nanos/react-basics.mp4",
      },
    });
    mockedGetNanoRatings.mockResolvedValue({
      nanoId: "nano-1",
      aggregation: {
        averageRating: 4.8,
        medianRating: 5,
        ratingCount: 11,
        distribution: [],
      },
      currentUserRating: null,
    });
    mockedGetNanoComments.mockResolvedValue({
      comments: [],
      pagination: {
        current_page: 1,
        page_size: 5,
        total_results: 0,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });
    mockedCreateNanoComment.mockResolvedValue({
      comment: {
        commentId: "comment-2",
        nanoId: "nano-1",
        userId: "user-1",
        username: "user",
        content: "Schon freigegeben.",
        moderationStatus: "approved",
        createdAt: "2026-03-21T10:00:00Z",
        updatedAt: "2026-03-21T10:00:00Z",
        isEdited: false,
      },
    });

    render(
      <LanguageProvider>
        <AuthContext.Provider
          value={{
            ...authValue,
            isAuthenticated: true,
            user: {
              id: "user-1",
              email: "user@example.com",
              username: "user",
              role: "creator",
            },
          }}
        >
          <MemoryRouter initialEntries={["/nano/nano-1"]}>
            <Routes>
              <Route path="/nano/:id" element={<NanoDetailsPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    await screen.findByRole("heading", { name: "React Basics" });

    fireEvent.change(screen.getByLabelText("Eigenen Kommentar verfassen"), {
      target: {
        value: "Schon freigegeben.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Kommentar absenden" }));

    await screen.findByText("Ihr Kommentar");
    expect(screen.queryByText("Ihr Kommentar wartet auf Moderation")).not.toBeInTheDocument();
  });
});

describe("NotFoundPage", () => {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  beforeEach(() => {
    window.localStorage.removeItem("diwei_ui_language");
  });

  it("switches not-found copy from German to English", () => {
    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/unknown-route"]}>
            <Routes>
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    expect(screen.getByRole("heading", { name: "Seite nicht gefunden" })).toBeTruthy();

    const languageSelect = screen.getAllByRole("combobox", {
      name: /sprache ausw\u00e4hlen/i,
    })[0] as HTMLSelectElement;

    fireEvent.change(languageSelect, { target: { value: "en" } });

    expect(screen.getByRole("heading", { name: "Page Not Found" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to Home" })).toBeTruthy();
  });
});

describe("TermsPage", () => {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  beforeEach(() => {
    window.localStorage.removeItem("diwei_ui_language");
  });

  it("switches terms content from German to English", () => {
    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/terms"]}>
            <>
              <HomePage />
              <TermsPage />
            </>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    expect(screen.getByRole("heading", { name: "Nutzungsbedingungen" })).toBeTruthy();

    const languageSelect = screen.getAllByRole("combobox", {
      name: /sprache ausw\u00e4hlen/i,
    })[0] as HTMLSelectElement;

    fireEvent.change(languageSelect, { target: { value: "en" } });

    expect(screen.getByRole("heading", { name: "Terms of Service" })).toBeTruthy();
  });
});

describe("PrivacyPage", () => {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: false,
    user: null,
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  beforeEach(() => {
    window.localStorage.removeItem("diwei_ui_language");
  });

  it("switches privacy content from German to English", () => {
    render(
      <LanguageProvider>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={["/privacy"]}>
            <>
              <HomePage />
              <PrivacyPage />
            </>
          </MemoryRouter>
        </AuthContext.Provider>
      </LanguageProvider>
    );

    expect(screen.getByRole("heading", { name: "Datenschutzerklärung" })).toBeTruthy();

    const languageSelect = screen.getAllByRole("combobox", {
      name: /sprache ausw\u00e4hlen/i,
    })[0] as HTMLSelectElement;

    fireEvent.change(languageSelect, { target: { value: "en" } });

    expect(screen.getByRole("heading", { name: "Privacy Policy" })).toBeTruthy();
  });
});
