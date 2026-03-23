import { useEffect, useState } from "react";

import {
  approveNano,
  getModerationQueue,
  rejectNano,
  type ModeratorQueueItem,
  type ModeratorQueueListResponse,
} from "../../shared/api/moderator";
import { useTranslation } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

/** Per-row action loading state to avoid blocking the whole list */
interface RowActionState {
  [nanoId: string]: "approving" | "rejecting" | null;
}

interface QueuePageState {
  data: ModeratorQueueListResponse | null;
  loading: boolean;
  error: string | null;
  page: number;
}

function extractHttpStatus(error: unknown): number | null {
  if (typeof error !== "object" || error === null || !("response" in error)) {
    return null;
  }
  const response = (error as { response?: { status?: unknown } }).response;
  return typeof response?.status === "number" ? response.status : null;
}

/**
 * Moderation Queue Page
 *
 * Accessible to MODERATOR and ADMIN roles only.
 * Displays all Nanos in `pending_review` status ordered oldest-first (FIFO).
 * Moderators can approve (→ published) or reject (→ draft) each submission.
 */
export function ModeratorQueuePage(): JSX.Element {
  const { t } = useTranslation();

  const resolveErrorMessage = (error: unknown): string => {
    const status = extractHttpStatus(error);
    if (status === 401) {
      return t("auth_error_unauthorized");
    }
    if (status === 403) {
      return t("auth_error_forbidden");
    }
    return error instanceof Error ? error.message : t("error_unknown");
  };

  const [queueState, setQueueState] = useState<QueuePageState>({
    data: null,
    loading: true,
    error: null,
    page: 1,
  });

  const [rowAction, setRowAction] = useState<RowActionState>({});
  const [actionError, setActionError] = useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Data fetching
  // -------------------------------------------------------------------------

  const fetchQueue = async (page: number): Promise<void> => {
    try {
      setQueueState((prev) => ({ ...prev, loading: true, error: null }));
      const response = await getModerationQueue({ page, limit: 20 });
      setQueueState({ data: response, loading: false, error: null, page });
    } catch (err) {
      const message = resolveErrorMessage(err);
      setQueueState((prev) => ({ ...prev, loading: false, error: message }));
    }
  };

  useEffect(() => {
    void fetchQueue(1);
  }, []);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  /**
   * Approve a Nano — transitions it to `published`.
   * Refreshes the current page after the action completes.
   */
  const handleApprove = async (nanoId: string): Promise<void> => {
    setRowAction((prev) => ({ ...prev, [nanoId]: "approving" }));
    setActionError(null);
    try {
      await approveNano(nanoId);
      await fetchQueue(queueState.page);
    } catch (err) {
      const message = resolveErrorMessage(err);
      setActionError(`${t("moderator_approve_error")}: ${message}`);
    } finally {
      setRowAction((prev) => ({ ...prev, [nanoId]: null }));
    }
  };

  /**
   * Reject a Nano — transitions it back to `draft`.
   * Refreshes the current page after the action completes.
   */
  const handleReject = async (nanoId: string): Promise<void> => {
    setRowAction((prev) => ({ ...prev, [nanoId]: "rejecting" }));
    setActionError(null);
    try {
      await rejectNano(nanoId);
      await fetchQueue(queueState.page);
    } catch (err) {
      const message = resolveErrorMessage(err);
      setActionError(`${t("moderator_reject_error")}: ${message}`);
    } finally {
      setRowAction((prev) => ({ ...prev, [nanoId]: null }));
    }
  };

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  /**
   * Formats an ISO date string into a human-readable, locale-aware string.
   * Falls back gracefully if the value is null/undefined.
   */
  const formatDate = (iso: string | null | undefined): string => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  // -------------------------------------------------------------------------
  // Render helpers
  // -------------------------------------------------------------------------

  const renderQueueItem = (item: ModeratorQueueItem): JSX.Element => {
    const currentAction = rowAction[item.nano_id] ?? null;
    const isProcessing = currentAction !== null;

    return (
      <li
        key={item.nano_id}
        className="flex flex-col gap-3 rounded-lg border border-neutral-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
      >
        {/* Nano metadata */}
        <div className="flex flex-col gap-1">
          <span className="font-semibold text-neutral-900">{item.title}</span>
          <span className="text-sm text-neutral-500">
            {t("moderator_queue_creator_label")}:{" "}
            <span className="font-medium text-neutral-700">{item.creator_username}</span>
          </span>
          <span className="text-sm text-neutral-500">
            {t("moderator_queue_submitted_label")}:{" "}
            <span className="font-medium text-neutral-700">{formatDate(item.submitted_at)}</span>
          </span>
          {item.description && (
            <p className="mt-1 max-w-prose text-sm text-neutral-600 line-clamp-2">
              {item.description}
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex shrink-0 gap-2">
          {/* Approve */}
          <button
            onClick={() => void handleApprove(item.nano_id)}
            disabled={isProcessing}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white bg-success-600 hover:bg-success-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Approve ${item.title}`}
          >
            {currentAction === "approving" ? t("moderator_approving") : t("moderator_approve")}
          </button>

          {/* Reject */}
          <button
            onClick={() => void handleReject(item.nano_id)}
            disabled={isProcessing}
            className="rounded-lg px-4 py-2 text-sm font-medium text-white bg-error-600 hover:bg-error-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Reject ${item.title}`}
          >
            {currentAction === "rejecting" ? t("moderator_rejecting") : t("moderator_reject")}
          </button>
        </div>
      </li>
    );
  };

  // -------------------------------------------------------------------------
  // Main render
  // -------------------------------------------------------------------------

  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">
        {/* Page header */}
        <header className="space-y-1">
          <h1 className="text-2xl font-bold text-neutral-900">{t("moderator_queue_title")}</h1>
          <p className="text-neutral-600">{t("moderator_queue_subtitle")}</p>
        </header>

        {/* Action error banner */}
        {actionError && (
          <div
            role="alert"
            className="rounded-lg border border-error-200 bg-error-50 px-4 py-3 text-sm text-error-700"
          >
            {actionError}
          </div>
        )}

        {/* Loading state */}
        {queueState.loading && (
          <div className="flex items-center justify-center py-12">
            <span className="text-neutral-500">{t("loading") || "Loading…"}</span>
          </div>
        )}

        {/* Error state */}
        {!queueState.loading && queueState.error && (
          <div
            role="alert"
            className="rounded-lg border border-error-200 bg-error-50 px-4 py-3 text-sm text-error-700"
          >
            {queueState.error}
          </div>
        )}

        {/* Queue list */}
        {!queueState.loading && !queueState.error && queueState.data && (
          <section>
            {queueState.data.nanos.length === 0 ? (
              <p className="py-12 text-center text-neutral-500">{t("moderator_queue_empty")}</p>
            ) : (
              <ul className="space-y-3">{queueState.data.nanos.map(renderQueueItem)}</ul>
            )}

            {/* Pagination */}
            {queueState.data.pagination.total_pages > 1 && (
              <div className="mt-6 flex items-center justify-between text-sm text-neutral-600">
                <span>
                  {queueState.data.pagination.current_page} / {queueState.data.pagination.total_pages}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => void fetchQueue(queueState.page - 1)}
                    disabled={!queueState.data.pagination.has_prev_page}
                    className="rounded px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                  >
                    {t("prev") || "Prev"}
                  </button>
                  <button
                    onClick={() => void fetchQueue(queueState.page + 1)}
                    disabled={!queueState.data.pagination.has_next_page}
                    className="rounded px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                  >
                    {t("next") || "Next"}
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </main>
    </>
  );
}
