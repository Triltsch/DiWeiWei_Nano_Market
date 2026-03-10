import type { PropsWithChildren, ReactNode } from "react";

/**
 * AppShell Component
 *
 * Main layout wrapper for the application.
 * Provides container constraints, responsive padding, and consistent spacing.
 * Header content is injected so the shared layer stays independent from feature logic.
 */
export interface AppShellProps extends PropsWithChildren {
  headerStart?: ReactNode;
  headerEnd?: ReactNode;
}

export function AppShell({ children, headerStart, headerEnd }: AppShellProps): JSX.Element {

  return (
    <main className="container-main min-h-screen bg-neutral-50 space-y-6">
      <header className="card-elevated flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">{headerStart}</div>

        <div className="flex items-center gap-3 text-sm text-neutral-700">{headerEnd}</div>
      </header>

      {children}
    </main>
  );
}
