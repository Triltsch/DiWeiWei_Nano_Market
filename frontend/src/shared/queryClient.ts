/**
 * React Query Client Configuration
 *
 * Centralized configuration for React Query with sensible defaults:
 * - Stale time: 1 minute (data considered fresh for 1 minute)
 * - Cache time: 5 minutes (data retained for 5 minutes after no references)
 * - Retry count: 1 (retry once on failure, then give up)
 * - Retry delay: exponential backoff (1000ms, 2000ms, 4000ms...)
 *
 * These defaults balance between:
 * - User experience (fresh data, quick feedback)
 * - Network efficiency (reduced redundant requests)
 * - Server load (controlled retry behavior)
 */

import { QueryClient } from "@tanstack/react-query";

/**
 * Create and configure the React Query client
 *
 * @returns Configured QueryClient instance
 */
function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Retry failed queries once before giving up
        retry: 1,
        // Data is considered fresh for 1 minute
        staleTime: 1000 * 60,
        // Keep cached data for 5 minutes, then garbage collect
        gcTime: 1000 * 60 * 5,
        // Retry with exponential backoff: 1s, 2s, 4s...
        retryDelay: (attemptIndex) => {
          return Math.min(1000 * Math.pow(2, attemptIndex), 30000);
        },
      },
      mutations: {
        // Mutations retry once by default
        retry: 1,
        // Retry mutations with exponential backoff
        retryDelay: (attemptIndex) => {
          return Math.min(1000 * Math.pow(2, attemptIndex), 30000);
        },
      },
    },
  });
}

/**
 * Global React Query client instance
 * Used by QueryClientProvider in app root
 */
export const queryClient = createQueryClient();

export default queryClient;
