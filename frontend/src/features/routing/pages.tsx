import { useEffect, useId, useRef, useState, type PropsWithChildren } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import {
  LoginPage as LoginAuthPage,
  RegisterPage as RegisterAuthPage,
  useAuth,
  VerifyEmailPage as VerifyEmailAuthPage,
} from "../auth";
import { PrivacyPage as PrivacyLegalPage, TermsPage as TermsLegalPage } from "../legal/pages";
import {
  CreatorDashboardPage as CreatorDashboardPageComponent,
  EditNanoPage as EditNanoPageComponent,
  ModeratorQueuePage as ModeratorQueuePageComponent,
  UploadWizardPage as UploadWizardPageComponent,
} from "../creator";
import {
  createNanoComment,
  createNanoRating,
  getNanoDetail,
  getNanoComments,
  getNanoDownloadInfo,
  getNanoRatings,
  NanoFeedbackApiError,
  NanoDetailApiError,
  normalizeSearchLevel,
  searchNanos,
  updateMyNanoRating,
  type NanoComment,
  type NanoCommentsResponse,
  type NanoDetail,
  type NanoRatingsResponse,
  type SearchFilters,
  type SearchNano,
} from "../../shared/api";
import { useTranslation, type TranslationKey } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

function PageLayout({ children }: PropsWithChildren): JSX.Element {
  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">{children}</main>
    </>
  );
}

function PlaceholderPage({ title, description }: PlaceholderPageProps): JSX.Element {
  return (
    <PageLayout>
      <section className="card-elevated space-y-2">
        <h1 className="text-primary-600">{title}</h1>
        <p className="text-base text-neutral-600">{description}</p>
      </section>
    </PageLayout>
  );
}

export function HomePage(): JSX.Element {
  const { t } = useTranslation();

  return (
    <PageLayout>
      {/* Hero Section */}
      <section className="space-y-8 py-12 md:py-20">
        <div className="space-y-6 text-center">
          <div className="flex justify-center">
            <img
              src={t("logo_src")}
              alt={t("logo_alt")}
              className="h-[25rem] w-auto max-w-full object-contain shadow-lg"
            />
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold text-neutral-900">
              {t("home_title")}
            </h1>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto leading-relaxed">
              {t("home_hero_description")}
            </p>
          </div>

          {/* Call-to-Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link
              to="/register"
              className="px-8 py-3 rounded-lg text-center font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors shadow-md hover:shadow-lg"
            >
              {t("home_cta_register")}
            </Link>
            <Link
              to="/search"
              className="px-8 py-3 rounded-lg text-center font-semibold bg-neutral-200 text-neutral-900 hover:bg-neutral-300 transition-colors shadow-md hover:shadow-lg"
            >
              {t("home_cta_discover")}
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards Section */}
      <section className="space-y-8">
        <h2 className="text-3xl font-bold text-center text-neutral-900">{t("home_features_title")}</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Feature Card 1 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">{t("home_feature_quality_title")}</h3>
            <p className="text-neutral-600">{t("home_feature_quality_description")}</p>
          </article>

          {/* Feature Card 2 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-secondary-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-secondary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">{t("home_feature_share_title")}</h3>
            <p className="text-neutral-600">{t("home_feature_share_description")}</p>
          </article>

          {/* Feature Card 3 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-accent-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-accent-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">{t("home_feature_fast_title")}</h3>
            <p className="text-neutral-600">{t("home_feature_fast_description")}</p>
          </article>
        </div>
      </section>

      {/* Secondary CTA Section */}
      <section className="rounded-lg bg-gradient-to-r from-primary-50 to-secondary-50 p-8 md:p-12 text-center space-y-4">
        <h2 className="text-2xl font-bold text-neutral-900">
          {t("home_creator_title")}
        </h2>
        <p className="text-neutral-600 max-w-xl mx-auto">
          {t("home_creator_description")}
        </p>
        <div>
          <Link
            to="/register"
            className="inline-block px-6 py-2 rounded-lg font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            {t("home_creator_cta")}
          </Link>
        </div>
      </section>

      {/* Footer Info */}
      <section className="border-t border-neutral-200 pt-8 space-y-4 text-center text-sm text-neutral-600">
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link to="/terms" className="hover:text-primary-600 transition-colors">
            {t("home_footer_terms")}
          </Link>
          <span className="hidden sm:inline">•</span>
          <Link to="/privacy" className="hover:text-primary-600 transition-colors">
            {t("home_footer_privacy")}
          </Link>
        </div>
        <p>{t("home_footer_copy")}</p>
      </section>
    </PageLayout>
  );
}

/** Number of search results loaded per page / "load more" batch. */
const PAGE_SIZE = 20;

/** Debounce delay (ms) for the keyword search input. */
const DEBOUNCE_MS = 300;

/** Page size for the public comments area on the detail page. */
const COMMENTS_PAGE_SIZE = 5;

const NANO_STATUS_TRANSLATION_KEYS: Partial<Record<string, TranslationKey>> = {
  draft: "nano_status_draft",
  pending_review: "nano_status_pending_review",
  published: "nano_status_published",
  archived: "nano_status_archived",
};

const COMPETENCY_TRANSLATION_KEYS: Partial<Record<string, TranslationKey>> = {
  beginner: "competency_beginner",
  intermediate: "competency_intermediate",
  advanced: "competency_advanced",
};

