import { useCallback, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../features/auth";
import { useTranslation } from "../i18n";
import { LanguageSelector } from "./LanguageSelector";

/**
 * GlobalNav Component
 *
 * Main navigation bar for the application.
 * Adapts based on authentication state and device size.
 * - Desktop: horizontal menu with all nav items
 * - Mobile: hamburger menu with collapsible navigation
 * - Active routes are highlighted with visual indicator
 * - Language selector available in both desktop and mobile views
 *
 * Accessibility:
 * - Semantic nav element with proper ARIA labels
 * - Hamburger button has proper aria-label and aria-expanded
 * - Active links indicated both visually and semantically
 */
export function GlobalNav(): JSX.Element {
  const { isAuthenticated, user, logout } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = useCallback(async () => {
    setMobileMenuOpen(false);
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }, [logout, navigate]);

  const isActive = (path: string): boolean => {
    return location.pathname === path;
  };

  const accountLabel =
    typeof user?.username === "string"
      ? user.username
      : typeof user?.email === "string"
        ? user.email
        : t("nav_fallback_account");

  const navLinkClass = (path: string): string => {
    const base = "px-3 py-2 rounded-md text-sm font-medium transition-colors";
    const active = isActive(path)
      ? "bg-primary-100 text-primary-700 font-semibold underline"
      : "text-neutral-700 hover:bg-neutral-100";
    return `${base} ${active}`;
  };

  return (
    <nav
      className="sticky top-0 z-50 bg-white border-b border-neutral-200 shadow-sm"
      aria-label={t("nav_aria_global")}
    >
      <div className="container-main flex items-center justify-between min-h-14 py-3">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-4 text-primary-600 font-semibold hover:text-primary-700 transition-colors"
          aria-label={t("nav_home_aria")}
          onClick={() => setMobileMenuOpen(false)}
        >
          <img
            src={t("logo_src")}
            alt={t("logo_alt")}
            className="h-16 w-auto object-contain"
          />
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          {/* Main nav items */}
          <div className="flex items-center gap-2">
            <Link
              to="/search"
              className={navLinkClass("/search")}
              aria-current={isActive("/search") ? "page" : undefined}
            >
              {t("nav_search")}
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  to="/dashboard"
                  className={navLinkClass("/dashboard")}
                  aria-current={isActive("/dashboard") ? "page" : undefined}
                >
                  {t("nav_dashboard")}
                </Link>
                <Link
                  to="/profile"
                  className={navLinkClass("/profile")}
                  aria-current={isActive("/profile") ? "page" : undefined}
                >
                  {t("nav_profile")}
                </Link>
              </>
            )}
          </div>

          {/* Language Selector */}
          <div className="border-l border-neutral-200 pl-6">
            <LanguageSelector />
          </div>

          {/* Authentication items */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-neutral-600">{accountLabel}</span>
                <button
                  type="button"
                  className="px-3 py-2 rounded-md text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
                  onClick={handleLogout}
                >
                  {t("nav_logout")}
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className={navLinkClass("/login")}
                  aria-current={isActive("/login") ? "page" : undefined}
                >
                  {t("nav_login")}
                </Link>
                <Link
                  to="/register"
                  className={navLinkClass("/register")}
                  aria-current={isActive("/register") ? "page" : undefined}
                >
                  {t("nav_register")}
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Mobile Menu Button + Language Selector */}
        <div className="md:hidden flex items-center gap-3">
          <LanguageSelector />
          <button
            type="button"
            className="p-2 rounded-md hover:bg-neutral-100 transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? t("nav_menu_close") : t("nav_menu_open")}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-menu"
          >
            <span className="sr-only">{mobileMenuOpen ? t("nav_menu_close") : t("nav_menu_open")}</span>
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-menu"
          className="md:hidden border-t border-neutral-200 bg-neutral-50"
          role="region"
          aria-label={t("nav_mobile_region")}
        >
          <div className="container-main py-4 space-y-2">
            <Link
              to="/search"
              className={navLinkClass("/search")}
              onClick={() => setMobileMenuOpen(false)}
              aria-current={isActive("/search") ? "page" : undefined}
            >
              {t("nav_search")}
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  to="/dashboard"
                  className={navLinkClass("/dashboard")}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive("/dashboard") ? "page" : undefined}
                >
                  {t("nav_dashboard")}
                </Link>
                <Link
                  to="/profile"
                  className={navLinkClass("/profile")}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive("/profile") ? "page" : undefined}
                >
                  {t("nav_profile")}
                </Link>
              </>
            )}

            <div className="border-t border-neutral-200 pt-2 mt-2">
              {isAuthenticated ? (
                <>
                  <div className="px-3 py-2 text-sm font-medium text-neutral-700">
                    {accountLabel}
                  </div>
                  <button
                    type="button"
                    className="w-full text-left px-3 py-2 rounded-md text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
                    onClick={handleLogout}
                  >
                    {t("nav_logout")}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className={navLinkClass("/login")}
                    onClick={() => setMobileMenuOpen(false)}
                    aria-current={isActive("/login") ? "page" : undefined}
                  >
                    {t("nav_login")}
                  </Link>
                  <Link
                    to="/register"
                    className={navLinkClass("/register")}
                    onClick={() => setMobileMenuOpen(false)}
                    aria-current={isActive("/register") ? "page" : undefined}
                  >
                    {t("nav_register")}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
