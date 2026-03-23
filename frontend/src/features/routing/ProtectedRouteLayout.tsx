import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth";
import type { AuthRole } from "../../shared/api/types";

interface ProtectedRouteLayoutProps {
  requiredRoles?: readonly AuthRole[];
}

/**
 * Protected Route Layout
 *
 * Blocks unauthenticated access and redirects to login while preserving
 * intended destination in the redirect query parameter.
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
