import { Route, Routes } from "react-router-dom";

import {
  AdminPage,
  CreatorDashboardPage,
  EditNanoPage,
  ForbiddenPage,
  HomePage,
  LoginPage,
  NanoDetailsPage,
  NotFoundPage,
  PrivacyPage,
  ProfilePage,
  RegisterPage,
  SearchPage,
  TermsPage,
  UploadPage,
  VerifyEmailPage,
  ModeratorQueuePage,
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
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/forbidden" element={<ForbiddenPage />} />

      <Route element={<ProtectedRouteLayout />}>
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      <Route
        element={<ProtectedRouteLayout requiredRoles={["creator", "moderator", "admin"]} />}
      >
        <Route path="/creator-dashboard" element={<CreatorDashboardPage />} />
        <Route path="/dashboard" element={<CreatorDashboardPage />} />
        <Route path="/nanos/:id/edit" element={<EditNanoPage />} />
        <Route path="/upload" element={<UploadPage />} />
      </Route>

      <Route element={<ProtectedRouteLayout requiredRoles={["moderator", "admin"]} />}>
        <Route path="/moderator/queue" element={<ModeratorQueuePage />} />
      </Route>

      <Route element={<ProtectedRouteLayout requiredRoles={["admin"]} />}>
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
