/**
 * Report control: open modal, submit, already-reported, own-nano hidden.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi, type ComponentProps } from "vitest";

import * as nanoFlagsApi from "../../../shared/api/nanoFlags";
import { LanguageProvider, useLanguage } from "../../../shared/i18n";
import { ReportNanoControl } from "./ReportNanoControl";

vi.mock("../../../shared/api/nanoFlags", async () => {
  const actual = await vi.importActual<typeof import("../../../shared/api/nanoFlags")>(
    "../../../shared/api/nanoFlags"
  );
  return {
    ...actual,
    createNanoFlag: vi.fn(),
    getMyNanoFlag: vi.fn(),
  };
});

const mockedCreateNanoFlag = vi.mocked(nanoFlagsApi.createNanoFlag);
const mockedGetMyNanoFlag = vi.mocked(nanoFlagsApi.getMyNanoFlag);

const defaultFlag = {
  id: "flag-1",
  nanoId: "nano-1",
  flaggingUserId: "user-1",
  reason: "spam" as const,
  comment: null,
  status: "pending",
  createdAt: "2026-03-20T12:00:00Z",
  reviewedAt: null,
  moderatorId: null,
};

function renderControl(
  props?: Partial<ComponentProps<typeof ReportNanoControl>>
): { onRequireLogin: ReturnType<typeof vi.fn> } {
  const onRequireLogin = vi.fn();
  render(
    <LanguageProvider>
      <ReportNanoControl
        nanoId="nano-1"
        creatorId="creator-1"
        isPublished
        isAuthenticated
        currentUserId="user-1"
        onRequireLogin={onRequireLogin}
        {...props}
      />
    </LanguageProvider>
  );
  return { onRequireLogin };
}

describe("ReportNanoControl", () => {
  beforeEach(() => {
    mockedCreateNanoFlag.mockReset();
    mockedGetMyNanoFlag.mockReset();
    mockedGetMyNanoFlag.mockResolvedValue(null);
    window.localStorage.removeItem("diwei_ui_language");
  });

  it("opens the modal, submits a report, and shows a success toast", async () => {
    mockedCreateNanoFlag.mockResolvedValue(defaultFlag);
    renderControl();

    fireEvent.click(await screen.findByRole("button", { name: "Diese Nano melden" }));
    expect(screen.getByRole("dialog", { name: "Unangemessenen Inhalt melden" })).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Grund"), { target: { value: "spam" } });
    fireEvent.click(screen.getByRole("button", { name: "Meldung absenden" }));

    await waitFor(() => {
      expect(mockedCreateNanoFlag).toHaveBeenCalledWith("nano-1", { reason: "spam", comment: "" });
      expect(screen.getByRole("status").textContent).toBe(
        "Danke für Ihre Meldung. Die Moderation prüft sie in Kürze."
      );
    });

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("button", { name: "Bereits gemeldet" })).toBeTruthy();
  });

  it("keeps the modal open and shows an error toast when submit fails", async () => {
    mockedCreateNanoFlag.mockRejectedValue(new nanoFlagsApi.NanoFlagApiError("boom", "request-failed"));
    renderControl();

    fireEvent.click(await screen.findByRole("button", { name: "Diese Nano melden" }));
    fireEvent.change(screen.getByLabelText("Grund"), { target: { value: "other" } });
    fireEvent.click(screen.getByRole("button", { name: "Meldung absenden" }));

    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toBe(
        "Meldung konnte nicht gesendet werden. Bitte erneut versuchen.",
      );
      expect(screen.getByRole("dialog")).toBeTruthy();
    });
  });

  it("shows a disabled already-reported button when my-flag exists", async () => {
    mockedGetMyNanoFlag.mockResolvedValue(defaultFlag);
    renderControl();

    const button = await screen.findByRole("button", { name: "Bereits gemeldet" });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    expect(button.getAttribute("title")).toBe(
      "Sie haben diese Nano bereits gemeldet (Prüfung ausstehend)",
    );
  });

  it("does not render a report action on the creator's own nano", () => {
    renderControl({ currentUserId: "creator-1" });
    expect(screen.queryByRole("button", { name: "Diese Nano melden" })).toBeNull();
  });

  it("redirects unauthenticated users instead of opening the modal", async () => {
    const { onRequireLogin } = renderControl({ isAuthenticated: false, currentUserId: undefined });

    fireEvent.click(await screen.findByRole("button", { name: "Diese Nano melden" }));
    expect(onRequireLogin).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("switches the report button label when the UI language changes", async () => {
    function LanguageToggle(): JSX.Element {
      const { setLanguage } = useLanguage();
      return (
        <button type="button" onClick={() => setLanguage("en")}>
          Switch to English
        </button>
      );
    }

    const onRequireLogin = vi.fn();
    render(
      <LanguageProvider>
        <LanguageToggle />
        <ReportNanoControl
          nanoId="nano-1"
          creatorId="creator-1"
          isPublished
          isAuthenticated
          currentUserId="user-1"
          onRequireLogin={onRequireLogin}
        />
      </LanguageProvider>,
    );

    expect(await screen.findByRole("button", { name: "Diese Nano melden" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Switch to English" }));
    expect(screen.getByRole("button", { name: "Report This Nano" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Diese Nano melden" })).toBeNull();
  });
});
