import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  deleteCreatorNano,
  getCreatorNanos,
  submitNanoForReview,
  withdrawNanoFromReview,
  type CreatorNanoListResponse,
} from "../../shared/api/creator";
import { useTranslation } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

interface CreatorDashboardState {
  data: CreatorNanoListResponse | null;
  loading: boolean;
  error: string | null;
}

interface DeleteConfirmState {
  nanoId: string | null;
  deleting: boolean;
}

interface SubmitConfirmState {
  nanoId: string | null;
  submitting: boolean;
}

interface WithdrawConfirmState {
  nanoId: string | null;
  withdrawing: boolean;
}

/**
 * Creator Dashboard Page
 *
 * Displays list of creator's own Nanos with management actions
 * (edit, delete, view, etc.). Supports pagination and filtering.
 */
export function CreatorDashboardPage(): JSX.Element {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  const [state, setState] = useState<CreatorDashboardState>({
    data: null,
    loading: true,
    error: null,
  });

  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
    nanoId: null,
    deleting: false,
  });

  const [submitConfirm, setSubmitConfirm] = useState<SubmitConfirmState>({
    nanoId: null,
    submitting: false,
  });

  const [withdrawConfirm, setWithdrawConfirm] = useState<WithdrawConfirmState>({
    nanoId: null,
    withdrawing: false,
  });

  const currentPage = parseInt(searchParams.get("page") ?? "1", 10);
  const statusFilter = searchParams.get("status") ?? undefined;

  // Fetch creator's nanos
  useEffect(() => {
    const fetchNanos = async (): Promise<void> => {
      try {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        const response = await getCreatorNanos({
          page: currentPage,
          limit: 20,
          status: statusFilter,
        });
        setState({ data: response, loading: false, error: null });
      } catch (err) {
        const message = err instanceof Error ? err.message : t("error_unknown");
        setState((prev) => ({ ...prev, loading: false, error: message }));
      }
    };

    fetchNanos();
  }, [currentPage, statusFilter, t]);

  const handleDeleteClick = (nanoId: string): void => {
    setDeleteConfirm({ nanoId, deleting: false });
  };

  const handleSubmitClick = (nanoId: string): void => {
    setSubmitConfirm({ nanoId, submitting: false });
  };

  const handleConfirmSubmit = async (): Promise<void> => {
    if (!submitConfirm.nanoId) return;

    try {
      setSubmitConfirm((prev) => ({ ...prev, submitting: true }));
      await submitNanoForReview(submitConfirm.nanoId);
      setSubmitConfirm({ nanoId: null, submitting: false });
      // Refresh the list
      setState((prev) => ({ ...prev, loading: true }));
      const response = await getCreatorNanos({
        page: currentPage,
        limit: 20,
        status: statusFilter,
      });
      setState({ data: response, loading: false, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : t("error_unknown");
      setSubmitConfirm({ nanoId: null, submitting: false });
      setState((prev) => ({ ...prev, error: message }));
    }
  };

  const handleWithdrawClick = (nanoId: string): void => {
    setWithdrawConfirm({ nanoId, withdrawing: false });
  };

  const handleConfirmWithdraw = async (): Promise<void> => {
    if (!withdrawConfirm.nanoId) return;

    try {
      setWithdrawConfirm((prev) => ({ ...prev, withdrawing: true }));
      await withdrawNanoFromReview(withdrawConfirm.nanoId);
      setWithdrawConfirm({ nanoId: null, withdrawing: false });
      // Refresh the list
      setState((prev) => ({ ...prev, loading: true }));
      const response = await getCreatorNanos({
        page: currentPage,
        limit: 20,
        status: statusFilter,
      });
      setState({ data: response, loading: false, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : t("error_unknown");
      setWithdrawConfirm({ nanoId: null, withdrawing: false });
      setState((prev) => ({ ...prev, error: message }));
    }
  };

  const handleConfirmDelete = async (): Promise<void> => {
    if (!deleteConfirm.nanoId) return;

    try {
      setDeleteConfirm((prev) => ({ ...prev, deleting: true }));
      await deleteCreatorNano(deleteConfirm.nanoId);
      setDeleteConfirm({ nanoId: null, deleting: false });
      // Refresh the list
      setState((prev) => ({ ...prev, loading: true }));
      const response = await getCreatorNanos({
        page: currentPage,
        limit: 20,
        status: statusFilter,
      });
      setState({ data: response, loading: false, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : t("error_unknown");
      setDeleteConfirm({ nanoId: null, deleting: false });
      setState((prev) => ({ ...prev, error: message }));
    }
  };

  const handleStatusFilter = (status: string | null): void => {
    const params = new URLSearchParams();
    params.set("page", "1");
    if (status) {
      params.set("status", status);
    }
    setSearchParams(params);
  };

  // Get status badge styling and label
  const getStatusBadge = (status: string): { bgClass: string; textClass: string; label: string } => {
    switch (status.toLowerCase()) {
      case "draft":
        return {
          bgClass: "bg-warning-100",
          textClass: "text-warning-800",
          label: t("nano_status_draft") || "Draft",
        };
      case "pending_review":
        return {
          bgClass: "bg-info-100",
          textClass: "text-info-800",
          label: t("nano_status_pending_review") || "Pending Review",
        };
      case "published":
        return {
          bgClass: "bg-success-100",
          textClass: "text-success-800",
          label: t("nano_status_published") || "Published",
        };
      case "archived":
        return {
          bgClass: "bg-neutral-100",
          textClass: "text-neutral-800",
          label: t("nano_status_archived") || "Archived",
        };
      default:
        return {
          bgClass: "bg-neutral-100",
          textClass: "text-neutral-800",
          label: status,
        };
    }
  };

  // Get competency level label
  const getCompetencyLabel = (level: string): string => {
    switch (level.toLowerCase()) {
      case "basic":
      case "beginner":
        return t("competency_beginner") || "Beginner";
      case "intermediate":
        return t("competency_intermediate") || "Intermediate";
      case "advanced":
        return t("competency_advanced") || "Advanced";
      default:
        return level;
    }
  };

  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-8 pb-8">
        {/* Header */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-neutral-900">
                {t("creator_dashboard_title") || "My Nanos"}
              </h1>
              <p className="text-neutral-600 mt-1">
                {t("creator_dashboard_subtitle") || "Manage your learning content"}
              </p>
            </div>
            <Link
              to="/upload"
              className="px-6 py-2 rounded-lg text-center font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors shadow-md hover:shadow-lg"
            >
              {t("creator_upload_new") || "Upload New Nano"}
            </Link>
          </div>
        </section>

        {/* Status Filter Tabs */}
        <section className="border-b border-neutral-200">
          <div className="flex gap-2 overflow-x-auto pb-4">
            <button
              onClick={() => handleStatusFilter(null)}
              className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-colors ${
                !statusFilter
                  ? "bg-primary-600 text-white"
                  : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
              }`}
            >
              {t("all") || "All"}
            </button>
            {["draft", "pending_review", "published", "archived"].map((status) => (
              <button
                key={status}
                onClick={() => handleStatusFilter(status)}
                className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-colors ${
                  statusFilter === status
                    ? "bg-primary-600 text-white"
                    : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                }`}
              >
                {getStatusBadge(status).label}
              </button>
            ))}
          </div>
        </section>

        {/* Content */}
        {state.loading ? (
          <section className="card-elevated text-center py-12">
            <p className="text-neutral-600">{t("loading") || "Loading..."}</p>
          </section>
        ) : state.error ? (
          <section className="card-elevated bg-error-50 border border-error-200 p-4 rounded-lg">
            <p className="text-error-800">
              {t("error_loading_nanos") || "Error loading your Nanos"}: {state.error}
            </p>
          </section>
        ) : !state.data || state.data.nanos.length === 0 ? (
          <section className="card-elevated text-center py-12 space-y-4">
            <p className="text-neutral-600">
              {statusFilter
                ? t("creator_no_nanos_with_status") || `No Nanos with status: ${statusFilter}`
                : t("creator_no_nanos") || "You haven't uploaded any Nanos yet"}
            </p>
            <Link
              to="/upload"
              className="inline-block px-6 py-2 rounded-lg font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              {t("creator_upload_new") || "Upload New Nano"}
            </Link>
          </section>
        ) : (
          <section className="space-y-4">
            {/* Nanos List */}
            <div className="space-y-3">
              {state.data.nanos.map((nano) => {
                const statusBadge = getStatusBadge(nano.status);
                const isDraft = nano.status === "draft";

                return (
                  <article
                    key={nano.nano_id}
                    className="card-elevated flex flex-col sm:flex-row gap-4 p-4 hover:shadow-md transition-shadow"
                  >
                    {/* Thumbnail */}
                    {nano.thumbnail_url && (
                      <div className="sm:w-32 sm:h-24 flex-shrink-0">
                        <img
                          src={nano.thumbnail_url}
                          alt={nano.title}
                          className="w-full h-24 object-cover rounded-lg"
                        />
                      </div>
                    )}

                    {/* Content */}
                    <div className="flex-grow space-y-2">
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                        <div className="flex-grow">
                          <Link
                            to={`/nano/${nano.nano_id}`}
                            className="text-lg font-semibold text-primary-600 hover:text-primary-700"
                          >
                            {nano.title}
                          </Link>
                          {nano.description && (
                            <p className="text-neutral-600 text-sm mt-1 line-clamp-2">
                              {nano.description}
                            </p>
                          )}
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${statusBadge.bgClass} ${statusBadge.textClass}`}
                        >
                          {statusBadge.label}
                        </span>
                      </div>

                      {/* Metadata */}
                      <div className="flex flex-wrap gap-4 text-sm text-neutral-600">
                        {nano.duration_minutes && (
                          <span>{nano.duration_minutes} {t("minutes_abbr") || "min"}</span>
                        )}
                        <span>{getCompetencyLabel(nano.competency_level)}</span>
                        <span>{new Date(nano.updated_at).toLocaleDateString()}</span>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        {isDraft && (
                          <>
                            <Link
                              to={`/nanos/${nano.nano_id}/edit`}
                              className="px-3 py-1 rounded text-sm font-medium text-primary-600 bg-primary-50 hover:bg-primary-100 transition-colors"
                            >
                              {t("edit") || "Edit"}
                            </Link>
                            <button
                              onClick={() => handleSubmitClick(nano.nano_id)}
                              className="px-3 py-1 rounded text-sm font-medium text-primary-600 bg-primary-50 hover:bg-primary-100 transition-colors"
                            >
                              {t("creator_submit_review")}
                            </button>
                            <button
                              onClick={() => handleDeleteClick(nano.nano_id)}
                              className="px-3 py-1 rounded text-sm font-medium text-error-600 bg-error-50 hover:bg-error-100 transition-colors"
                            >
                              {t("delete") || "Delete"}
                            </button>
                          </>
                        )}
                        {nano.status === "pending_review" && (
                          <button
                            onClick={() => handleWithdrawClick(nano.nano_id)}
                            className="px-3 py-1 rounded text-sm font-medium text-warning-600 bg-warning-50 hover:bg-warning-100 transition-colors"
                          >
                            {t("creator_withdraw_review")}
                          </button>
                        )}
                        <Link
                          to={`/nano/${nano.nano_id}`}
                          className="px-3 py-1 rounded text-sm font-medium text-neutral-600 bg-neutral-100 hover:bg-neutral-200 transition-colors"
                        >
                          {t("view") || "View"}
                        </Link>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>

            {/* Pagination */}
            {state.data.pagination.total_pages > 1 && (
              <div className="flex justify-center items-center gap-2 pt-4">
                <button
                  onClick={() => {
                    const newPage = currentPage - 1;
                    const params = new URLSearchParams();
                    params.set("page", newPage.toString());
                    if (statusFilter) params.set("status", statusFilter);
                    setSearchParams(params);
                  }}
                  disabled={!state.data.pagination.has_prev_page}
                  className="px-3 py-1 rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                >
                  {t("prev") || "Previous"}
                </button>

                <span className="text-neutral-600 text-sm">
                  {t("page_of") || "Page"} {currentPage} {t("of") || "of"}{" "}
                  {state.data.pagination.total_pages}
                </span>

                <button
                  onClick={() => {
                    const newPage = currentPage + 1;
                    const params = new URLSearchParams();
                    params.set("page", newPage.toString());
                    if (statusFilter) params.set("status", statusFilter);
                    setSearchParams(params);
                  }}
                  disabled={!state.data.pagination.has_next_page}
                  className="px-3 py-1 rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
                >
                  {t("next") || "Next"}
                </button>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Delete Confirmation Modal */}
    {/* Submit for Review Confirmation Modal */}
      {submitConfirm.nanoId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6 space-y-4">
            <h2 className="text-lg font-semibold text-neutral-900">
              {t("creator_submit_review_confirm")}
            </h2>
            <p className="text-neutral-600 text-sm">
              {t("creator_submit_review_warning")}
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setSubmitConfirm({ nanoId: null, submitting: false })}
                disabled={submitConfirm.submitting}
                className="px-4 py-2 rounded-lg font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 transition-colors disabled:opacity-50"
              >
                {t("cancel")}
              </button>
              <button
                onClick={handleConfirmSubmit}
                disabled={submitConfirm.submitting}
                className="px-4 py-2 rounded-lg font-medium text-white bg-primary-600 hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {submitConfirm.submitting
                  ? t("creator_submit_review_submitting")
                  : t("creator_submit_review")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Withdraw from Review Confirmation Modal */}
      {withdrawConfirm.nanoId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6 space-y-4">
            <h2 className="text-lg font-semibold text-neutral-900">
              {t("creator_withdraw_review_confirm")}
            </h2>
            <p className="text-neutral-600 text-sm">
              {t("creator_withdraw_review_warning")}
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setWithdrawConfirm({ nanoId: null, withdrawing: false })}
                disabled={withdrawConfirm.withdrawing}
                className="px-4 py-2 rounded-lg font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 transition-colors disabled:opacity-50"
              >
                {t("cancel")}
              </button>
              <button
                onClick={handleConfirmWithdraw}
                disabled={withdrawConfirm.withdrawing}
                className="px-4 py-2 rounded-lg font-medium text-white bg-warning-600 hover:bg-warning-700 transition-colors disabled:opacity-50"
              >
                {withdrawConfirm.withdrawing
                  ? t("creator_withdraw_review_withdrawing")
                  : t("creator_withdraw_review")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm.nanoId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6 space-y-4">
            <h2 className="text-lg font-semibold text-neutral-900">
              {t("creator_confirm_delete") || "Delete Nano?"}
            </h2>
            <p className="text-neutral-600">
              {t("creator_delete_warning") ||
                "This action cannot be undone. Are you sure you want to delete this Nano?"}
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setDeleteConfirm({ nanoId: null, deleting: false })}
                disabled={deleteConfirm.deleting}
                className="px-4 py-2 rounded-lg font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 transition-colors disabled:opacity-50"
              >
                {t("cancel") || "Cancel"}
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleteConfirm.deleting}
                className="px-4 py-2 rounded-lg font-medium text-white bg-error-600 hover:bg-error-700 transition-colors disabled:opacity-50"
              >
                {deleteConfirm.deleting
                  ? t("deleting") || "Deleting..."
                  : t("delete") || "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
