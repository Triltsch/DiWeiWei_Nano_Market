/**
 * API Module Exports
 *
 * Central export point for HTTP client, query hooks, and related utilities.
 */

export { httpClient } from "./httpClient";
export { API_CONFIG, validateApiConfig } from "./config";
export {
  setupInterceptors,
  setupRequestInterceptor,
  setupResponseInterceptor,
} from "./interceptors";
export { useUserProfile } from "./useUserProfile";
export { normalizeSearchLevel, searchNanos } from "./search";
export {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  setAuthSession,
  updateAuthTokens,
} from "./authSession";
export type { AuthTokens, AuthUser } from "./types";
export type { SearchFilters, SearchNano, SearchRequest, SearchResponse } from "./search";
