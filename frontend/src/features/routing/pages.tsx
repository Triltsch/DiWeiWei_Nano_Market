import type { PropsWithChildren } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  LoginPage as LoginAuthPage,
  RegisterPage as RegisterAuthPage,
  VerifyEmailPage as VerifyEmailAuthPage,
  useAuth,
} from "../auth";
import { PrivacyPage as PrivacyLegalPage, TermsPage as TermsLegalPage } from "../legal/pages";
import { AppShell } from "../../shared/ui/AppShell";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

function PageLayout({ children }: PropsWithChildren): JSX.Element {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const accountLabel =
    typeof user?.username === "string"
      ? user.username
      : typeof user?.email === "string"
        ? user.email
        : "Account";

  return (
    <AppShell
      headerStart={
        <>
          <Link to="/" className="text-primary-600 font-semibold">
            DiWeiWei Nano Market
          </Link>
          <Link to="/search">Search</Link>
          {isAuthenticated && <Link to="/dashboard">Dashboard</Link>}
        </>
      }
      headerEnd={
        isAuthenticated ? (
          <>
            <span>{accountLabel}</span>
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
        )
      }
    >
      {children}
    </AppShell>
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
  return (
    <PageLayout>
      <section className="space-y-6">
        <div className="card-elevated space-y-2">
          <h1 className="text-primary-600">DiWeiWei Nano Market</h1>
          <p className="text-base text-neutral-600">Frontend routing baseline for Story 8.1.</p>
        </div>
        <nav className="card-elevated">
          <h2 className="text-secondary-600">Available Placeholder Routes</h2>
          <ul className="mt-3 list-disc list-inside text-neutral-700 space-y-1">
            <li>
              <Link to="/search">/search</Link>
            </li>
            <li>
              <Link to="/nano/demo">/nano/:id</Link>
            </li>
            <li>
              <Link to="/login">/login</Link>
            </li>
            <li>
              <Link to="/register">/register</Link>
            </li>
            <li>
              <Link to="/verify-email">/verify-email</Link>
            </li>
            <li>
              <Link to="/dashboard">/dashboard</Link>
            </li>
            <li>
              <Link to="/profile">/profile</Link>
            </li>
            <li>
              <Link to="/admin">/admin</Link>
            </li>
          </ul>
        </nav>
      </section>
    </PageLayout>
  );
}

export function SearchPage(): JSX.Element {
  return (
    <PlaceholderPage
      title="Search"
      description="Search view placeholder for Sprint 3 implementation."
    />
  );
}

export function NanoDetailsPage(): JSX.Element {
  const params = useParams<{ id: string }>();
  const nanoId = params.id ?? "unknown";

  return (
    <PlaceholderPage
      title="Nano Details"
      description={`Detail route placeholder. Current nano id: ${nanoId}`}
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
  return <PlaceholderPage title="Dashboard" description="Protected dashboard placeholder route." />;
}

export function ProfilePage(): JSX.Element {
  return <PlaceholderPage title="Profile" description="Protected profile placeholder route." />;
}

export function AdminPage(): JSX.Element {
  return <PlaceholderPage title="Admin" description="Protected admin placeholder route." />;
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
  return (
    <PageLayout>
      <section className="card-elevated space-y-4">
        <div className="space-y-2">
          <h1 className="text-primary-600">Page Not Found</h1>
          <p className="text-base text-neutral-600">
            The requested route does not exist. Use navigation to return to known routes.
          </p>
        </div>
        <div>
          <Link to="/" className="btn-outline">
            Back to Home
          </Link>
        </div>
      </section>
    </PageLayout>
  );
}
