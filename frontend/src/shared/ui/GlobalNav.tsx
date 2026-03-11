import { useCallback, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../features/auth";
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
        : "Account";

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
      aria-label="Global navigation"
    >
      <div className="container-main flex items-center justify-between min-h-56 py-3">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-4 text-primary-600 font-semibold hover:text-primary-700 transition-colors"
          aria-label="DiWeiWei Nano Market Home"
        >
          <img
            src="/logo.png"
            alt="DiWeiWei Nano Market Logo"
            className="h-56 w-auto object-contain"
          />
          <span className="hidden sm:inline text-2xl font-bold">DiWeiWei Nano Market</span>
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
              Search
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  to="/dashboard"
                  className={navLinkClass("/dashboard")}
                  aria-current={isActive("/dashboard") ? "page" : undefined}
                >
                  Dashboard
                </Link>
                <Link
                  to="/profile"
                  className={navLinkClass("/profile")}
                  aria-current={isActive("/profile") ? "page" : undefined}
                >
                  Profile
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
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className={navLinkClass("/login")}
                  aria-current={isActive("/login") ? "page" : undefined}
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-2 rounded-md text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
                >
                  Register
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
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-menu"
          >
            <span className="sr-only">{mobileMenuOpen ? "Close menu" : "Open menu"}</span>
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
          aria-label="Mobile navigation"
        >
          <div className="container-main py-4 space-y-2">
            <Link
              to="/search"
              className={navLinkClass("/search")}
              onClick={() => setMobileMenuOpen(false)}
              aria-current={isActive("/search") ? "page" : undefined}
            >
              Search
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  to="/dashboard"
                  className={navLinkClass("/dashboard")}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive("/dashboard") ? "page" : undefined}
                >
                  Dashboard
                </Link>
                <Link
                  to="/profile"
                  className={navLinkClass("/profile")}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive("/profile") ? "page" : undefined}
                >
                  Profile
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
                    Logout
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
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="block px-3 py-2 rounded-md text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Register
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
