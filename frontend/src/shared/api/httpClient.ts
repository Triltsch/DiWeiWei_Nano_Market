/**
 * HTTP Client - Centralized Axios Instance
 *
 * Provides a configured Axios client for all API communication.
 *
 * Features:
 * - Environment-based configuration (base URL, timeout)
 * - Automatic JWT token injection in request headers
 * - Error handling with placeholder for token refresh (Sprint 3)
 * - Request/response logging in development mode
 *
 * Usage:
 * ```typescript
 * import { httpClient } from "../shared/api/httpClient"
 *
 * // Make authenticated request - token is automatically injected
 * const response = await httpClient.get("/api/v1/auth/me")
 *
 * // POST request with data
 * const data = await httpClient.post("/api/v1/auth/login", {
 *   email: "user@example.com",
 *   password: "password123"
 * })
 * ```
 */

import axios from "axios";

import { API_CONFIG } from "./config";
import { setupInterceptors } from "./interceptors";

/**
 * Create and configure centralized HTTP client
 */
function createHttpClient() {
  const instance = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.REQUEST_TIMEOUT,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Setup interceptors for token injection and error handling
  setupInterceptors(instance);

  return instance;
}

/**
 * Singleton HTTP client instance
 * Reused for all API requests in the application
 */
export const httpClient = createHttpClient();

export default httpClient;
