import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LanguageProvider } from "../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { UploadWizardPage } from "./UploadWizardPage";

vi.mock("../../shared/api/upload", () => {
  return {
    uploadNanoZip: vi.fn(),
    updateNanoMetadata: vi.fn(),
    publishNano: vi.fn(),
  };
});

afterEach(() => {
  vi.clearAllMocks();
});

function renderPage(): void {
  const authValue: AuthContextValue = {
    isLoading: false,
    isAuthenticated: true,
    user: { email: "creator@test.de", role: "creator" },
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
  };

  render(
    <LanguageProvider>
      <AuthContext.Provider value={authValue}>
        <MemoryRouter>
          <UploadWizardPage />
        </MemoryRouter>
      </AuthContext.Provider>
    </LanguageProvider>
  );
}

describe("UploadWizardPage", () => {
  it("renders step labels and upload CTA", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Nano hochladen" })).toBeTruthy();
    expect(screen.getByText("1. ZIP")).toBeTruthy();
    expect(screen.getByText("2. Metadaten")).toBeTruthy();
    expect(screen.getByText("3. Veröffentlichen")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Upload starten" })).toBeTruthy();
  });

  it("shows an inline validation error when upload starts without file", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Upload starten" }));

    expect(screen.getByText("Bitte wählen Sie zuerst eine ZIP-Datei aus.")).toBeTruthy();
  });
});
