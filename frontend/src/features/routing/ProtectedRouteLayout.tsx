import { Outlet } from "react-router-dom";

/**
 * Protected Route Layout
 *
 * Sprint 2 scaffold: route grouping is in place so Sprint 3 can add
 * authentication/authorization checks without restructuring routes.
 */
export function ProtectedRouteLayout(): JSX.Element {
  return <Outlet />;
}
