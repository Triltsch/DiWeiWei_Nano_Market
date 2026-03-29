import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as sharedApi from "../../shared/api";
import { LanguageProvider } from "../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { ModeratorQueuePage } from "./ModeratorQueuePage";

vi.mock("../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../shared/api")>("../../shared/api");
  return {
    ...actual,
    adminTakedownNano: vi.fn(),
    getAdminModerationQueue: vi.fn(),
    reviewModerationCase: vi.fn(),
  };
});

const mockedGetAdminModerationQueue = vi.mocked(sharedApi.getAdminModerationQueue);
const mockedReviewModerationCase = vi.mocked(sharedApi.reviewModerationCase);
const mockedAdminTakedownNano = vi.mocked(sharedApi.adminTakedownNano);

const baseModerationResponse = {
  items: [
    {
      caseId: "case-1",
      contentType: "nano_comment" as const,
      contentId: "comment-1",
      reporterId: null,
      status: "pending" as const,
      reason: null,
      decidedByUserId: null,
      decidedAt: null,
      deferredUntil: null,
      escalationNote: null,
      createdAt: "2026-03-29T08:00:00Z",
      updatedAt: "2026-03-29T08:00:00Z",
      contentDetail: {
        nanoId: "nano-7",
        content: "Potentially problematic comment",
        authorUsername: "reader-1",
        moderationStatus: "pending",
        createdAt: "2026-03-29T08:00:00Z",
      },
    },
  ],
  pagination: {
    currentPage: 1,
    pageSize: 20,
    totalResults: 1,
    totalPages: 1,
    hasNextPage: false,
    hasPrevPage: false,
  },
};

function renderPage(authValue?: Partial<AuthContextValue>): void {
  const value: AuthContextValue = {
    isLoading: false,
    isAuthenticated: true,
    user: {
      id: "admin-1",
      email: "admin@example.com",
      username: "admin",
      role: "admin",
    },
    login: async () => Promise.resolve(),
    logout: async () => Promise.resolve(),
    ...authValue,
  };

  render(
    <MemoryRouter>
      <LanguageProvider>
        <AuthContext.Provider value={value}>
          <ModeratorQueuePage />
        </AuthContext.Provider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

describe("ModeratorQueuePage", () => {
  beforeEach(() => {
    mockedGetAdminModerationQueue.mockReset();
    mockedReviewModerationCase.mockReset();
    mockedAdminTakedownNano.mockReset();

    mockedGetAdminModerationQueue.mockResolvedValue(baseModerationResponse);
    mockedReviewModerationCase.mockResolvedValue(baseModerationResponse.items[0]);
    mockedAdminTakedownNano.mockResolvedValue({
      nanoId: "nano-7",
      oldStatus: "published",
      newStatus: "archived",
      alreadyRemoved: false,
      takedownReason: "Policy breach",
      takenDownAt: "2026-03-29T11:00:00Z",
      message: "done",
    });
  });

  it("loads queue from case-based moderation API and applies filters", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Potentially problematic comment")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Inhaltstyp"), { target: { value: "nano_comment" } });
    fireEvent.click(screen.getByRole("button", { name: "Filter anwenden" }));

    await waitFor(() => {
      expect(mockedGetAdminModerationQueue).toHaveBeenCalledWith(
        expect.objectContaining({
          contentType: "nano_comment",
          status: "pending",
          page: 1,
          limit: 20,
        }),
      );
    });
  });

  it("supports moderation decision and takedown for admins", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Potentially problematic comment")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Entscheidungsbegründung"), {
      target: { value: "Policy breach" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Ablehnen" }));

    await waitFor(() => {
      expect(mockedReviewModerationCase).toHaveBeenCalledWith(
        "case-1",
        expect.objectContaining({ decision: "reject", reason: "Policy breach" }),
      );
    });

    fireEvent.change(screen.getByLabelText("Entscheidungsbegründung"), {
      target: { value: "Policy breach" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Takedown auslösen" }));

    await waitFor(() => {
      expect(mockedAdminTakedownNano).toHaveBeenCalledWith(
        "nano-7",
        "Policy breach",
        expect.stringContaining("case-1"),
      );
    });
  });

  it("hides takedown action for non-admin moderators", async () => {
    renderPage({
      user: {
        id: "moderator-1",
        email: "moderator@example.com",
        username: "moderator",
        role: "moderator",
      },
    });

    await waitFor(() => {
      expect(screen.getByText("Potentially problematic comment")).toBeTruthy();
    });

    expect(screen.queryByRole("button", { name: "Takedown auslösen" })).toBeNull();
  });
});
