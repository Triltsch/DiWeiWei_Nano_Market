import axios from "axios";

import { httpClient } from "../../shared/api/httpClient";
import type {
  AuthTokens,
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
  VerificationResponse,
} from "./types";

interface ApiErrorResponse {
  detail?: string;
}

export type AuthErrorCode =
  | "connection-error"
  | "request-failed"
  | "email-already-registered"
  | "username-already-taken"
  | "accept-terms-required"
  | "accept-privacy-required"
  | "password-too-short"
  | "password-uppercase-required"
  | "password-digit-required"
  | "password-special-required"
  | "service-unavailable"
  | "unknown";

const AUTH_ERROR_CODES: Record<string, AuthErrorCode> = {
  "Connection error. Please try again.": "connection-error",
  "Request failed. Please try again.": "request-failed",
  "Email already registered": "email-already-registered",
  "Username already taken": "username-already-taken",
  "You must accept the Terms of Service to register": "accept-terms-required",
  "You must accept the Privacy Policy to register": "accept-privacy-required",
  "Password must be at least 8 characters": "password-too-short",
  "Password must contain at least one uppercase letter": "password-uppercase-required",
  "Password must contain at least one digit": "password-digit-required",
  "Password must contain at least one special character": "password-special-required",
  "Service temporarily unavailable. Please try again later.": "service-unavailable",
};

function getErrorCode(error: unknown): AuthErrorCode {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    if (!error.response) {
      return "connection-error";
    }

    const detail = error.response.data?.detail;
    if (detail && detail in AUTH_ERROR_CODES) {
      return AUTH_ERROR_CODES[detail];
    }

    if (error.response.status === 503) {
      return "service-unavailable";
    }

    return "request-failed";
  }

  return "unknown";
}

function getRegisterErrorCode(error: unknown): AuthErrorCode {
  if (axios.isAxiosError<ApiErrorResponse>(error) && error.response?.status === 409) {
    const detail = error.response.data?.detail;
    if (detail && detail in AUTH_ERROR_CODES) {
      return AUTH_ERROR_CODES[detail];
    }

    return "request-failed";
  }

  return getErrorCode(error);
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    if (!error.response) {
      return "Connection error. Please try again.";
    }

    return error.response.data?.detail ?? "Request failed. Please try again.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed. Please try again.";
}

export class AuthApiError extends Error {
  code: AuthErrorCode;

  constructor(message: string, code: AuthErrorCode = "unknown") {
    super(message);
    this.name = "AuthApiError";
    this.code = code;
  }
}

export async function registerUser(payload: RegisterPayload): Promise<RegisterResponse> {
  try {
    const response = await httpClient.post<RegisterResponse>("/api/v1/auth/register", {
      email: payload.email,
      username: payload.username,
      password: payload.password,
      accept_terms: payload.acceptTerms,
      accept_privacy: payload.acceptPrivacy,
    });

    return response.data;
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getRegisterErrorCode(error));
  }
}

export async function loginUser(payload: LoginPayload): Promise<AuthTokens> {
  try {
    const response = await httpClient.post<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }>("/api/v1/auth/login", payload);

    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      expiresIn: response.data.expires_in,
    };
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function refreshToken(refreshTokenValue: string): Promise<AuthTokens> {
  try {
    const response = await httpClient.post<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }>("/api/v1/auth/refresh-token", {
      refresh_token: refreshTokenValue,
    });

    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      expiresIn: response.data.expires_in,
    };
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function logoutUser(refreshTokenValue: string): Promise<void> {
  try {
    await httpClient.post("/api/v1/auth/logout", {
      refresh_token: refreshTokenValue,
    });
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function verifyEmail(token: string): Promise<VerificationResponse> {
  try {
    const response = await httpClient.post<VerificationResponse>("/api/v1/auth/verify-email", {
      token,
    });

    return response.data;
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function resendVerificationEmail(email: string): Promise<VerificationResponse> {
  try {
    const response = await httpClient.post<VerificationResponse>(
      "/api/v1/auth/resend-verification-email",
      { email }
    );

    return response.data;
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error), getErrorCode(error));
  }
}
