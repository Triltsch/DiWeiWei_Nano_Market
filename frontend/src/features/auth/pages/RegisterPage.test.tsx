/**
 * Tests for the registration page.
 * Scope: verify localized password requirements, localized registration error
 * handling, and successful submission for valid registration data.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageProvider } from "../../../shared/i18n";
import * as authApi from "../api";
import { RegisterPage } from "./RegisterPage";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    registerUser: vi.fn(),
  };
});

const mockedRegisterUser = vi.mocked(authApi.registerUser);

function renderRegisterPage(): void {
  render(
    <LanguageProvider>
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-email" element={<div>verify-email-destination</div>} />
        </Routes>
      </MemoryRouter>
    </LanguageProvider>
  );
}

function fillValidRegistrationForm(): void {
  fireEvent.change(screen.getByLabelText("E-Mail"), {
    target: { value: "test4@test.de" },
  });
  fireEvent.change(screen.getByLabelText("Benutzername"), {
    target: { value: "tes4" },
  });
  fireEvent.change(screen.getByLabelText("Passwort"), {
    target: { value: "sjdsfgJHKJB//%%8&&" },
  });
  fireEvent.change(screen.getByLabelText("Passwort bestätigen"), {
    target: { value: "sjdsfgJHKJB//%%8&&" },
  });

  const [acceptTermsCheckbox, acceptPrivacyCheckbox] = screen.getAllByRole("checkbox");
  fireEvent.click(acceptTermsCheckbox);
  fireEvent.click(acceptPrivacyCheckbox);
}

describe("RegisterPage", () => {
  beforeEach(() => {
    mockedRegisterUser.mockReset();
    window.localStorage.removeItem("diwei_ui_language");
  });

  /**
   * Verifies that the registration page shows German password requirements and
   * does not leak the previous hardcoded English requirement strings.
   */
  it("renders password requirements in German", () => {
    renderRegisterPage();

    expect(screen.getByText("Mindestens 8 Zeichen")).toBeInTheDocument();
    expect(screen.getByText("Mindestens 1 Großbuchstabe")).toBeInTheDocument();
    expect(screen.getByText("Mindestens 1 Ziffer")).toBeInTheDocument();
    expect(screen.getByText("Mindestens 1 Sonderzeichen")).toBeInTheDocument();
    expect(screen.queryByText("Minimum 8 characters")).not.toBeInTheDocument();
  });

  /**
   * Verifies that known backend registration failures are presented with a
   * localized German message instead of exposing the raw English API detail.
   */
  it("localizes duplicate-email API errors", async () => {
    mockedRegisterUser.mockRejectedValue(
      new authApi.AuthApiError("Email already registered", "email-already-registered")
    );

    renderRegisterPage();
    fillValidRegistrationForm();

    const submitButton = screen.getByRole("button", { name: "Konto erstellen" });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => expect(mockedRegisterUser).toHaveBeenCalledTimes(1));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Diese E-Mail-Adresse ist bereits registriert."
    );
    expect(screen.queryByText("Email already registered")).not.toBeInTheDocument();
  });

  /**
   * Verifies that a valid registration form submission accepts the current
   * password example and continues to the verify-email route.
   */
  it("submits valid registration data and navigates to verify-email", async () => {
    mockedRegisterUser.mockResolvedValue({
      id: "user-1",
      email: "test4@test.de",
      username: "tes4",
      email_verified: false,
    });

    renderRegisterPage();
    fillValidRegistrationForm();

    const submitButton = screen.getByRole("button", { name: "Konto erstellen" });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => expect(mockedRegisterUser).toHaveBeenCalledTimes(1));
    expect(mockedRegisterUser).toHaveBeenCalledWith({
      email: "test4@test.de",
      username: "tes4",
      password: "sjdsfgJHKJB//%%8&&",
      acceptTerms: true,
      acceptPrivacy: true,
    });
    expect(await screen.findByText("verify-email-destination")).toBeInTheDocument();
    expect(screen.queryByText("Passwort erfüllt die Richtlinie nicht")).not.toBeInTheDocument();
  });
});