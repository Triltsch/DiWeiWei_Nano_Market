import { useEffect, useState } from "react";

import {
  AdminApiError,
  adminTakedownNano,
  deleteAdminUser,
  getAdminAuditLogs,
  getAdminModerationQueue,
  getAdminUsers,
  reviewModerationCase,
  updateAdminUserRole,
  type AdminUser,
  type AdminUserStatus,
  type AuditLogItem,
  type ModerationCaseItem,
  type ModerationCaseStatus,
  type ModerationContentType,
} from "../../shared/api";
import type { AuthRole } from "../../shared/api/types";
import { useTranslation } from "../../shared/i18n";

const USER_PAGE_SIZE = 10;
const AUDIT_PAGE_SIZE = 10;
const MODERATION_PAGE_SIZE = 10;

type SectionError = string | null;

interface ModerationDraft {
  reason: string;
  deferredUntil: string;
}

function formatDateTime(value: string | null, locale: string): string {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function getAdminErrorMessage(error: unknown, fallback: string, forbidden: string, unauthorized: string): string {
  if (error instanceof AdminApiError) {
    if (error.code === "forbidden") {
      return forbidden;
    }
    if (error.code === "unauthorized") {
      return unauthorized;
    }
    return error.message || fallback;
  }

  return fallback;
}

function getRoleLabel(role: AuthRole, t: ReturnType<typeof useTranslation>["t"]): string {
  if (role === "admin") {
    return t("admin_user_role_admin");
  }
  if (role === "moderator") {
    return t("admin_user_role_moderator");
  }
  if (role === "creator") {
    return t("admin_user_role_creator");
  }
  return t("admin_user_role_consumer");
}

function getUserStatusLabel(status: AdminUserStatus, t: ReturnType<typeof useTranslation>["t"]): string {
  if (status === "suspended") {
    return t("admin_user_status_suspended");
  }
  if (status === "inactive") {
    return t("admin_user_status_inactive");
  }
  if (status === "deleted") {
    return t("admin_user_status_deleted");
  }
  return t("admin_user_status_active");
}

function getContentTypeLabel(
  value: ModerationContentType,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (value === "nano_rating") {
    return t("admin_moderation_content_type_rating");
  }
  if (value === "nano_comment") {
    return t("admin_moderation_content_type_comment");
  }
  return t("admin_moderation_content_type_nano");
}

function getCaseStatusLabel(
  value: ModerationCaseStatus,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (value === "approved") {
    return t("admin_moderation_status_approved");
  }
  if (value === "rejected") {
    return t("admin_moderation_status_rejected");
  }
  if (value === "deferred") {
    return t("admin_moderation_status_deferred");
  }
  if (value === "escalated") {
    return t("admin_moderation_status_escalated");
  }
  return t("admin_moderation_status_pending");
}

function getModerationNanoId(item: ModerationCaseItem): string | null {
  if (item.contentType === "nano") {
    return item.contentId;
  }
  if (item.contentDetail && "nanoId" in item.contentDetail) {
    return item.contentDetail.nanoId;
  }
  return null;
}

function getModerationSummary(item: ModerationCaseItem, t: ReturnType<typeof useTranslation>["t"]): string {
  if (!item.contentDetail) {
    return t("admin_moderation_missing_content");
  }

  if (item.contentType === "nano") {
    return item.contentDetail.title;
  }

  if (item.contentType === "nano_rating") {
    return `${item.contentDetail.score}/5`;
  }

  return item.contentDetail.content;
}

function getModerationMeta(item: ModerationCaseItem, t: ReturnType<typeof useTranslation>["t"]): string {
  if (!item.contentDetail) {
    return t("admin_moderation_missing_content");
  }

  if (item.contentType === "nano") {
    return item.contentDetail.creatorUsername ?? t("search_creator_fallback");
  }

  return item.contentDetail.authorUsername ?? t("search_creator_fallback");
}

function getInitialDrafts(items: ModerationCaseItem[]): Record<string, ModerationDraft> {
  const nextDrafts: Record<string, ModerationDraft> = {};
  for (const item of items) {
    nextDrafts[item.caseId] = {
      reason: item.reason ?? "",
      deferredUntil: item.deferredUntil ? item.deferredUntil.slice(0, 16) : "",
    };
  }
  return nextDrafts;
}

export function AdminPanelPage(): JSX.Element {
  const { t, language } = useTranslation();
  const locale = language === "de" ? "de-DE" : "en-US";

  const [userSearch, setUserSearch] = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState<AuthRole | "all">("all");
  const [userStatusFilter, setUserStatusFilter] = useState<AdminUserStatus | "all">("all");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [userTotal, setUserTotal] = useState(0);
  const [userOffset, setUserOffset] = useState(0);
  const [usersLoading, setUsersLoading] = useState(true);
  const [usersError, setUsersError] = useState<SectionError>(null);
  const [userMessage, setUserMessage] = useState<string | null>(null);
  const [userRoleDrafts, setUserRoleDrafts] = useState<Record<string, AuthRole>>({});
  const [userRolePending, setUserRolePending] = useState<Record<string, boolean>>({});
  const [userDeletePending, setUserDeletePending] = useState<Record<string, boolean>>({});

  const [auditActionFilter, setAuditActionFilter] = useState("");
  const [auditResourceTypeFilter, setAuditResourceTypeFilter] = useState("");
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditOffset, setAuditOffset] = useState(0);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditError, setAuditError] = useState<SectionError>(null);

  const [moderationContentTypeFilter, setModerationContentTypeFilter] = useState<
    ModerationContentType | "all"
  >("all");
  const [moderationStatusFilter, setModerationStatusFilter] = useState<
    ModerationCaseStatus | "all"
  >("pending");
  const [moderationItems, setModerationItems] = useState<ModerationCaseItem[]>([]);
  const [moderationPage, setModerationPage] = useState(1);
  const [moderationTotal, setModerationTotal] = useState(0);
  const [moderationOpenTotal, setModerationOpenTotal] = useState(0);
  const [moderationLoading, setModerationLoading] = useState(true);
  const [moderationError, setModerationError] = useState<SectionError>(null);
  const [moderationMessage, setModerationMessage] = useState<string | null>(null);
  const [moderationDrafts, setModerationDrafts] = useState<Record<string, ModerationDraft>>({});
  const [moderationPending, setModerationPending] = useState<Record<string, boolean>>({});
  const [takedownPending, setTakedownPending] = useState<Record<string, boolean>>({});

  const loadUsers = async (nextOffset = 0): Promise<void> => {
    setUsersLoading(true);
    setUsersError(null);

    try {
      const response = await getAdminUsers({
        search: userSearch,
        role: userRoleFilter,
        status: userStatusFilter,
        limit: USER_PAGE_SIZE,
        offset: nextOffset,
      });
      setUsers(response.users);
      setUserTotal(response.total);
      setUserOffset(response.offset);
      setUserRoleDrafts(
        Object.fromEntries(response.users.map((user) => [user.id, user.role])) as Record<string, AuthRole>,
      );
    } catch (error) {
      setUsersError(
        getAdminErrorMessage(
          error,
          t("admin_users_load_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setUsersLoading(false);
    }
  };

  const loadAuditLogs = async (nextOffset = 0): Promise<void> => {
    setAuditLoading(true);
    setAuditError(null);

    try {
      const response = await getAdminAuditLogs({
        action: auditActionFilter,
        resourceType: auditResourceTypeFilter,
        limit: AUDIT_PAGE_SIZE,
        offset: nextOffset,
      });
      setAuditLogs(response.logs);
      setAuditTotal(response.total);
      setAuditOffset(response.offset);
    } catch (error) {
      setAuditError(
        getAdminErrorMessage(
          error,
          t("admin_audit_load_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setAuditLoading(false);
    }
  };

  const loadModerationQueue = async (nextPage = 1): Promise<void> => {
    setModerationLoading(true);
    setModerationError(null);

    try {
      const response = await getAdminModerationQueue({
        contentType: moderationContentTypeFilter,
        status: moderationStatusFilter,
        page: nextPage,
        limit: MODERATION_PAGE_SIZE,
      });
      setModerationItems(response.items);
      setModerationPage(response.pagination.currentPage);
      setModerationTotal(response.pagination.totalResults);
      setModerationDrafts(getInitialDrafts(response.items));
    } catch (error) {
      setModerationError(
        getAdminErrorMessage(
          error,
          t("admin_moderation_load_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setModerationLoading(false);
    }
  };

  const loadModerationOpenTotal = async (): Promise<void> => {
    try {
      const response = await getAdminModerationQueue({
        contentType: "all",
        status: "pending",
        page: 1,
        limit: 1,
      });
      setModerationOpenTotal(response.pagination.totalResults);
    } catch {
      // Keep the previous KPI value when summary refresh fails.
    }
  };

  useEffect(() => {
    const loadInitialData = async (): Promise<void> => {
      await Promise.all([
        loadUsers(0),
        loadAuditLogs(0),
        loadModerationQueue(1),
        loadModerationOpenTotal(),
      ]);
    };

    void loadInitialData();
  }, []);

  const handleRoleDraftChange = (userId: string, role: AuthRole): void => {
    setUserRoleDrafts((current) => ({ ...current, [userId]: role }));
  };

  const handleSaveRole = async (userId: string): Promise<void> => {
    const nextRole = userRoleDrafts[userId];
    const currentUser = users.find((user) => user.id === userId);
    if (!nextRole || !currentUser || currentUser.role === nextRole) {
      return;
    }

    setUserMessage(null);
    setUserRolePending((current) => ({ ...current, [userId]: true }));
    try {
      const updatedUser = await updateAdminUserRole(userId, nextRole);
      setUsers((current) => current.map((user) => (user.id === userId ? updatedUser : user)));
      setUserRoleDrafts((current) => ({ ...current, [userId]: updatedUser.role }));
      setUserMessage(t("admin_users_role_update_success"));
      void loadAuditLogs(auditOffset);
    } catch (error) {
      setUsersError(
        getAdminErrorMessage(
          error,
          t("admin_users_role_update_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setUserRolePending((current) => ({ ...current, [userId]: false }));
    }
  };

  const handleDeleteUser = async (userId: string): Promise<void> => {
    const currentUser = users.find((user) => user.id === userId);
    if (!currentUser) {
      return;
    }

    const confirmed = window.confirm(
      `${t("admin_users_delete_confirm_prefix")} ${currentUser.username}?`,
    );
    if (!confirmed) {
      return;
    }

    setUserMessage(null);
    setUserDeletePending((current) => ({ ...current, [userId]: true }));
    try {
      await deleteAdminUser(userId);
      setUserMessage(t("admin_users_delete_success"));
      await Promise.all([loadUsers(0), loadAuditLogs(auditOffset)]);
    } catch (error) {
      setUsersError(
        getAdminErrorMessage(
          error,
          t("admin_users_delete_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setUserDeletePending((current) => ({ ...current, [userId]: false }));
    }
  };

  const handleModerationDraftChange = (caseId: string, field: keyof ModerationDraft, value: string): void => {
    setModerationDrafts((current) => ({
      ...current,
      [caseId]: {
        reason: current[caseId]?.reason ?? "",
        deferredUntil: current[caseId]?.deferredUntil ?? "",
        [field]: value,
      },
    }));
  };

  const handleModerationAction = async (
    item: ModerationCaseItem,
    decision: "approve" | "reject" | "defer" | "escalate",
  ): Promise<void> => {
    const draft = moderationDrafts[item.caseId] ?? { reason: "", deferredUntil: "" };
    const trimmedReason = draft.reason.trim();

    if ((decision === "reject" || decision === "defer" || decision === "escalate") && !trimmedReason) {
      setModerationError(t("admin_moderation_reason_required"));
      return;
    }

    if (decision === "defer" && !draft.deferredUntil) {
      setModerationError(t("admin_moderation_deferred_until_required"));
      return;
    }

    setModerationError(null);
    setModerationMessage(null);
    setModerationPending((current) => ({ ...current, [item.caseId]: true }));

    try {
      await reviewModerationCase(item.caseId, {
        decision,
        reason: trimmedReason || undefined,
        deferredUntil: draft.deferredUntil ? new Date(draft.deferredUntil).toISOString() : undefined,
      });
      setModerationMessage(t("admin_moderation_action_success"));
      await Promise.all([
        loadModerationQueue(moderationPage),
        loadAuditLogs(auditOffset),
        loadModerationOpenTotal(),
      ]);
    } catch (error) {
      setModerationError(
        getAdminErrorMessage(
          error,
          t("admin_moderation_action_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setModerationPending((current) => ({ ...current, [item.caseId]: false }));
    }
  };

  const handleTakedown = async (item: ModerationCaseItem): Promise<void> => {
    const nanoId = getModerationNanoId(item);
    const draft = moderationDrafts[item.caseId] ?? { reason: "", deferredUntil: "" };
    const trimmedReason = draft.reason.trim();

    if (!nanoId) {
      setModerationError(t("admin_takedown_not_available"));
      return;
    }

    if (!trimmedReason) {
      setModerationError(t("admin_takedown_reason_required"));
      return;
    }

    setModerationError(null);
    setModerationMessage(null);
    setTakedownPending((current) => ({ ...current, [item.caseId]: true }));

    try {
      await adminTakedownNano(nanoId, trimmedReason, `${t("admin_takedown_note_prefix")} ${item.caseId}`);
      setModerationMessage(t("admin_takedown_success"));
      await Promise.all([
        loadModerationQueue(moderationPage),
        loadAuditLogs(auditOffset),
        loadModerationOpenTotal(),
      ]);
    } catch (error) {
      setModerationError(
        getAdminErrorMessage(
          error,
          t("admin_takedown_error"),
          t("auth_error_forbidden"),
          t("auth_error_unauthorized"),
        ),
      );
    } finally {
      setTakedownPending((current) => ({ ...current, [item.caseId]: false }));
    }
  };

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-neutral-200 bg-gradient-to-br from-white via-primary-50 to-secondary-50 p-6 shadow-sm">
        <div className="space-y-3">
          <span className="inline-flex rounded-full bg-primary-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-primary-700">
            {t("admin_badge")}
          </span>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-neutral-950">{t("admin_title")}</h1>
            <p className="max-w-3xl text-sm text-neutral-700">{t("admin_description")}</p>
          </div>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-medium text-neutral-500">{t("admin_summary_users")}</p>
          <p className="mt-2 text-3xl font-semibold text-neutral-900">{userTotal}</p>
        </article>
        <article className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-medium text-neutral-500">{t("admin_summary_audit")}</p>
          <p className="mt-2 text-3xl font-semibold text-neutral-900">{auditTotal}</p>
        </article>
        <article className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-medium text-neutral-500">{t("admin_summary_moderation")}</p>
          <p className="mt-2 text-3xl font-semibold text-neutral-900">{moderationOpenTotal}</p>
        </article>
      </section>

      <section className="rounded-3xl border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-neutral-950">{t("admin_users_title")}</h2>
            <p className="text-sm text-neutral-600">{t("admin_users_description")}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_users_search_label")}</span>
              <input
                value={userSearch}
                onChange={(event) => setUserSearch(event.target.value)}
                placeholder={t("admin_users_search_placeholder")}
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              />
            </label>
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_users_role_filter_label")}</span>
              <select
                value={userRoleFilter}
                onChange={(event) => setUserRoleFilter(event.target.value as AuthRole | "all")}
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              >
                <option value="all">{t("admin_filter_all_roles")}</option>
                <option value="consumer">{t("admin_user_role_consumer")}</option>
                <option value="creator">{t("admin_user_role_creator")}</option>
                <option value="moderator">{t("admin_user_role_moderator")}</option>
                <option value="admin">{t("admin_user_role_admin")}</option>
              </select>
            </label>
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_users_status_filter_label")}</span>
              <select
                value={userStatusFilter}
                onChange={(event) =>
                  setUserStatusFilter(event.target.value as AdminUserStatus | "all")
                }
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              >
                <option value="all">{t("admin_filter_all_statuses")}</option>
                <option value="active">{t("admin_user_status_active")}</option>
                <option value="inactive">{t("admin_user_status_inactive")}</option>
                <option value="suspended">{t("admin_user_status_suspended")}</option>
                <option value="deleted">{t("admin_user_status_deleted")}</option>
              </select>
            </label>
            <button
              onClick={() => void loadUsers(0)}
              className="rounded-xl bg-primary-600 px-4 py-2 font-medium text-white transition hover:bg-primary-700"
            >
              {t("admin_apply_filters")}
            </button>
          </div>
        </div>

        {userMessage && (
          <p className="mt-4 rounded-xl border border-success-200 bg-success-50 px-3 py-2 text-sm text-success-700">
            {userMessage}
          </p>
        )}
        {usersError && (
          <p role="alert" className="mt-4 rounded-xl border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">
            {usersError}
          </p>
        )}

        {usersLoading ? (
          <p role="status" className="mt-4 text-sm text-neutral-500">{t("admin_users_loading")}</p>
        ) : users.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-500">{t("admin_users_empty")}</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-y-2 text-left text-sm">
              <thead>
                <tr className="text-neutral-500">
                  <th className="px-3 py-2">{t("admin_users_table_identity")}</th>
                  <th className="px-3 py-2">{t("admin_users_table_status")}</th>
                  <th className="px-3 py-2">{t("admin_users_table_role")}</th>
                  <th className="px-3 py-2">{t("admin_users_table_last_login")}</th>
                  <th className="px-3 py-2">{t("admin_users_table_actions")}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const draftRole = userRoleDrafts[user.id] ?? user.role;
                  const isSaving = userRolePending[user.id] === true;
                  const isDeleting = userDeletePending[user.id] === true;
                  const isChanged = draftRole !== user.role;

                  return (
                    <tr key={user.id} className="rounded-2xl bg-neutral-50 text-neutral-800">
                      <td className="rounded-l-2xl px-3 py-3 align-top">
                        <div className="font-medium text-neutral-950">{user.username}</div>
                        <div className="text-neutral-600">{user.email}</div>
                        <div className="text-xs text-neutral-500">
                          {user.firstName || user.lastName
                            ? `${user.firstName ?? ""} ${user.lastName ?? ""}`.trim()
                            : t("admin_users_identity_fallback")}
                        </div>
                      </td>
                      <td className="px-3 py-3 align-top">
                        <div>{getUserStatusLabel(user.status, t)}</div>
                        <div className="text-xs text-neutral-500">
                          {user.emailVerified
                            ? t("admin_users_verified_yes")
                            : t("admin_users_verified_no")}
                        </div>
                      </td>
                      <td className="px-3 py-3 align-top">
                        <select
                          value={draftRole}
                          onChange={(event) => handleRoleDraftChange(user.id, event.target.value as AuthRole)}
                          className="w-full rounded-xl border border-neutral-300 px-3 py-2"
                          aria-label={`${t("admin_users_table_role")} ${user.username}`}
                        >
                          <option value="consumer">{t("admin_user_role_consumer")}</option>
                          <option value="creator">{t("admin_user_role_creator")}</option>
                          <option value="moderator">{t("admin_user_role_moderator")}</option>
                          <option value="admin">{t("admin_user_role_admin")}</option>
                        </select>
                        <div className="mt-2 text-xs text-neutral-500">{getRoleLabel(user.role, t)}</div>
                      </td>
                      <td className="px-3 py-3 align-top text-neutral-600">
                        {formatDateTime(user.lastLogin, locale)}
                      </td>
                      <td className="rounded-r-2xl px-3 py-3 align-top">
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => void handleSaveRole(user.id)}
                            disabled={!isChanged || isSaving || isDeleting}
                            className="rounded-xl bg-neutral-900 px-4 py-2 font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {isSaving ? t("admin_users_saving") : t("admin_users_save_role")}
                          </button>
                          <button
                            onClick={() => void handleDeleteUser(user.id)}
                            disabled={isSaving || isDeleting || user.status === "deleted"}
                            className="rounded-xl bg-error-600 px-4 py-2 font-medium text-white transition hover:bg-error-700 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {isDeleting ? t("admin_users_deleting") : t("admin_users_delete")}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 flex items-center justify-between text-sm text-neutral-600">
          <span>{t("admin_pagination_results_prefix")} {userTotal}</span>
          <div className="flex gap-2">
            <button
              onClick={() => void loadUsers(Math.max(userOffset - USER_PAGE_SIZE, 0))}
              disabled={userOffset === 0 || usersLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_previous")}
            </button>
            <button
              onClick={() => void loadUsers(userOffset + USER_PAGE_SIZE)}
              disabled={userOffset + USER_PAGE_SIZE >= userTotal || usersLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_next")}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-neutral-950">{t("admin_audit_title")}</h2>
            <p className="text-sm text-neutral-600">{t("admin_audit_description")}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_audit_action_filter_label")}</span>
              <input
                value={auditActionFilter}
                onChange={(event) => setAuditActionFilter(event.target.value)}
                placeholder={t("admin_audit_action_filter_placeholder")}
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              />
            </label>
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_audit_resource_filter_label")}</span>
              <input
                value={auditResourceTypeFilter}
                onChange={(event) => setAuditResourceTypeFilter(event.target.value)}
                placeholder={t("admin_audit_resource_filter_placeholder")}
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              />
            </label>
            <button
              onClick={() => void loadAuditLogs(0)}
              className="rounded-xl bg-primary-600 px-4 py-2 font-medium text-white transition hover:bg-primary-700"
            >
              {t("admin_apply_filters")}
            </button>
          </div>
        </div>

        {auditError && (
          <p role="alert" className="mt-4 rounded-xl border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">
            {auditError}
          </p>
        )}

        {auditLoading ? (
          <p role="status" className="mt-4 text-sm text-neutral-500">{t("admin_audit_loading")}</p>
        ) : auditLogs.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-500">{t("admin_audit_empty")}</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-y-2 text-left text-sm">
              <thead>
                <tr className="text-neutral-500">
                  <th className="px-3 py-2">{t("admin_audit_table_time")}</th>
                  <th className="px-3 py-2">{t("admin_audit_table_action")}</th>
                  <th className="px-3 py-2">{t("admin_audit_table_resource")}</th>
                  <th className="px-3 py-2">{t("admin_audit_table_context")}</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} className="rounded-2xl bg-neutral-50 text-neutral-800">
                    <td className="rounded-l-2xl px-3 py-3 align-top text-neutral-600">
                      {formatDateTime(log.createdAt, locale)}
                    </td>
                    <td className="px-3 py-3 align-top font-medium text-neutral-950">{log.action}</td>
                    <td className="px-3 py-3 align-top text-neutral-600">
                      {log.resourceType ?? "-"}
                      {log.resourceId ? <div className="text-xs text-neutral-500">{log.resourceId}</div> : null}
                    </td>
                    <td className="rounded-r-2xl px-3 py-3 align-top text-neutral-600">
                      {log.metadata ? JSON.stringify(log.metadata) : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 flex items-center justify-between text-sm text-neutral-600">
          <span>{t("admin_pagination_results_prefix")} {auditTotal}</span>
          <div className="flex gap-2">
            <button
              onClick={() => void loadAuditLogs(Math.max(auditOffset - AUDIT_PAGE_SIZE, 0))}
              disabled={auditOffset === 0 || auditLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_previous")}
            </button>
            <button
              onClick={() => void loadAuditLogs(auditOffset + AUDIT_PAGE_SIZE)}
              disabled={auditOffset + AUDIT_PAGE_SIZE >= auditTotal || auditLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_next")}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-neutral-950">{t("admin_moderation_title")}</h2>
            <p className="text-sm text-neutral-600">{t("admin_moderation_description")}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_moderation_content_filter_label")}</span>
              <select
                value={moderationContentTypeFilter}
                onChange={(event) =>
                  setModerationContentTypeFilter(event.target.value as ModerationContentType | "all")
                }
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              >
                <option value="all">{t("admin_filter_all_content_types")}</option>
                <option value="nano">{t("admin_moderation_content_type_nano")}</option>
                <option value="nano_rating">{t("admin_moderation_content_type_rating")}</option>
                <option value="nano_comment">{t("admin_moderation_content_type_comment")}</option>
              </select>
            </label>
            <label className="space-y-1 text-sm text-neutral-700">
              <span>{t("admin_moderation_status_filter_label")}</span>
              <select
                value={moderationStatusFilter}
                onChange={(event) =>
                  setModerationStatusFilter(event.target.value as ModerationCaseStatus | "all")
                }
                className="w-full rounded-xl border border-neutral-300 px-3 py-2"
              >
                <option value="all">{t("admin_filter_all_statuses")}</option>
                <option value="pending">{t("admin_moderation_status_pending")}</option>
                <option value="approved">{t("admin_moderation_status_approved")}</option>
                <option value="rejected">{t("admin_moderation_status_rejected")}</option>
                <option value="deferred">{t("admin_moderation_status_deferred")}</option>
                <option value="escalated">{t("admin_moderation_status_escalated")}</option>
              </select>
            </label>
            <button
              onClick={() => void loadModerationQueue(1)}
              className="rounded-xl bg-primary-600 px-4 py-2 font-medium text-white transition hover:bg-primary-700"
            >
              {t("admin_apply_filters")}
            </button>
          </div>
        </div>

        {moderationMessage && (
          <p className="mt-4 rounded-xl border border-success-200 bg-success-50 px-3 py-2 text-sm text-success-700">
            {moderationMessage}
          </p>
        )}
        {moderationError && (
          <p role="alert" className="mt-4 rounded-xl border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">
            {moderationError}
          </p>
        )}

        {moderationLoading ? (
          <p role="status" className="mt-4 text-sm text-neutral-500">{t("admin_moderation_loading")}</p>
        ) : moderationItems.length === 0 ? (
          <p className="mt-4 text-sm text-neutral-500">{t("admin_moderation_empty")}</p>
        ) : (
          <div className="mt-4 space-y-4">
            {moderationItems.map((item) => {
              const draft = moderationDrafts[item.caseId] ?? { reason: "", deferredUntil: "" };
              const isReviewPending = moderationPending[item.caseId] === true;
              const isTakedownPending = takedownPending[item.caseId] === true;

              return (
                <article key={item.caseId} className="rounded-2xl border border-neutral-200 bg-neutral-50 p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-neutral-600">
                          {getContentTypeLabel(item.contentType, t)}
                        </span>
                        <span className="rounded-full bg-primary-100 px-3 py-1 text-xs font-semibold text-primary-700">
                          {getCaseStatusLabel(item.status, t)}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-neutral-950">
                        {getModerationSummary(item, t)}
                      </h3>
                      <p className="text-sm text-neutral-600">
                        {t("admin_moderation_author_prefix")} {getModerationMeta(item, t)}
                      </p>
                      <p className="text-sm text-neutral-500">
                        {t("admin_moderation_created_prefix")} {formatDateTime(item.createdAt, locale)}
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 lg:w-[26rem]">
                      <label className="space-y-1 text-sm text-neutral-700 sm:col-span-2">
                        <span>{t("admin_moderation_reason_label")}</span>
                        <textarea
                          value={draft.reason}
                          onChange={(event) =>
                            handleModerationDraftChange(item.caseId, "reason", event.target.value)
                          }
                          rows={3}
                          className="w-full rounded-xl border border-neutral-300 px-3 py-2"
                        />
                      </label>
                      <label className="space-y-1 text-sm text-neutral-700 sm:col-span-2">
                        <span>{t("admin_moderation_deferred_until_label")}</span>
                        <input
                          type="datetime-local"
                          value={draft.deferredUntil}
                          onChange={(event) =>
                            handleModerationDraftChange(item.caseId, "deferredUntil", event.target.value)
                          }
                          className="w-full rounded-xl border border-neutral-300 px-3 py-2"
                        />
                      </label>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      onClick={() => void handleModerationAction(item, "approve")}
                      disabled={isReviewPending || isTakedownPending}
                      className="rounded-xl bg-success-600 px-4 py-2 font-medium text-white transition hover:bg-success-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {t("admin_moderation_approve")}
                    </button>
                    <button
                      onClick={() => void handleModerationAction(item, "reject")}
                      disabled={isReviewPending || isTakedownPending}
                      className="rounded-xl bg-error-600 px-4 py-2 font-medium text-white transition hover:bg-error-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {t("admin_moderation_reject")}
                    </button>
                    <button
                      onClick={() => void handleModerationAction(item, "defer")}
                      disabled={isReviewPending || isTakedownPending}
                      className="rounded-xl border border-neutral-300 px-4 py-2 font-medium text-neutral-700 transition hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {t("admin_moderation_defer")}
                    </button>
                    <button
                      onClick={() => void handleModerationAction(item, "escalate")}
                      disabled={isReviewPending || isTakedownPending}
                      className="rounded-xl border border-neutral-300 px-4 py-2 font-medium text-neutral-700 transition hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {t("admin_moderation_escalate")}
                    </button>
                    <button
                      onClick={() => void handleTakedown(item)}
                      disabled={isReviewPending || isTakedownPending || getModerationNanoId(item) === null}
                      className="rounded-xl bg-neutral-900 px-4 py-2 font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isTakedownPending ? t("admin_takedown_pending") : t("admin_takedown_action")}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        <div className="mt-4 flex items-center justify-between text-sm text-neutral-600">
          <span>{t("admin_pagination_results_prefix")} {moderationTotal}</span>
          <div className="flex gap-2">
            <button
              onClick={() => void loadModerationQueue(Math.max(moderationPage - 1, 1))}
              disabled={moderationPage <= 1 || moderationLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_previous")}
            </button>
            <button
              onClick={() => void loadModerationQueue(moderationPage + 1)}
              disabled={moderationPage * MODERATION_PAGE_SIZE >= moderationTotal || moderationLoading}
              className="rounded-xl border border-neutral-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("admin_pagination_next")}
            </button>
          </div>
        </div>
      </section>
    </section>
  );
}