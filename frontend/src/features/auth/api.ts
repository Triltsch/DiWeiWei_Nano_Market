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
  constructor(message: string) {
    super(message);
    this.name = "AuthApiError";
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
    throw new AuthApiError(getErrorMessage(error));
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
    throw new AuthApiError(getErrorMessage(error));
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
    throw new AuthApiError(getErrorMessage(error));
  }
}

export async function logoutUser(refreshTokenValue: string): Promise<void> {
  try {
    await httpClient.post("/api/v1/auth/logout", {
      refresh_token: refreshTokenValue,
    });
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error));
  }
}

export async function verifyEmail(token: string): Promise<VerificationResponse> {
  try {
    const response = await httpClient.post<VerificationResponse>("/api/v1/auth/verify-email", {
      token,
    });

    return response.data;
  } catch (error) {
    throw new AuthApiError(getErrorMessage(error));
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
    throw new AuthApiError(getErrorMessage(error));
  }
}
