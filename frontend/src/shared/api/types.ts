/**
 * Shared API Type Definitions
 *
 * Core types used across the API and auth layers to avoid circular dependencies
 * between shared and feature layers.
 */

/**
 * JWT tokens returned from authentication endpoints.
 */
export type AuthTokens = {
  /**
   * Short-lived token used for authenticating API requests.
   */
  accessToken: string;
  /**
   * Long-lived token used to obtain new access tokens.
   */
  refreshToken: string;
  /**
   * Expiration time in seconds for the access token.
   */
  expiresIn: number;
};

/**
 * Serialized representation of the authenticated user stored in localStorage.
 *
 * The exact shape is intentionally broad here because this module only
 * persists and retrieves the value without inspecting its properties.
 */
export type AuthUser = Record<string, unknown>;