const FEEDBACK_STATUS_TRANSLATION_KEYS: Partial<Record<string, TranslationKey>> = {
  approved: "nano_details_feedback_status_approved",
  pending: "nano_details_feedback_status_pending",
  hidden: "nano_details_feedback_status_hidden",
};

const RATING_STATUS_MESSAGE_KEYS: Partial<Record<string, TranslationKey>> = {
  approved: "nano_details_rating_status_approved",
  pending: "nano_details_rating_status_pending",
  hidden: "nano_details_rating_status_hidden",
};

const COMMENT_STATUS_MESSAGE_KEYS: Partial<Record<string, TranslationKey>> = {
  approved: "nano_details_comment_status_approved",
  pending: "nano_details_comment_status_pending",
  hidden: "nano_details_comment_status_hidden",
};

function getFeedbackStatusLabel(status: string, t: (key: TranslationKey) => string): string {
  const translationKey = FEEDBACK_STATUS_TRANSLATION_KEYS[status];
  return translationKey ? t(translationKey) : status;
}

function getFeedbackStatusMessage(
  status: string,
  type: "rating" | "comment",
  t: (key: TranslationKey) => string,
): string | null {
  const translationKey =
    type === "rating" ? RATING_STATUS_MESSAGE_KEYS[status] : COMMENT_STATUS_MESSAGE_KEYS[status];
  return translationKey ? t(translationKey) : null;
}

function getFeedbackStatusClasses(status: string): string {
  switch (status) {
    case "approved":
      return "bg-success-100 text-success-700";
    case "hidden":
      return "bg-error-100 text-error-700";
    default:
      return "bg-warning-100 text-warning-700";
  }
}

function buildDefaultRatingsState(nanoId: string, detail: NanoDetail | null): NanoRatingsResponse {
  return {
    nanoId,
    aggregation: {
      averageRating: detail?.ratingSummary.averageRating ?? 0,
      medianRating: 0,
      ratingCount: detail?.ratingSummary.ratingCount ?? 0,
      distribution: [],
    },
    currentUserRating: null,
  };
}

function buildDefaultCommentsState(): NanoCommentsResponse {
  return {
    comments: [],
    pagination: {
      current_page: 1,
      page_size: COMMENTS_PAGE_SIZE,
      total_results: 0,
      total_pages: 1,
      has_next_page: false,
      has_prev_page: false,
    },
  };
}

function formatTimestamp(value: string, locale: string): string {
  if (!value) {
    return "";
  }

  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(timestamp);
}

