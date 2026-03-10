import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth";

/**
 * Protected Route Layout
 *
 * Blocks unauthenticated access and redirects to login while preserving
 * intended destination in the redirect query parameter.
 */
export function ProtectedRouteLayout(): JSX.Element {
  const location = useLocation();
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <p className="text-neutral-600">Checking authentication...</p>;
  }

  if (!isAuthenticated) {
    const redirectTarget = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?redirect=${encodeURIComponent(redirectTarget)}`} replace />;
  }

  return <Outlet />;
}
