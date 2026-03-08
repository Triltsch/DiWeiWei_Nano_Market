/**
 * App Providers - Centralized Provider Composition
 *
 * Composes all application-level providers in a single component:
 * - React Query QueryClientProvider for async state management
 * - BrowserRouter for client-side routing
 *
 * This component wraps the entire app to ensure all providers are available
 * to any component in the tree.
 *
 * Usage in main.tsx:
 * ```tsx
 * ReactDOM.createRoot(document.getElementById("root")).render(
 *   <React.StrictMode>
 *     <AppProviders>
 *       <App />
 *     </AppProviders>
 *   </React.StrictMode>
 * )
 * ```
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import { queryClient } from "../shared/queryClient";

interface AppProvidersProps {
  /**
   * Child components to wrap with providers
   */
  children: React.ReactNode;
}

/**
 * Compose all app-level providers
 *
 * @param children - Child components to wrap
 * @returns Provider-wrapped children
 */
export function AppProviders({ children }: AppProvidersProps): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

export default AppProviders;
