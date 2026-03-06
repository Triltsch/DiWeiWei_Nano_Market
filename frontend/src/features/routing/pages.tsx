import type { PropsWithChildren } from "react";
import { Link, useParams } from "react-router-dom";

import { AppShell } from "../../shared/ui/AppShell";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

function PageLayout({ children }: PropsWithChildren): JSX.Element {
  return <AppShell>{children}</AppShell>;
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
  return <PlaceholderPage title="Search" description="Search view placeholder for Sprint 3 implementation." />;
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
  return <PlaceholderPage title="Login" description="Authentication login placeholder route." />;
}

export function RegisterPage(): JSX.Element {
  return <PlaceholderPage title="Register" description="Authentication registration placeholder route." />;
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
