import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth";
import type { AuthRole } from "../../shared/api/types";

interface ProtectedRouteLayoutProps {
  requiredRoles?: readonly AuthRole[];
}

/**
 * Protected Route Layout
 *
 * Guards routes by enforcing authentication and optional role-based authorization.
 *
 * - If the user is not authenticated, redirects to the login page while preserving
 *   the intended destination in the `redirect` query parameter.
 * - If `requiredRoles` is provided and the authenticated user's role is not included,
 *   redirects to the `/forbidden` page.
 */
export function ProtectedRouteLayout({ requiredRoles }: ProtectedRouteLayoutProps): JSX.Element {
  const location = useLocation();
  const { isLoading, isAuthenticated, user } = useAuth();

  if (isLoading) {
    return <p className="text-neutral-600">Checking authentication...</p>;
  }

  if (!isAuthenticated) {
    const redirectTarget = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?redirect=${encodeURIComponent(redirectTarget)}`} replace />;
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const currentRole = user?.role ?? "consumer";
    if (!requiredRoles.includes(currentRole)) {
      return <Navigate to="/forbidden" replace />;
    }
  }

  return <Outlet />;
}
