import type { PropsWithChildren } from "react";
import { Link, useParams } from "react-router-dom";

import {
  LoginPage as LoginAuthPage,
  RegisterPage as RegisterAuthPage,
  VerifyEmailPage as VerifyEmailAuthPage,
} from "../auth";
import { PrivacyPage as PrivacyLegalPage, TermsPage as TermsLegalPage } from "../legal/pages";
import { GlobalNav } from "../../shared/ui/GlobalNav";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

function PageLayout({ children }: PropsWithChildren): JSX.Element {
  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">{children}</main>
    </>
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
      {/* Hero Section */}
      <section className="space-y-8 py-12 md:py-20">
        <div className="space-y-6 text-center">
          <div className="flex justify-center">
            <img
              src="/logo.png"
              alt="DiWeiWei Nano Market Logo"
              className="h-[25rem] w-auto max-w-full object-contain shadow-lg"
            />
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold text-neutral-900">
              DiWeiWei Nano Market
            </h1>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto leading-relaxed">
              Der Marktplatz für Nano-Lerneinheiten. Hochwertige Schulungsinhalte austauschen,
              entdecken und weiterentwickeln – alles in einem Ökosystem für lebenslanges Lernen.
            </p>
          </div>

          {/* Call-to-Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link
              to="/register"
              className="px-8 py-3 rounded-lg text-center font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors shadow-md hover:shadow-lg"
            >
              Jetzt Registrieren
            </Link>
            <Link
              to="/search"
              className="px-8 py-3 rounded-lg text-center font-semibold bg-neutral-200 text-neutral-900 hover:bg-neutral-300 transition-colors shadow-md hover:shadow-lg"
            >
              Lerneinheiten Entdecken
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards Section */}
      <section className="space-y-8">
        <h2 className="text-3xl font-bold text-center text-neutral-900">Warum DiWeiWei?</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Feature Card 1 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">Hochwertige Inhalte</h3>
            <p className="text-neutral-600">
              Kurierte Nano-Lerneinheiten von Experten für schnelles, gezieltes Lernen.
            </p>
          </article>

          {/* Feature Card 2 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-secondary-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-secondary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">Einfach Teilbar</h3>
            <p className="text-neutral-600">
              Inhalte schnell hochladen, verwalten und mit der Community teilen.
            </p>
          </article>

          {/* Feature Card 3 */}
          <article className="card-elevated space-y-3 hover:shadow-lg transition-shadow">
            <div className="h-12 w-12 rounded-lg bg-accent-100 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-accent-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900">Schneller Zugriff</h3>
            <p className="text-neutral-600">
              Mobil-optimiert und blitzschnell. Lernen Sie jederzeit und überall.
            </p>
          </article>
        </div>
      </section>

      {/* Secondary CTA Section */}
      <section className="rounded-lg bg-gradient-to-r from-primary-50 to-secondary-50 p-8 md:p-12 text-center space-y-4">
        <h2 className="text-2xl font-bold text-neutral-900">
          Sie sind Inhalts-Creator oder Trainer?
        </h2>
        <p className="text-neutral-600 max-w-xl mx-auto">
          Teilen Sie Ihre Expertise als Nano-Lerneinheiten und erreichen Sie ein globales Publikum.
        </p>
        <div>
          <Link
            to="/register"
            className="inline-block px-6 py-2 rounded-lg font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            Als Creator Beitreten
          </Link>
        </div>
      </section>

      {/* Footer Info */}
      <section className="border-t border-neutral-200 pt-8 space-y-4 text-center text-sm text-neutral-600">
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link to="/terms" className="hover:text-primary-600 transition-colors">
            Nutzungsbedingungen
          </Link>
          <span className="hidden sm:inline">•</span>
          <Link to="/privacy" className="hover:text-primary-600 transition-colors">
            Datenschutz
          </Link>
        </div>
        <p>
          © 2026 DiWeiWei Nano Market. Alle Rechte vorbehalten. | Sprint 3 Launch
        </p>
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
