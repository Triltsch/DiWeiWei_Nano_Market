export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthUser {
  email: string;
  username?: string;
}

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
