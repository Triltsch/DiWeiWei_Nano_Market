import { Route, Routes } from "react-router-dom";

import {
  AdminPage,
  DashboardPage,
  HomePage,
  LoginPage,
  NanoDetailsPage,
  NotFoundPage,
  ProfilePage,
  RegisterPage,
  SearchPage,
} from "../features/routing/pages";
import { ProtectedRouteLayout } from "../features/routing/ProtectedRouteLayout";

/**
 * App Router
 *
 * Provides the Sprint 2 base route map and keeps the route hierarchy
 * ready for auth-guard enforcement in Sprint 3.
 *
 * Note: BrowserRouter wrapper is provided by AppProviders in main.tsx
 */
export function AppRouter(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/nano/:id" element={<NanoDetailsPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRouteLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
