import type { PropsWithChildren } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../features/auth";

/**
 * AppShell Component
 *
 * Main layout wrapper for the application.
 * Provides container constraints, responsive padding, and consistent spacing.
 */
export function AppShell({ children }: PropsWithChildren): JSX.Element {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <main className="container-main min-h-screen bg-neutral-50 space-y-6">
      <header className="card-elevated flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-primary-600 font-semibold">
            DiWeiWei Nano Market
          </Link>
          <Link to="/search">Search</Link>
          {isAuthenticated && <Link to="/dashboard">Dashboard</Link>}
        </div>

        <div className="flex items-center gap-3 text-sm text-neutral-700">
          {isAuthenticated ? (
            <>
              <span>{user?.username ?? user?.email}</span>
              <button
                type="button"
                className="btn-outline"
                onClick={() => {
                  void logout().then(() => {
                    navigate("/login");
                  });
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </header>

      {children}
    </main>
  );
}
