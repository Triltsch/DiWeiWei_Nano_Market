/**
 * API Configuration
 *
 * Centralized configuration for HTTP client, loaded from environment variables.
 * Provides base URL, request timeout, and other API settings.
 *
 * Environment Variables:
 * - VITE_API_BASE_URL: Base URL for API requests (default: http://localhost:8000)
 * - VITE_API_REQUEST_TIMEOUT: Request timeout in milliseconds (default: 30000)
 */

export const API_CONFIG = {
  /**
   * Base URL for API requests
   * Loaded from VITE_API_BASE_URL environment variable
   * Defaults to localhost:8000 for development
   */
  BASE_URL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",

  /**
   * Request timeout in milliseconds
   * Loaded from VITE_API_REQUEST_TIMEOUT environment variable
   * Defaults to 30 seconds
   */
  REQUEST_TIMEOUT: import.meta.env.VITE_API_REQUEST_TIMEOUT
    ? parseInt(import.meta.env.VITE_API_REQUEST_TIMEOUT as string, 10)
    : 30000,

  /**
   * API version prefix
   * Used to construct endpoint paths like /api/v1/{endpoint}
   */
  VERSION: "v1",
} as const;

/**
 * Validate API configuration
 * Called on module load to ensure all required configuration is present
 */
export function validateApiConfig(): void {
  // Check if environment variable was explicitly set (not using default)
  if (!import.meta.env.VITE_API_BASE_URL) {
    console.warn(
      "API_CONFIG: VITE_API_BASE_URL is not set. Using default: http://localhost:8000"
    );
  }

  if (API_CONFIG.REQUEST_TIMEOUT < 1000) {
    console.warn(
      "API_CONFIG: REQUEST_TIMEOUT is very low (" +
        API_CONFIG.REQUEST_TIMEOUT +
        "ms). Consider increasing it."
    );
  }
}

// Validate configuration on module load
if (import.meta.env.DEV) {
  validateApiConfig();
}
