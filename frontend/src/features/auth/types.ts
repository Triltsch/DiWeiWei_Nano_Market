// Re-export core types from shared to avoid circular dependencies
export type { AuthTokens, AuthUser } from "../../shared/api/types";

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  username: string;
  email_verified: boolean;
}

export interface VerificationResponse {
  message: string;
  email: string;
}

export type PasswordStrengthLabel = "weak" | "medium" | "strong";
