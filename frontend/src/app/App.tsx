import { AppShell } from "../shared/ui/AppShell";

/**
 * Main App Component for DiWeiWei Nano-Marktplatz
 *
 * Provides the root layout and bootstraps the feature modules.
 * Uses Tailwind CSS design tokens for styling.
 */
export function App(): JSX.Element {
  return (
    <AppShell>
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-primary-600">DiWeiWei Nano Market</h1>
          <p className="text-base text-neutral-600">
            Frontend baseline with Tailwind CSS and design tokens ready for Sprint 2 feature modules.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card-elevated">
            <h3 className="text-secondary-600">Design System</h3>
            <p className="text-sm text-neutral-600 mt-2">
              Tailwind CSS with custom color palette, typography scales, and component tokens.
            </p>
          </div>

          <div className="card-elevated">
            <h3 className="text-secondary-600">Ready to Build</h3>
            <p className="text-sm text-neutral-600 mt-2">
              React 18, TypeScript, and Vite are configured. Create components using design tokens.
            </p>
          </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button className="btn-primary">Get Started</button>
          <button className="btn-outline">Learn More</button>
        </div>
      </div>
    </AppShell>
  );
}
