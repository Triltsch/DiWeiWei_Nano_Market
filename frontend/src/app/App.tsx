import { AppRouter } from "./router";

/**
 * Main App Component for DiWeiWei Nano-Marktplatz
 *
 * Provides the root layout and bootstraps the feature modules.
 * Uses Tailwind CSS design tokens for styling.
 */
export function App(): JSX.Element {
  return <AppRouter />;
}
