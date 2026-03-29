import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as sharedApi from "../../shared/api";
import { LanguageProvider } from "../../shared/i18n";
import { AuthContext, type AuthContextValue } from "../auth/AuthContext";
import { AdminPanelPage } from "./AdminPanelPage";

vi.mock("../../shared/api", async () => {
  const actual = await vi.importActual<typeof import("../../shared/api")>("../../shared/api");
  return {
    ...actual,
    adminTakedownNano: vi.fn(),
    getAdminAuditLogs: vi.fn(),
    getAdminModerationQueue: vi.fn(),
    getAdminUsers: vi.fn(),
    reviewModerationCase: vi.fn(),
    updateAdminUserRole: vi.fn(),
  };
});

const mockedGetAdminUsers = vi.mocked(sharedApi.getAdminUsers);
const mockedUpdateAdminUserRole = vi.mocked(sharedApi.updateAdminUserRole);
const mockedGetAdminAuditLogs = vi.mocked(sharedApi.getAdminAuditLogs);
const mockedGetAdminModerationQueue = vi.mocked(sharedApi.getAdminModerationQueue);
const mockedReviewModerationCase = vi.mocked(sharedApi.reviewModerationCase);
const mockedAdminTakedownNano = vi.mocked(sharedApi.adminTakedownNano);

const baseUsers = {
  users: [
    {
      id: "user-1",
      email: "creator@example.com",
      username: "creator-1",
      firstName: "Ada",
      lastName: "Lovelace",
      bio: null,
      preferredLanguage: "de",
      status: "active" as const,
      role: "creator" as const,
      emailVerified: true,
      verifiedAt: "2026-03-29T09:00:00Z",
      createdAt: "2026-03-10T09:00:00Z",
      updatedAt: "2026-03-10T09:00:00Z",
      lastLogin: "2026-03-29T10:00:00Z",
      profileAvatar: null,
      company: null,
      jobTitle: null,
      phone: null,
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const baseAuditLogs = {
  logs: [
    {
      id: "audit-1",
      userId: "admin-1",
      action: "role_changed",
      resourceType: "user",
      resourceId: "user-1",
      metadata: { old_role: "creator", new_role: "moderator" },
      ipAddress: "127.0.0.1",
      userAgent: "Vitest",
      createdAt: "2026-03-29T11:00:00Z",
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const baseModeration = {
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
    pageSize: 10,
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
    <LanguageProvider>
      <AuthContext.Provider value={value}>
        <AdminPanelPage />
      </AuthContext.Provider>
    </LanguageProvider>,
  );
}

describe("AdminPanelPage", () => {
  beforeEach(() => {
    mockedGetAdminUsers.mockReset();
    mockedUpdateAdminUserRole.mockReset();
    mockedGetAdminAuditLogs.mockReset();
    mockedGetAdminModerationQueue.mockReset();
    mockedReviewModerationCase.mockReset();
    mockedAdminTakedownNano.mockReset();

    mockedGetAdminUsers.mockResolvedValue(baseUsers);
    mockedGetAdminAuditLogs.mockResolvedValue(baseAuditLogs);
    mockedGetAdminModerationQueue.mockResolvedValue(baseModeration);
  });

  it("loads the admin sections and renders fetched data", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Admin-Konsole" })).toBeTruthy();
    });

    expect(screen.getByText("creator-1")).toBeTruthy();
    expect(screen.getByText("role_changed")).toBeTruthy();
    expect(screen.getByText("Potentially problematic comment")).toBeTruthy();
  });

  it("updates a user role from the admin panel", async () => {
    mockedUpdateAdminUserRole.mockResolvedValue({
      ...baseUsers.users[0],
      role: "moderator",
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByDisplayValue("Creator")).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText("Rolle creator-1"), { target: { value: "moderator" } });
    fireEvent.click(screen.getByRole("button", { name: "Rolle speichern" }));

    await waitFor(() => {
      expect(mockedUpdateAdminUserRole).toHaveBeenCalledWith("user-1", "moderator");
    });

    expect(screen.getByText("Rolle wurde aktualisiert.")).toBeTruthy();
  });

  it("submits moderation decisions and takedown actions", async () => {
    mockedReviewModerationCase.mockResolvedValue(baseModeration.items[0]);
    mockedAdminTakedownNano.mockResolvedValue({
      nanoId: "nano-7",
      oldStatus: "published",
      newStatus: "archived",
      alreadyRemoved: false,
      takedownReason: "Policy breach",
      takenDownAt: "2026-03-29T11:00:00Z",
      message: "done",
    });

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

  it("shows a forbidden error state when admin APIs reject access", async () => {
    mockedGetAdminUsers.mockRejectedValue(new sharedApi.AdminApiError("Forbidden", "forbidden"));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Sie haben keine Berechtigung für diese Aktion.")).toBeTruthy();
    });
  });

  it("keeps open moderation summary independent from active moderation filters", async () => {
    mockedGetAdminModerationQueue.mockImplementation(async (params = {}) => {
      const isSummaryCall = params.contentType === "all" && params.status === "pending" && params.limit === 1;
      if (isSummaryCall) {
        return {
          ...baseModeration,
          pagination: {
            ...baseModeration.pagination,
            totalResults: 6,
          },
        };
      }

      if (params.contentType === "nano_comment") {
        return {
          ...baseModeration,
          pagination: {
            ...baseModeration.pagination,
            totalResults: 1,
          },
        };
      }

      return {
        ...baseModeration,
        pagination: {
          ...baseModeration.pagination,
          totalResults: 6,
        },
      };
    });

    renderPage();

    await waitFor(() => {
      expect(mockedGetAdminModerationQueue).toHaveBeenCalled();
    });

    const moderationSummaryCard = screen.getByText("Offene Moderationsfälle").closest("article");
    expect(moderationSummaryCard).toBeTruthy();
    expect(within(moderationSummaryCard as HTMLElement).getByText("6")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Inhaltstyp"), {
      target: { value: "nano_comment" },
    });

    const applyFilterButtons = screen.getAllByRole("button", { name: "Filter anwenden" });
    fireEvent.click(applyFilterButtons[2]);

    await waitFor(() => {
      expect(mockedGetAdminModerationQueue).toHaveBeenCalledWith(
        expect.objectContaining({
          contentType: "nano_comment",
          status: "pending",
          page: 1,
          limit: 10,
        }),
      );
    });

    expect(within(moderationSummaryCard as HTMLElement).getByText("6")).toBeTruthy();
    const moderationSection = screen
      .getByRole("heading", { name: "Moderation & Takedown" })
      .closest("section");
    expect(moderationSection).toBeTruthy();
    expect(within(moderationSection as HTMLElement).getByText("Gesamt: 1")).toBeTruthy();
  });
});