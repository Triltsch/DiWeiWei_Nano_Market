import { useEffect, useState } from "react";

import {
  AdminApiError,
  adminTakedownNano,
  getAdminModerationQueue,
  reviewModerationCase,
  type ModerationCaseItem,
  type ModerationCaseStatus,
  type ModerationContentType,
} from "../../shared/api";
import { useAuth } from "../auth";
import { useTranslation } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

const MODERATION_PAGE_SIZE = 20;

type SectionError = string | null;

interface ModerationDraft {
  reason: string;
  deferredUntil: string;
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

function getContentTypeLabel(value: ModerationContentType, t: ReturnType<typeof useTranslation>["t"]): string {
  if (value === "nano_rating") {
    return t("admin_moderation_content_type_rating");
  }
  if (value === "nano_comment") {
    return t("admin_moderation_content_type_comment");
  }
  return t("admin_moderation_content_type_nano");
}

function getCaseStatusLabel(value: ModerationCaseStatus, t: ReturnType<typeof useTranslation>["t"]): string {
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

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

/**
 * Moderation Queue Page
 *
 * Accessible to MODERATOR and ADMIN roles only.
 * Displays all Nanos in `pending_review` status ordered oldest-first (FIFO).
 * Moderators can approve (→ published) or reject (→ draft) each submission.
 */
export function ModeratorQueuePage(): JSX.Element {
  const { user } = useAuth();
  const { t } = useTranslation();
  const isAdmin = user?.role === "admin";

  const [moderationContentTypeFilter, setModerationContentTypeFilter] = useState<
    ModerationContentType | "all"
  >("all");
  const [moderationStatusFilter, setModerationStatusFilter] = useState<ModerationCaseStatus | "all">(
    "pending",
  );
  const [moderationItems, setModerationItems] = useState<ModerationCaseItem[]>([]);
  const [moderationPage, setModerationPage] = useState(1);
  const [moderationTotal, setModerationTotal] = useState(0);
  const [moderationLoading, setModerationLoading] = useState(true);
  const [moderationError, setModerationError] = useState<SectionError>(null);
  const [moderationMessage, setModerationMessage] = useState<string | null>(null);
  const [moderationDrafts, setModerationDrafts] = useState<Record<string, ModerationDraft>>({});
  const [moderationPending, setModerationPending] = useState<Record<string, boolean>>({});
  const [takedownPending, setTakedownPending] = useState<Record<string, boolean>>({});

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

  useEffect(() => {
    void loadModerationQueue(1);
  }, []);

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
      await loadModerationQueue(moderationPage);
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
      await loadModerationQueue(moderationPage);
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
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">
        <header className="space-y-1">
          <h1 className="text-2xl font-bold text-neutral-900">{t("moderator_queue_title")}</h1>
          <p className="text-neutral-600">{t("moderator_queue_subtitle")}</p>
        </header>

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
                        <h3 className="text-lg font-semibold text-neutral-950">{getModerationSummary(item, t)}</h3>
                        <p className="text-sm text-neutral-600">
                          {t("admin_moderation_author_prefix")} {getModerationMeta(item, t)}
                        </p>
                        <p className="text-sm text-neutral-500">
                          {t("admin_moderation_created_prefix")} {formatDateTime(item.createdAt)}
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
                      {isAdmin ? (
                        <button
                          onClick={() => void handleTakedown(item)}
                          disabled={
                            isReviewPending || isTakedownPending || getModerationNanoId(item) === null
                          }
                          className="rounded-xl bg-neutral-900 px-4 py-2 font-medium text-white transition hover:bg-neutral-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {isTakedownPending ? t("admin_takedown_pending") : t("admin_takedown_action")}
                        </button>
                      ) : null}
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
      </main>
    </>
  );
}
