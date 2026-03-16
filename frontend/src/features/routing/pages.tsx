import { useEffect, useMemo, useState, type PropsWithChildren } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import {
  LoginPage as LoginAuthPage,
  RegisterPage as RegisterAuthPage,
  VerifyEmailPage as VerifyEmailAuthPage,
} from "../auth";
import { PrivacyPage as PrivacyLegalPage, TermsPage as TermsLegalPage } from "../legal/pages";
import { searchNanos, type SearchFilters, type SearchNano } from "../../shared/api";
import { useTranslation } from "../../shared/i18n";
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

export function SearchPage(): JSX.Element {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialState = useMemo(() => {
    return {
      query: searchParams.get("q") ?? "",
      filters: {
        category: searchParams.get("category") ?? "",
        level: searchParams.get("level") ?? "",
        duration: searchParams.get("duration") ?? "",
        language: searchParams.get("language") ?? "",
      },
    };
  }, [searchParams]);

  const [queryInput, setQueryInput] = useState(initialState.query);
  const [debouncedQuery, setDebouncedQuery] = useState(initialState.query);
  const [filters, setFilters] = useState<SearchFilters>(initialState.filters);
  const [results, setResults] = useState<SearchNano[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [lastPageCount, setLastPageCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const pageSize = 20;
  const debounceMs = 300;

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedQuery(queryInput.trim());
    }, debounceMs);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [queryInput]);

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

    setSearchParams(nextParams, { replace: true });
  }, [filters, queryInput, setSearchParams]);

  useEffect(() => {
    let isActive = true;

    const fetchFirstPage = async (): Promise<void> => {
      setIsLoading(true);

      try {
        const response = await searchNanos({
          query: debouncedQuery,
          filters,
          limit: pageSize,
          offset: 0,
        });

        if (!isActive) {
          return;
        }

        setResults(response.items);
        setTotal(response.total);
        setLastPageCount(response.items.length);
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
  }, [debouncedQuery, filters]);

  const hasMore = total === null ? lastPageCount === pageSize : results.length < total;

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
        limit: pageSize,
        offset: results.length,
      });

      setResults((current) => [...current, ...response.items]);
      setTotal(response.total);
      setLastPageCount(response.items.length);
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
                <option value="beginner">{t("search_level_beginner")}</option>
                <option value="intermediate">{t("search_level_intermediate")}</option>
                <option value="advanced">{t("search_level_advanced")}</option>
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
                <option value="0-15">0-15 min</option>
                <option value="15-30">15-30 min</option>
                <option value="30+">30+ min</option>
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

            {!isLoading && results.length === 0 && (
              <div className="card-elevated">
                <p className="text-neutral-700">{t("search_empty")}</p>
              </div>
            )}

            {!isLoading && results.length > 0 && (
              <>
                <ul className="space-y-3">
                  {results.map((item) => (
                    <li key={item.id} className="card-elevated space-y-2">
                      <h3 className="text-lg font-semibold text-neutral-900">{item.title}</h3>
                      <div className="grid gap-2 text-sm text-neutral-700 sm:grid-cols-2">
                        <p>
                          <span className="font-medium">{t("search_creator_label")}</span> {item.creator}
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
  const { t } = useTranslation();
  const params = useParams<{ id: string }>();
  const nanoId = params.id ?? "unknown";

  return (
    <PlaceholderPage
      title={t("nano_details_title")}
      description={t("nano_details_description").replace("{id}", nanoId)}
    />
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
