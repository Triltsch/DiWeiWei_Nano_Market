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

export type AuthRole = "consumer" | "creator" | "moderator" | "admin";

/**
 * Serialized representation of the authenticated user stored in localStorage.
 *
 * This interface defines the expected structure of the stored user object.
 * Additional optional fields may be added over time, but existing fields
 * (`email`, `role`, `username`, `id`) are part of the public contract.
 */
export interface AuthUser {
  email: string;
  role?: AuthRole;
  username?: string;
  id?: string;
}
