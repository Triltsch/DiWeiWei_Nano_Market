/**
 * HTTP Request/Response Interceptors
 *
 * Handles:
 * - JWT access token injection in Authorization header
 * - Response error handling with placeholder for token refresh
 * - Request logging in development mode
 */

import type { AxiosError, AxiosInstance, AxiosResponse } from "axios";

/**
 * Type for access token stored in localStorage
 */
interface TokenStorage {
  accessToken?: string;
  refreshToken?: string;
  expiresIn?: number;
}

/**
 * Setup request interceptor for token injection
 *
 * Injects the JWT access token into the Authorization header if it exists.
 * The token is retrieved from localStorage under the key "auth_tokens".
 *
 * Token Format: Bearer <jwt_token>
 *
 * @param instance - Axios instance to configure
 */
export function setupRequestInterceptor(instance: AxiosInstance): void {
  instance.interceptors.request.use(
    (config) => {
      // Get tokens from localStorage
      const storedTokens = localStorage.getItem("auth_tokens");

      if (storedTokens) {
        try {
          const tokens: TokenStorage = JSON.parse(storedTokens);

          // Inject access token into Authorization header if available
          if (tokens.accessToken) {
            config.headers.Authorization = `Bearer ${tokens.accessToken}`;
          }
        } catch (error) {
          // Silently ignore JSON parsing errors
          // localStorage could be corrupted, but request can still proceed
          console.debug("Failed to parse stored tokens:", error);
        }
      }

      // Log requests in development mode
      if (import.meta.env.DEV) {
        console.debug(
          `[API] ${config.method?.toUpperCase()} ${config.url}`,
          config.data || ""
        );
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
}

/**
 * Setup response interceptor for error handling
 *
 * Handles HTTP errors with a placeholder for token refresh logic:
 * - On 401 Unauthorized: Prepared to refresh token (Sprint 3)
 * - On other errors: Pass through normal error handling
 *
 * @param instance - Axios instance to configure
 */
export function setupResponseInterceptor(instance: AxiosInstance): void {
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log successful responses in development mode
      if (import.meta.env.DEV) {
        console.debug(`[API] Response ${response.status}:`, response.data);
      }

      return response;
    },
    async (error: AxiosError) => {
      // Reserved for token refresh/retry logic (Sprint 3)
      const _originalRequest = error.config;

      // Handle 401 Unauthorized errors
      if (error.response?.status === 401) {
        console.warn("[API] Unauthorized request - 401");

        // PLACEHOLDER: Token Refresh Logic (Sprint 3)
        // This is prepared for Sprint 3 implementation:
        //
        // 1. Get refresh token from localStorage
        // 2. Call POST /api/v1/auth/refresh-token with refresh token
        // 3. Store new access token in localStorage
        // 4. Retry original request with new token
        //
        // For now, we clear tokens and let the app redirect to login
        localStorage.removeItem("auth_tokens");

        // Optional: Emit event for app to redirect to login
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
      }

      // Log errors in development mode
      if (import.meta.env.DEV) {
        console.error(
          `[API] Error ${error.response?.status || "unknown"}:`,
          error.message
        );
      }

      return Promise.reject(error);
    }
  );
}

/**
 * Setup all interceptors
 *
 * @param instance - Axios instance to configure
 */
export function setupInterceptors(instance: AxiosInstance): void {
  setupRequestInterceptor(instance);
  setupResponseInterceptor(instance);
}
