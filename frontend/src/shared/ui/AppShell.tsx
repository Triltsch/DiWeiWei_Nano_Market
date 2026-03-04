import type { PropsWithChildren } from "react";

/**
 * AppShell Component
 *
 * Main layout wrapper for the application.
 * Provides container constraints, responsive padding, and consistent spacing.
 *
 * Uses Tailwind CSS classes referencing design tokens:
 * - container-main: max-width with responsive padding
 * - min-h-screen: ensures full viewport height
 * - bg-neutral-50: baseline background color from design tokens
 */
export function AppShell({ children }: PropsWithChildren): JSX.Element {
  return <main className="container-main min-h-screen bg-neutral-50">{children}</main>;
}
