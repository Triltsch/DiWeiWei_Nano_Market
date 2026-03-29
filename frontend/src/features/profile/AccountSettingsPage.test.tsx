/**
 * Account settings page tests.
 *
 * Covers the authenticated user flows introduced for Issue #114:
 * - loading and rendering current profile data
 * - saving profile edits and synchronizing language preference
 * - showing inline password-change validation errors
 * - executing GDPR export and deletion request actions
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as sharedApi from "../../shared/api";
import { LanguageProvider } from "../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { AccountSettingsPage } from "./AccountSettingsPage";

vi.mock("../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../shared/api")>("../../shared/api");
  return {
    ...actual,
    changeMyPassword: vi.fn(),
    exportMyData: vi.fn(),
    getMyProfile: vi.fn(),
    requestMyAccountDeletion: vi.fn(),
    updateMyProfile: vi.fn(),
  };
});

const mockedGetMyProfile = vi.mocked(sharedApi.getMyProfile);
const mockedUpdateMyProfile = vi.mocked(sharedApi.updateMyProfile);
const mockedChangeMyPassword = vi.mocked(sharedApi.changeMyPassword);
const mockedExportMyData = vi.mocked(sharedApi.exportMyData);
const mockedRequestMyAccountDeletion = vi.mocked(sharedApi.requestMyAccountDeletion);

const baseProfile = {
  id: "user-1",
  email: "user@example.com",
  username: "nano-user",
  firstName: "Ada",
  lastName: "Lovelace",
  bio: "Builds learning experiences.",
  preferredLanguage: "de",
  status: "active" as const,
  role: "creator" as const,
  emailVerified: true,
  verifiedAt: "2026-03-28T10:00:00Z",
  createdAt: "2026-03-20T10:00:00Z",
  updatedAt: "2026-03-28T10:00:00Z",
  lastLogin: "2026-03-28T11:00:00Z",
  profileAvatar: null,
  company: "DiWeiWei",
  jobTitle: "Creator",
  phone: "+49-123",
  acceptedTerms: "2026-03-20T10:00:00Z",
  acceptedPrivacy: "2026-03-20T10:00:00Z",
  deletionRequestedAt: null,
  deletionScheduledAt: null,
};

function renderPage(authValue?: Partial<AuthContextValue>): void {
  const value: AuthContextValue = {
    isLoading: false,
    isAuthenticated: true,
    user: {
      email: "user@example.com",
      role: "creator",
      username: "nano-user",
      id: "user-1",
    },
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
    ...authValue,
  };

  render(
    <LanguageProvider>
      <AuthContext.Provider value={value}>
        <AccountSettingsPage />
      </AuthContext.Provider>
    </LanguageProvider>,
  );
}

describe("AccountSettingsPage", () => {
  beforeEach(() => {
    mockedGetMyProfile.mockReset();
    mockedUpdateMyProfile.mockReset();
    mockedChangeMyPassword.mockReset();
    mockedExportMyData.mockReset();
    mockedRequestMyAccountDeletion.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
    mockedGetMyProfile.mockResolvedValue(baseProfile);
  });

  /**
   * Verifies the page loads the current profile and renders editable account
   * fields instead of the previous placeholder state.
   */
  it("loads and renders account settings data", async () => {
    renderPage();

    expect(screen.getByLabelText("Profil wird geladen...")).toBeTruthy();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Profil" })).toBeTruthy();
    });

    expect(screen.getByDisplayValue("nano-user")).toBeTruthy();
    expect(screen.getByDisplayValue("Ada")).toBeTruthy();
    expect(screen.getByDisplayValue("Builds learning experiences.")).toBeTruthy();
  });

  /**
   * Verifies the language selector inside the profile form updates the active
   * UI language immediately instead of waiting for a backend roundtrip.
   */
  it("switches the visible UI language immediately from the profile form", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("Sprache")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Sprache"), { target: { value: "en" } });

    await waitFor(() => {
      expect(window.localStorage.getItem("diwei_ui_language")).toBe("en");
    });
    expect(screen.getByRole("button", { name: "Save profile" })).toBeTruthy();
  });

  /**
   * Verifies profile edits are submitted and the selected preferred language is
   * also persisted through the UI language provider state.
   */
  it("saves profile edits and syncs the language preference", async () => {
    const updatedProfile = {
      ...baseProfile,
      firstName: "Grace",
      preferredLanguage: "en",
    };

    mockedGetMyProfile.mockReset();
    mockedGetMyProfile.mockResolvedValueOnce(baseProfile).mockResolvedValue(updatedProfile);
    mockedUpdateMyProfile.mockResolvedValue(updatedProfile);

    renderPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue("Ada")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Vorname"), { target: { value: "Grace" } });
    fireEvent.change(screen.getByLabelText("Sprache"), { target: { value: "en" } });
    fireEvent.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => {
      expect(mockedUpdateMyProfile).toHaveBeenCalledWith(
        expect.objectContaining({ firstName: "Grace", preferredLanguage: "en" }),
      );
    });

    await waitFor(() => {
      expect(window.localStorage.getItem("diwei_ui_language")).toBe("en");
    });
    expect(screen.getByDisplayValue("Grace")).toBeTruthy();
  });

  /**
   * Verifies a wrong current password stays an inline error and does not force
   * the page out of the authenticated state.
   */
  it("shows an inline error when the current password is incorrect", async () => {
    mockedChangeMyPassword.mockRejectedValue(
      new sharedApi.AccountSettingsApiError(
        "Current password is incorrect",
        "current-password-incorrect",
      ),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("Aktuelles Passwort")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Aktuelles Passwort"), {
      target: { value: "WrongP@ss1" },
    });
    fireEvent.change(screen.getByLabelText("Neues Passwort"), {
      target: { value: "BetterP@ss2" },
    });
    fireEvent.change(screen.getByLabelText("Neues Passwort bestätigen"), {
      target: { value: "BetterP@ss2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Passwort ändern" }));

    await waitFor(() => {
      expect(screen.getByText("Das aktuelle Passwort ist nicht korrekt.")).toBeTruthy();
    });
  });

  /**
   * Verifies the password change button is wired to the backend call when the
   * form is valid and surfaces the success response.
   */
  it("submits the password change when the form is valid", async () => {
    mockedChangeMyPassword.mockResolvedValue("Password changed successfully");

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText("Aktuelles Passwort")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Aktuelles Passwort"), {
      target: { value: "OldP@ss1" },
    });
    fireEvent.change(screen.getByLabelText("Neues Passwort"), {
      target: { value: "BetterP@ss2" },
    });
    fireEvent.change(screen.getByLabelText("Neues Passwort bestätigen"), {
      target: { value: "BetterP@ss2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Passwort ändern" }));

    await waitFor(() => {
      expect(mockedChangeMyPassword).toHaveBeenCalledWith({
        currentPassword: "OldP@ss1",
        newPassword: "BetterP@ss2",
      });
    });

    expect(screen.getByText("Password changed successfully")).toBeTruthy();
  });

  /**
   * Verifies the GDPR export action calls the backend and surfaces a success
   * state after the download has been prepared.
   */
  it("exports user data and shows success feedback", async () => {
    const createObjectUrlSpy = vi.fn(() => "blob:export-test");
    const revokeObjectUrlSpy = vi.fn();
    const anchorClickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    Object.defineProperty(window.URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: createObjectUrlSpy,
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: revokeObjectUrlSpy,
    });

    mockedExportMyData.mockResolvedValue({
      exportDate: "2026-03-28T12:00:00Z",
      userId: "user-1",
      email: "user@example.com",
      username: "nano-user",
      firstName: "Ada",
      lastName: "Lovelace",
      bio: null,
      company: null,
      jobTitle: null,
      phone: null,
      preferredLanguage: "de",
      createdAt: "2026-03-20T10:00:00Z",
      updatedAt: "2026-03-28T10:00:00Z",
      lastLogin: null,
      emailVerified: true,
      verifiedAt: null,
      status: "active",
      role: "creator",
      acceptedTerms: null,
      acceptedPrivacy: null,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Datenexport herunterladen" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Datenexport herunterladen" }));

    await waitFor(() => {
      expect(mockedExportMyData).toHaveBeenCalledOnce();
      expect(screen.getByText("Ihr Datenexport wurde vorbereitet.")).toBeTruthy();
    });

    expect(createObjectUrlSpy).toHaveBeenCalledOnce();
    expect(revokeObjectUrlSpy).toHaveBeenCalledOnce();
    expect(anchorClickSpy).toHaveBeenCalledOnce();
  });

  /**
   * Verifies account deletion is blocked until the explicit confirmation is
   * checked and then submits the confirmed request successfully.
   */
  it("requests account deletion only after explicit confirmation", async () => {
    mockedRequestMyAccountDeletion.mockResolvedValue({
      message: "Account deletion scheduled. You have 30 days to cancel.",
      deletionScheduledAt: "2026-04-27T10:00:00Z",
      gracePeriodDays: 30,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Account-Löschung anfordern" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Account-Löschung anfordern" }));

    await waitFor(() => {
      expect(screen.getByText("Bitte bestätigen Sie die Löschanfrage ausdrücklich.")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.change(screen.getByLabelText("Grund für die Löschanfrage"), {
      target: { value: "No longer needed" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Account-Löschung anfordern" }));

    await waitFor(() => {
      expect(mockedRequestMyAccountDeletion).toHaveBeenCalledWith({
        confirm: true,
        reason: "No longer needed",
      });
    });

    expect(screen.getByText("Account deletion scheduled. You have 30 days to cancel.")).toBeTruthy();
  });
});