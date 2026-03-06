/**
 * User Profile Query Hook - Sample React Query Integration
 *
 * This hook demonstrates React Query integration for fetching user profile data.
 * Used as a smoke test to validate React Query + app providers are wired correctly.
 *
 * The hook:
 * - Uses React Query's useQuery to manage async state
 * - Automatically handles loading, error, and data states
 * - Caches data per React Query config defaults (1 minute stale time)
 * - Integrates with the centralized httpClient for API calls
 *
 * Usage in components:
 * ```tsx
 * function Profile() {
 *   const { data: profile, isLoading, error } = useUserProfile();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return <div>Hello {profile.name}</div>;
 * }
 * ```
 */

import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import { httpClient } from "./httpClient";

/**
 * User profile data structure
 */
interface UserProfile {
  id: string;
  email: string;
  name?: string;
  created_at?: string;
}

/**
 * Query key for user profile - used by React Query for caching
 */
const USER_PROFILE_QUERY_KEY = ["auth", "profile"];

/**
 * Fetch user profile from backend
 * This is called by the useUserProfile hook
 */
async function fetchUserProfile(): Promise<UserProfile> {
  const response = await httpClient.get<UserProfile>("/api/v1/auth/me");
  return response.data;
}

/**
 * Hook to fetch current user profile
 *
 * Returns React Query state:
 * - data: User profile object (undefined while loading)
 * - isLoading: True while fetching
 * - isError: True if request failed
 * - error: Error object if request failed
 *
 * @returns Query state and user profile data
 */
export function useUserProfile() {
  return useQuery<UserProfile, AxiosError>({
    queryKey: USER_PROFILE_QUERY_KEY,
    queryFn: fetchUserProfile,
    // Don't automatically fetch - let component decide when to load
    enabled: false,
  });
}

export default useUserProfile;