export function SearchPage(): JSX.Element {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialise state from URL on first mount.
  const [queryInput, setQueryInput] = useState(() => searchParams.get("q") ?? "");
  const [debouncedQuery, setDebouncedQuery] = useState(() => searchParams.get("q") ?? "");
  const [filters, setFilters] = useState<SearchFilters>(() => ({
    category: searchParams.get("category") ?? "",
    level: normalizeSearchLevel(searchParams.get("level")) ?? "",
    duration: searchParams.get("duration") ?? "",
    language: searchParams.get("language") ?? "",
  }));
  const [results, setResults] = useState<SearchNano[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [lastPageCount, setLastPageCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasNextPage, setHasNextPage] = useState(false);

  /**
   * Tracks the last URLSearchParams string we wrote ourselves so the
   * bidirectional-sync effect can distinguish our own writes from external
   * navigation (browser back/forward) and avoid an update loop.
   */
  const lastWrittenSearch = useRef<string>("");

  // Debounce the raw keyword input before triggering a search fetch.
  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedQuery(queryInput.trim());
    }, DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [queryInput]);

  // Keep the URL in sync whenever the search inputs change (write direction).
  useEffect(() => {
    const nextParams = new URLSearchParams();

    if (queryInput.trim().length > 0) {
      nextParams.set("q", queryInput.trim());
    }
    if (filters.category && filters.category.length > 0) {
      nextParams.set("category", filters.category);
    }
    if (filters.level && filters.level.length > 0) {
      nextParams.set("level", filters.level);
    }
    if (filters.duration && filters.duration.length > 0) {
      nextParams.set("duration", filters.duration);
    }
    if (filters.language && filters.language.length > 0) {
      nextParams.set("language", filters.language);
    }

    lastWrittenSearch.current = nextParams.toString();
    setSearchParams(nextParams, { replace: true });
  }, [filters, queryInput, setSearchParams]);

  // Fetch the first page whenever the debounced query or filters change.
  useEffect(() => {
    let isActive = true;

    const fetchFirstPage = async (): Promise<void> => {
      setIsLoading(true);
      setSearchError(null);
      setCurrentPage(1);
      setHasNextPage(false);

      try {
        const response = await searchNanos({
          query: debouncedQuery,
          filters,
          limit: PAGE_SIZE,
          page: 1,
        });
        const responsePage = Number.isFinite(response.page) ? response.page : 1;

        if (!isActive) {
          return;
        }

        setResults(response.items);
        setTotal(response.total);
        setCurrentPage(responsePage);
        setLastPageCount(response.items.length);
        setHasNextPage(response.hasNextPage === true);
      } catch {
        if (isActive) {
          setResults([]);
          setTotal(null);
          setLastPageCount(0);
          setSearchError(t("search_error"));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void fetchFirstPage();

    return () => {
      isActive = false;
    };
  }, [debouncedQuery, filters, t]);

  /**
   * Bidirectional URL sync (read direction).
   * Updates local state when searchParams change externally, e.g. browser
   * back/forward navigation. The `lastWrittenSearch` ref prevents a feedback
   * loop with our own `setSearchParams` calls above.
   */
  useEffect(() => {
    if (searchParams.toString() === lastWrittenSearch.current) {
      // This change originated from our own write – skip.
      return;
    }

    const newQuery = searchParams.get("q") ?? "";
    const newFilters: SearchFilters = {
      category: searchParams.get("category") ?? "",
      level: normalizeSearchLevel(searchParams.get("level")) ?? "",
      duration: searchParams.get("duration") ?? "",
      language: searchParams.get("language") ?? "",
    };

    setQueryInput((prev) => (prev === newQuery ? prev : newQuery));
    setDebouncedQuery((prev) => (prev === newQuery ? prev : newQuery));
    setFilters((prev) => {
      if (
        prev.category === newFilters.category &&
        prev.level === newFilters.level &&
        prev.duration === newFilters.duration &&
        prev.language === newFilters.language
      ) {
        return prev; // Stable reference – avoids unnecessary re-renders.
      }
      return newFilters;
    });
  }, [searchParams]);

  const hasMore = hasNextPage || (total === null ? lastPageCount === PAGE_SIZE : results.length < total);

  const handleFilterChange = (field: keyof SearchFilters, value: string): void => {
    setFilters((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleLoadMore = async (): Promise<void> => {
    if (isLoadingMore || !hasMore) {
      return;
    }

    setIsLoadingMore(true);
    try {
      const response = await searchNanos({
        query: debouncedQuery,
        filters,
        limit: PAGE_SIZE,
        page: currentPage + 1,
      });
      const responsePage = Number.isFinite(response.page) ? response.page : currentPage + 1;

      setResults((current) => [...current, ...response.items]);
      setTotal(response.total);
      setCurrentPage(responsePage);
      setLastPageCount(response.items.length);
      setHasNextPage(response.hasNextPage === true);
    } catch {
      setSearchError(t("search_error"));
    } finally {
      setIsLoadingMore(false);
    }
  };

  return (
    <PageLayout>
      <section className="space-y-6">
        <header className="card-elevated space-y-4">
          <h1 className="text-primary-600">{t("search_title")}</h1>
          <p className="text-base text-neutral-600">{t("search_description")}</p>
          <label className="block space-y-2" htmlFor="nano-search-input">
            <span className="text-sm font-medium text-neutral-700">{t("search_keyword_label")}</span>
            <input
              id="nano-search-input"
              type="search"
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
              placeholder={t("search_keyword_placeholder")}
              value={queryInput}
              onChange={(event) => setQueryInput(event.target.value)}
            />
          </label>
        </header>

        <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
          <aside className="card-elevated space-y-4" aria-label={t("search_filters_aria")}>
            <h2 className="text-lg font-semibold text-neutral-900">{t("search_filters_title")}</h2>

            <label className="block space-y-1" htmlFor="filter-category">
              <span className="text-sm font-medium text-neutral-700">{t("search_category_label")}</span>
              <input
                id="filter-category"
                type="text"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                value={filters.category ?? ""}
                onChange={(event) => handleFilterChange("category", event.target.value)}
                placeholder={t("search_category_placeholder")}
              />
            </label>

            <label className="block space-y-1" htmlFor="filter-level">
              <span className="text-sm font-medium text-neutral-700">{t("search_level_label")}</span>
              <select
                id="filter-level"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                value={filters.level ?? ""}
                onChange={(event) => handleFilterChange("level", event.target.value)}
              >
                <option value="">{t("search_level_all")}</option>
                <option value="1">{t("search_level_beginner")}</option>
                <option value="2">{t("search_level_intermediate")}</option>
                <option value="3">{t("search_level_advanced")}</option>
              </select>
            </label>

            <label className="block space-y-1" htmlFor="filter-duration">
              <span className="text-sm font-medium text-neutral-700">{t("search_duration_label")}</span>
              <select
                id="filter-duration"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                value={filters.duration ?? ""}
                onChange={(event) => handleFilterChange("duration", event.target.value)}
              >
                <option value="">{t("search_duration_all")}</option>
                <option value="0-15">{t("search_duration_0_15")}</option>
                <option value="15-30">{t("search_duration_15_30")}</option>
                <option value="30+">{t("search_duration_30_plus")}</option>
              </select>
            </label>

            <label className="block space-y-1" htmlFor="filter-language">
              <span className="text-sm font-medium text-neutral-700">{t("search_language_label")}</span>
              <select
                id="filter-language"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                value={filters.language ?? ""}
                onChange={(event) => handleFilterChange("language", event.target.value)}
              >
                <option value="">{t("search_language_all")}</option>
                <option value="de">{t("language_option_de")}</option>
                <option value="en">{t("language_option_en")}</option>
              </select>
            </label>
          </aside>

          <section className="space-y-4" aria-label={t("search_results_aria")}>
            {isLoading && (
              <div className="space-y-3" aria-label={t("search_loading_aria")}>
                {Array.from({ length: 3 }).map((_, index) => (
                  <article key={`skeleton-${index}`} className="card-elevated animate-pulse space-y-3">
                    <div className="h-5 w-2/3 rounded bg-neutral-200" />
                    <div className="h-4 w-1/2 rounded bg-neutral-200" />
                    <div className="grid grid-cols-2 gap-2">
                      <div className="h-4 rounded bg-neutral-200" />
                      <div className="h-4 rounded bg-neutral-200" />
                    </div>
                  </article>
                ))}
              </div>
            )}

            {searchError && (
              <div className="card-elevated" role="alert">
                <p className="text-red-600">{searchError}</p>
              </div>
            )}

            {!isLoading && !searchError && results.length === 0 && (
              <div className="card-elevated">
                <p className="text-neutral-700">{t("search_empty")}</p>
              </div>
            )}

            {!isLoading && results.length > 0 && (
              <>
                <ul className="space-y-3">
                  {results.map((item) => (
                    <li key={item.id} className="card-elevated space-y-2">
                      <h3 className="text-lg font-semibold text-neutral-900">
                        <Link
                          to={`/nano/${item.id}`}
                          className="hover:text-primary-600 focus:text-primary-600 focus:outline-none"
                        >
                          {item.title ?? t("search_title_fallback")}
                        </Link>
                      </h3>
                      <div className="grid gap-2 text-sm text-neutral-700 sm:grid-cols-2">
                        <p>
                          <span className="font-medium">{t("search_creator_label")}</span>{" "}
                          {item.creator ?? t("search_creator_fallback")}
                        </p>
                        <p>
                          <span className="font-medium">{t("search_avg_rating_label")}</span>{" "}
                          {item.averageRating !== null
                            ? item.averageRating.toFixed(1)
                            : t("search_not_available")}
                        </p>
                        <p>
                          <span className="font-medium">{t("search_duration_result_label")}</span>{" "}
                          {item.durationMinutes !== null
                            ? `${item.durationMinutes} min`
                            : t("search_not_available")}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>

                {hasMore && (
                  <div className="pt-2">
                    <button
                      type="button"
                      className="btn-outline"
                      onClick={() => {
                        void handleLoadMore();
                      }}
                      disabled={isLoadingMore}
                    >
                      {isLoadingMore ? t("search_loading_more") : t("search_load_more")}
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </section>
    </PageLayout>
  );
}
export function NanoDetailsPage(): JSX.Element {
  const { language, t } = useTranslation();
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const params = useParams<{ id: string }>();
  const nanoId = params.id ?? "";
  const commentFieldId = useId();
  const [detail, setDetail] = useState<NanoDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorCode, setErrorCode] = useState<"generic" | "not-found" | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [ratings, setRatings] = useState<NanoRatingsResponse | null>(null);
  const [isRatingsLoading, setIsRatingsLoading] = useState(true);
  const [ratingsError, setRatingsError] = useState<string | null>(null);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [isRatingSubmitting, setIsRatingSubmitting] = useState(false);
  const [ratingMessage, setRatingMessage] = useState<string | null>(null);
  const [ratingError, setRatingError] = useState<string | null>(null);
  const [comments, setComments] = useState<NanoCommentsResponse | null>(null);
  const [commentsPage, setCommentsPage] = useState(1);
  const [isCommentsLoading, setIsCommentsLoading] = useState(true);
  const [commentsError, setCommentsError] = useState<string | null>(null);
  const [commentDraft, setCommentDraft] = useState("");
  const [isCommentSubmitting, setIsCommentSubmitting] = useState(false);
  const [commentMessage, setCommentMessage] = useState<string | null>(null);
  const [commentError, setCommentError] = useState<string | null>(null);
  const [latestPendingComment, setLatestPendingComment] = useState<NanoComment | null>(null);

  const locale = language === "de" ? "de-DE" : "en-US";
  const loginRedirectPath = `/login?redirect=${encodeURIComponent(`/nano/${nanoId}`)}`;

  useEffect(() => {
    let isActive = true;

    const loadNanoDetail = async (): Promise<void> => {
      if (!nanoId) {
        setErrorCode("not-found");
        setIsLoading(false);
        setDetail(null);
        return;
      }

      setIsLoading(true);
      setErrorCode(null);
      setDownloadError(null);

      try {
        const response = await getNanoDetail(nanoId);
        if (!isActive) {
          return;
        }
        setDetail(response);
      } catch (error) {
        if (!isActive) {
          return;
        }
        setDetail(null);

        if (error instanceof NanoDetailApiError && error.code === "not-found") {
          setErrorCode("not-found");
          return;
        }
        setErrorCode("generic");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void loadNanoDetail();

    return () => {
      isActive = false;
    };
  }, [nanoId]);

  useEffect(() => {
    setCommentsPage(1);
    setSelectedRating(null);
    setRatingMessage(null);
    setRatingError(null);
    setCommentMessage(null);
    setCommentError(null);
    setLatestPendingComment(null);
    setCommentDraft("");
  }, [nanoId]);

  useEffect(() => {
    if (!detail) {
      return;
    }

    if (detail.metadata.status !== "published") {
      setRatings(buildDefaultRatingsState(nanoId, detail));
      setComments(buildDefaultCommentsState());
      setIsRatingsLoading(false);
      setIsCommentsLoading(false);
      setRatingsError(null);
      setCommentsError(null);
      return;
    }

    if (!nanoId) {
      return;
    }

    let isActive = true;

    const loadRatings = async (): Promise<void> => {
      setIsRatingsLoading(true);
      setRatingsError(null);

      try {
        const response = await getNanoRatings(nanoId);
        if (!isActive) {
          return;
        }

        setRatings(response);
        setSelectedRating(response.currentUserRating?.score ?? null);
        setDetail((currentDetail) =>
          currentDetail
            ? {
                ...currentDetail,
                ratingSummary: {
                  ...currentDetail.ratingSummary,
                  averageRating: response.aggregation.averageRating,
                  ratingCount: response.aggregation.ratingCount,
                },
              }
            : currentDetail
        );
      } catch (error) {
        if (!isActive) {
          return;
        }

        setRatings(buildDefaultRatingsState(nanoId, detail));
        if (error instanceof NanoFeedbackApiError) {
          if (error.code === "unauthorized") {
            navigate(loginRedirectPath);
            return;
          }

          if (error.code === "forbidden") {
            setRatingsError(t("auth_error_forbidden"));
            return;
          }
        }

        setRatingsError(t("nano_details_rating_error"));
      } finally {
        if (isActive) {
          setIsRatingsLoading(false);
        }
      }
    };

    void loadRatings();

    return () => {
      isActive = false;
    };
  }, [detail?.metadata.status, isAuthenticated, loginRedirectPath, nanoId, navigate, t, user?.id]);

  useEffect(() => {
    if (!detail) {
      return;
    }

    if (detail.metadata.status !== "published") {
      setComments(buildDefaultCommentsState());
      setIsCommentsLoading(false);
      setCommentsError(null);
      return;
    }

    if (!nanoId) {
      return;
    }

    let isActive = true;

    const loadComments = async (): Promise<void> => {
      setIsCommentsLoading(true);
      setCommentsError(null);

      try {
        const response = await getNanoComments(nanoId, {
          page: commentsPage,
          limit: COMMENTS_PAGE_SIZE,
        });

        if (!isActive) {
          return;
        }

        setComments(response);
      } catch (error) {
        if (!isActive) {
          return;
        }

        if (error instanceof NanoFeedbackApiError && error.code === "forbidden") {
          setCommentsError(t("auth_error_forbidden"));
          return;
        }

        setCommentsError(t("nano_details_comments_error"));
      } finally {
        if (isActive) {
          setIsCommentsLoading(false);
        }
      }
    };

    void loadComments();

    return () => {
      isActive = false;
    };
  }, [commentsPage, detail?.metadata.status, nanoId, t]);

  const handleDownloadClick = async (): Promise<void> => {
    if (!nanoId) {
      return;
    }

    setDownloadError(null);

    if (!isAuthenticated) {
      navigate(loginRedirectPath);
      return;
    }

    setIsDownloading(true);

    try {
      const downloadInfo = await getNanoDownloadInfo(nanoId);

      if (!downloadInfo.canDownload || downloadInfo.downloadUrl.length === 0) {
        setDownloadError(t("nano_details_download_error"));
        return;
      }

      window.location.assign(downloadInfo.downloadUrl);
    } catch {
      setDownloadError(t("nano_details_download_error"));
    } finally {
      setIsDownloading(false);
    }
  };

  const handleRatingSelect = async (score: number): Promise<void> => {
    if (!nanoId) {
      return;
    }

    if (!isAuthenticated) {
      navigate(loginRedirectPath);
      return;
    }

    setSelectedRating(score);
    setRatingError(null);
    setRatingMessage(null);
    setIsRatingSubmitting(true);

    try {
      const response = ratings?.currentUserRating
        ? await updateMyNanoRating(nanoId, score)
        : await createNanoRating(nanoId, score);

      setRatings({
        nanoId: response.nanoId,
        aggregation: response.aggregation,
        currentUserRating: response.userRating,
      });
      setDetail((currentDetail) =>
        currentDetail
          ? {
              ...currentDetail,
              ratingSummary: {
                ...currentDetail.ratingSummary,
                averageRating: response.aggregation.averageRating,
                ratingCount: response.aggregation.ratingCount,
              },
            }
          : currentDetail
      );
      setRatingMessage(t("nano_details_rating_saved_message"));
    } catch (error) {
      if (error instanceof NanoFeedbackApiError) {
        if (error.code === "unauthorized") {
          navigate(loginRedirectPath);
          return;
        }

        if (error.code === "forbidden") {
          setRatingError(t("auth_error_forbidden"));
          return;
        }

        if (error.code === "conflict") {
          setRatingError(t("nano_details_rating_conflict"));
          return;
        }

        if (error.code === "validation") {
          setRatingError(t("nano_details_rating_validation_error"));
          return;
        }
      }

      setRatingError(t("nano_details_rating_submit_error"));
    } finally {
      setIsRatingSubmitting(false);
    }
  };

  const handleCommentSubmit = async (): Promise<void> => {
    if (!nanoId) {
      return;
    }

    if (!isAuthenticated) {
      navigate(loginRedirectPath);
      return;
    }

    if (commentDraft.trim().length === 0) {
      setCommentError(t("nano_details_comment_validation_error"));
      return;
    }

    setCommentError(null);
    setCommentMessage(null);
    setIsCommentSubmitting(true);

    try {
      const response = await createNanoComment(nanoId, commentDraft);
      setLatestPendingComment(response.comment);
      setCommentDraft("");
      setCommentMessage(t("nano_details_comment_pending_message"));
    } catch (error) {
      if (error instanceof NanoFeedbackApiError) {
        if (error.code === "unauthorized") {
          navigate(loginRedirectPath);
          return;
        }

        if (error.code === "forbidden") {
          setCommentError(t("auth_error_forbidden"));
          return;
        }

        if (error.code === "conflict") {
          setCommentError(t("nano_details_comment_conflict"));
          return;
        }

        if (error.code === "validation") {
          setCommentError(t("nano_details_comment_validation_error"));
          return;
        }
      }

      setCommentError(t("nano_details_comment_submit_error"));
    } finally {
      setIsCommentSubmitting(false);
    }
  };

  const handleChatClick = (): void => {
    if (!isAuthenticated) {
      navigate(loginRedirectPath);
      return;
    }

    navigate("/profile");
  };

  if (isLoading) {
    return (
      <PageLayout>
        <section className="card-elevated" aria-label={t("nano_details_loading")}> 
          <p className="text-neutral-700">{t("nano_details_loading")}</p>
        </section>
      </PageLayout>
    );
  }

  if (errorCode === "not-found") {
    return (
      <PageLayout>
        <section className="card-elevated space-y-3">
          <h1 className="text-primary-600">{t("nano_details_not_found_title")}</h1>
          <p className="text-neutral-700">{t("nano_details_not_found_description")}</p>
          <Link to="/search" className="btn-outline inline-flex">
            {t("nano_details_back_to_search")}
          </Link>
        </section>
      </PageLayout>
    );
  }

  if (!detail || errorCode === "generic") {
    return (
      <PageLayout>
        <section className="card-elevated space-y-3" role="alert">
          <h1 className="text-primary-600">{t("nano_details_title")}</h1>
          <p className="text-neutral-700">{t("nano_details_error")}</p>
          <Link to="/search" className="btn-outline inline-flex">
            {t("nano_details_back_to_search")}
          </Link>
        </section>
      </PageLayout>
    );
  }

  const statusKey = NANO_STATUS_TRANSLATION_KEYS[detail.metadata.status];
  const competencyKey = COMPETENCY_TRANSLATION_KEYS[detail.metadata.competencyLevel];
  const durationLabel =
    detail.metadata.durationMinutes !== null
      ? `${detail.metadata.durationMinutes} ${t("minutes_abbr")}`
      : t("search_not_available");
  const categoriesLabel =
    detail.metadata.categories.length > 0
      ? detail.metadata.categories.map((category) => category.categoryName).join(", ")
      : t("search_not_available");
  const uploadedAtLabel = detail.metadata.uploadedAt
    ? formatTimestamp(detail.metadata.uploadedAt, locale)
    : t("search_not_available");
  const publishedAtLabel = detail.metadata.publishedAt
    ? formatTimestamp(detail.metadata.publishedAt, locale)
    : t("search_not_available");
  const updatedAtLabel = detail.metadata.updatedAt
    ? formatTimestamp(detail.metadata.updatedAt, locale)
    : t("search_not_available");
  const ratingsState = ratings ?? buildDefaultRatingsState(nanoId, detail);
  const commentsState = comments ?? buildDefaultCommentsState();
  const currentUserRating = ratingsState.currentUserRating;
  const currentRatingStatus = currentUserRating
    ? getFeedbackStatusLabel(currentUserRating.moderationStatus, t)
    : null;
  const currentRatingMessage = currentUserRating
    ? getFeedbackStatusMessage(currentUserRating.moderationStatus, "rating", t)
    : null;
  const ratingAverageLabel = ratingsState.aggregation.averageRating.toFixed(1);
  const isPublished = detail.metadata.status === "published";

  return (
    <PageLayout>
      <section className="space-y-6">
        <article className="card-elevated space-y-4">
          <header className="space-y-2">
            <h1 className="text-primary-600">{detail.title}</h1>
            <p className="text-neutral-700">{detail.metadata.description ?? t("search_not_available")}</p>
          </header>

          <dl className="grid gap-3 text-sm text-neutral-700 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="font-medium">{t("nano_details_creator_label")}</dt>
              <dd>{detail.creator.username ?? t("search_creator_fallback")}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("search_duration_result_label")}</dt>
              <dd>{durationLabel}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_level_label")}</dt>
              <dd>{competencyKey ? t(competencyKey) : detail.metadata.competencyLevel}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_language_label")}</dt>
              <dd>{detail.metadata.language || t("search_not_available")}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_format_label")}</dt>
              <dd>{detail.metadata.format || t("search_not_available")}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_license_label")}</dt>
              <dd>{detail.metadata.license || t("search_not_available")}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_status_label")}</dt>
              <dd>{statusKey ? t(statusKey) : detail.metadata.status}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_categories_label")}</dt>
              <dd>{categoriesLabel}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_uploaded_at_label")}</dt>
              <dd>{uploadedAtLabel}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_published_at_label")}</dt>
              <dd>{publishedAtLabel}</dd>
            </div>
            <div>
              <dt className="font-medium">{t("nano_details_updated_at_label")}</dt>
              <dd>{updatedAtLabel}</dd>
            </div>
          </dl>
        </article>

        <div className="grid gap-4 lg:grid-cols-2">
          <article className="card-elevated space-y-3">
            <h2 className="text-lg font-semibold text-neutral-900">{t("nano_details_download_title")}</h2>
            <p className="text-sm text-neutral-700">{t("nano_details_download_description")}</p>
            {!isAuthenticated && (
              <p className="text-sm text-neutral-700">{t("nano_details_download_requires_login")}</p>
            )}
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                void handleDownloadClick();
              }}
              disabled={isDownloading}
            >
              {isDownloading ? t("nano_details_downloading") : t("nano_details_download_button")}
            </button>
            {downloadError && <p className="text-sm text-error-600">{downloadError}</p>}
          </article>

          <article className="card-elevated space-y-3">
            <h2 className="text-lg font-semibold text-neutral-900">{t("nano_details_ratings_title")}</h2>
            {ratingsError && (
              <p className="text-sm text-error-600" role="alert">
                {ratingsError}
              </p>
            )}
            <dl className="space-y-2 text-sm text-neutral-700">
              <div className="flex items-center justify-between gap-3">
                <dt>{t("nano_details_avg_rating_label")}</dt>
                <dd className="font-medium">{ratingAverageLabel}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt>{t("nano_details_rating_count_label")}</dt>
                <dd className="font-medium">{ratingsState.aggregation.ratingCount}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt>{t("nano_details_download_count_label")}</dt>
                <dd className="font-medium">{detail.ratingSummary.downloadCount}</dd>
              </div>
            </dl>

            {!isPublished && <p className="text-sm text-neutral-700">{t("nano_details_feedback_unavailable")}</p>}

            {isPublished && (
              <div className="space-y-3 border-t border-neutral-200 pt-3">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-neutral-800">{t("nano_details_rating_prompt")}</p>
                  {!isAuthenticated && (
                    <p className="text-sm text-neutral-700">{t("nano_details_rating_login_prompt")}</p>
                  )}
                </div>

                {isRatingsLoading ? (
                  <p className="text-sm text-neutral-700">{t("nano_details_rating_loading")}</p>
                ) : (
                  <div className="flex flex-wrap gap-2" aria-label={t("nano_details_rating_widget_label")}>
                    {Array.from({ length: 5 }).map((_, index) => {
                      const score = index + 1;
                      const isActive = score <= (selectedRating ?? currentUserRating?.score ?? 0);

                      return (
                        <button
                          key={`rating-${score}`}
                          type="button"
                          className={`rounded-md border px-3 py-2 text-lg leading-none transition-colors ${
                            isActive
                              ? "border-warning-400 bg-warning-100 text-warning-700"
                              : "border-neutral-300 bg-white text-neutral-500 hover:border-primary-400 hover:text-primary-600"
                          }`}
                          aria-label={`${t("nano_details_rating_choose")}: ${score}`}
                          onClick={() => {
                            void handleRatingSelect(score);
                          }}
                          disabled={isRatingSubmitting}
                        >
                          {"★".repeat(score)}
                        </button>
                      );
                    })}
                  </div>
                )}

                {isRatingSubmitting && <p className="text-sm text-neutral-700">{t("nano_details_rating_submitting")}</p>}
                {ratingMessage && <p className="text-sm text-success-700">{ratingMessage}</p>}
                {ratingError && (
                  <p className="text-sm text-error-600" role="alert">
                    {ratingError}
                  </p>
                )}

                {currentUserRating && (
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm text-neutral-700">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p>
                        <span className="font-medium">{t("nano_details_your_rating_label")}</span>{" "}
                        {currentUserRating.score}/5
                      </p>
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${getFeedbackStatusClasses(currentUserRating.moderationStatus)}`}
                      >
                        {currentRatingStatus}
                      </span>
                    </div>
                    {currentRatingMessage && <p className="mt-2">{currentRatingMessage}</p>}
                  </div>
                )}
              </div>
            )}
          </article>
        </div>

        <article className="card-elevated space-y-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-neutral-900">{t("nano_details_chat_title")}</h2>
            <p className="text-sm text-neutral-700">{t("nano_details_chat_description")}</p>
          </div>

          {!isPublished && <p className="text-sm text-neutral-700">{t("nano_details_feedback_unavailable")}</p>}

          {isPublished && (
            <>
              <div className="space-y-2 rounded-md border border-neutral-200 bg-neutral-50 p-4">
                <label className="block space-y-2" htmlFor={commentFieldId}>
                  <span className="text-sm font-medium text-neutral-800">{t("nano_details_comment_label")}</span>
                  <textarea
                    id={commentFieldId}
                    className="min-h-28 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                    value={commentDraft}
                    onChange={(event) => setCommentDraft(event.target.value)}
                    placeholder={t("nano_details_comment_placeholder")}
                    disabled={isCommentSubmitting}
                  />
                </label>
                {!isAuthenticated && (
                  <p className="text-sm text-neutral-700">{t("nano_details_comment_login_prompt")}</p>
                )}
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => {
                      void handleCommentSubmit();
                    }}
                    disabled={isCommentSubmitting}
                  >
                    {isCommentSubmitting ? t("nano_details_comment_submitting") : t("nano_details_comment_submit")}
                  </button>
                  <button type="button" className="btn-outline" onClick={handleChatClick}>
                    {isAuthenticated ? t("nano_details_chat_button_open") : t("nano_details_chat_button_login")}
                  </button>
                </div>
                {commentMessage && <p className="text-sm text-success-700">{commentMessage}</p>}
                {commentError && (
                  <p className="text-sm text-error-600" role="alert">
                    {commentError}
                  </p>
                )}
              </div>

              {latestPendingComment && (
                <section className="rounded-md border border-warning-200 bg-warning-50 p-4 text-sm text-neutral-700">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold text-neutral-900">{t("nano_details_comment_pending_preview_title")}</h3>
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${getFeedbackStatusClasses(latestPendingComment.moderationStatus)}`}
                    >
                      {getFeedbackStatusLabel(latestPendingComment.moderationStatus, t)}
                    </span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap">{latestPendingComment.content}</p>
                  {getFeedbackStatusMessage(latestPendingComment.moderationStatus, "comment", t) && (
                    <p className="mt-2">{getFeedbackStatusMessage(latestPendingComment.moderationStatus, "comment", t)}</p>
                  )}
                </section>
              )}

              <section className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-base font-semibold text-neutral-900">{t("nano_details_comments_title")}</h3>
                  {commentsState.pagination.total_results > 0 && (
                    <p className="text-sm text-neutral-600">
                      {t("page_of")} {commentsState.pagination.current_page} {t("of")} {commentsState.pagination.total_pages}
                    </p>
                  )}
                </div>

                {isCommentsLoading && <p className="text-sm text-neutral-700">{t("nano_details_comments_loading")}</p>}
                {commentsError && (
                  <p className="text-sm text-error-600" role="alert">
                    {commentsError}
                  </p>
                )}
                {!isCommentsLoading && !commentsError && commentsState.comments.length === 0 && (
                  <p className="text-sm text-neutral-700">{t("nano_details_comments_empty")}</p>
                )}

                {!isCommentsLoading && commentsState.comments.length > 0 && (
                  <ul className="space-y-3">
                    {commentsState.comments.map((comment) => {
                      const authorLabel = comment.username ?? t("search_creator_fallback");
                      const updatedLabel = comment.updatedAt
                        ? formatTimestamp(comment.updatedAt, locale)
                        : t("search_not_available");

                      return (
                        <li key={comment.commentId} className="rounded-md border border-neutral-200 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-sm font-medium text-neutral-900">{authorLabel}</p>
                            <p className="text-xs text-neutral-500">{updatedLabel}</p>
                          </div>
                          <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-700">{comment.content}</p>
                          {comment.isEdited && (
                            <p className="mt-2 text-xs text-neutral-500">{t("nano_details_comment_edited")}</p>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}

                {commentsState.pagination.total_pages > 1 && (
                  <div className="flex gap-3">
                    <button
                      type="button"
                      className="btn-outline"
                      onClick={() => setCommentsPage((currentPage) => Math.max(1, currentPage - 1))}
                      disabled={!commentsState.pagination.has_prev_page || isCommentsLoading}
                    >
                      {t("prev")}
                    </button>
                    <button
                      type="button"
                      className="btn-outline"
                      onClick={() => setCommentsPage((currentPage) => currentPage + 1)}
                      disabled={!commentsState.pagination.has_next_page || isCommentsLoading}
                    >
                      {t("next")}
                    </button>
                  </div>
                )}
              </section>
            </>
          )}
        </article>

        <div>
          <Link to="/search" className="btn-outline inline-flex">
            {t("nano_details_back_to_search")}
          </Link>
        </div>
      </section>
    </PageLayout>
  );
}

export function LoginPage(): JSX.Element {
  return (
    <PageLayout>
      <LoginAuthPage />
    </PageLayout>
  );
}

export function RegisterPage(): JSX.Element {
  return (
    <PageLayout>
      <RegisterAuthPage />
    </PageLayout>
  );
}

export function VerifyEmailPage(): JSX.Element {
  return (
    <PageLayout>
      <VerifyEmailAuthPage />
    </PageLayout>
  );
}

export function DashboardPage(): JSX.Element {
  const { t } = useTranslation();
  return <PlaceholderPage title={t("dashboard_title")} description={t("dashboard_description")} />;
}

export function ProfilePage(): JSX.Element {
  const { t } = useTranslation();
  return <PlaceholderPage title={t("profile_title")} description={t("profile_description")} />;
}

export function AdminPage(): JSX.Element {
  const { t } = useTranslation();
  return <PlaceholderPage title={t("admin_title")} description={t("admin_description")} />;
}

export function TermsPage(): JSX.Element {
  return (
    <PageLayout>
      <TermsLegalPage />
    </PageLayout>
  );
}

export function PrivacyPage(): JSX.Element {
  return (
    <PageLayout>
      <PrivacyLegalPage />
    </PageLayout>
  );
}

export function NotFoundPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <PageLayout>
      <section className="card-elevated space-y-4">
        <div className="space-y-2">
          <h1 className="text-primary-600">{t("not_found_title")}</h1>
          <p className="text-base text-neutral-600">{t("not_found_description")}</p>
        </div>
        <div>
          <Link to="/" className="btn-outline">
            {t("not_found_back_home")}
          </Link>
        </div>
      </section>
    </PageLayout>
  );
}

export function ForbiddenPage(): JSX.Element {
  const { t } = useTranslation();
  return (
    <PageLayout>
      <section className="card-elevated space-y-4">
        <div className="space-y-2">
          <h1 className="text-primary-600">{t("forbidden_title")}</h1>
          <p className="text-base text-neutral-600">{t("forbidden_description")}</p>
        </div>
        <div className="flex gap-3">
          <Link to="/" className="btn-outline">
            {t("forbidden_back_home")}
          </Link>
          <Link to="/search" className="btn-primary">
            {t("forbidden_go_search")}
          </Link>
        </div>
      </section>
    </PageLayout>
  );
}

export function CreatorDashboardPage(): JSX.Element {
  return <CreatorDashboardPageComponent />;
}

export function UploadPage(): JSX.Element {
  return <UploadWizardPageComponent />;
}

export function EditNanoPage(): JSX.Element {
  return <EditNanoPageComponent />;
}

export function ModeratorQueuePage(): JSX.Element {
  return <ModeratorQueuePageComponent />;
}
