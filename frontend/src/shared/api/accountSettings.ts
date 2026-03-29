import axios from "axios";

import type { AuthRole } from "./types";
import { httpClient } from "./httpClient";

export type AccountStatus = "active" | "inactive" | "suspended" | "deleted";

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  firstName: string | null;
  lastName: string | null;
  bio: string | null;
  preferredLanguage: string;
  status: AccountStatus;
  role: AuthRole;
  emailVerified: boolean;
  verifiedAt: string | null;
  createdAt: string;
  updatedAt: string;
  lastLogin: string | null;
  profileAvatar: string | null;
  company: string | null;
  jobTitle: string | null;
  phone: string | null;
  acceptedTerms: string | null;
  acceptedPrivacy: string | null;
  deletionRequestedAt: string | null;
  deletionScheduledAt: string | null;
}

export interface UserProfileUpdateRequest {
  firstName?: string | null;
  lastName?: string | null;
  bio?: string | null;
  company?: string | null;
  jobTitle?: string | null;
  phone?: string | null;
  preferredLanguage?: string;
}

export interface PasswordChangeRequest {
  currentPassword: string;
  newPassword: string;
}

export interface UserDataExport {
  exportDate: string;
  userId: string;
  email: string;
  username: string;
  firstName: string | null;
  lastName: string | null;
  bio: string | null;
  company: string | null;
  jobTitle: string | null;
  phone: string | null;
  preferredLanguage: string;
  createdAt: string;
  updatedAt: string;
  lastLogin: string | null;
  emailVerified: boolean;
  verifiedAt: string | null;
  status: string;
  role: string;
  acceptedTerms: string | null;
  acceptedPrivacy: string | null;
}

export interface AccountDeletionResponse {
  message: string;
  deletionScheduledAt: string;
  gracePeriodDays: number;
}

export interface AccountDeletionRequest {
  confirm: boolean;
  reason?: string;
}

export type AccountSettingsApiErrorCode =
  | "unauthorized"
  | "forbidden"
  | "validation"
  | "current-password-incorrect"
  | "deletion-already-requested"
  | "service-unavailable"
  | "request-failed"
  | "unknown";

interface ErrorResponseBody {
  detail?: string;
}

interface RawUserProfile {
  id?: unknown;
  email?: unknown;
  username?: unknown;
  first_name?: unknown;
  last_name?: unknown;
  bio?: unknown;
  preferred_language?: unknown;
  status?: unknown;
  role?: unknown;
  email_verified?: unknown;
  verified_at?: unknown;
  created_at?: unknown;
  updated_at?: unknown;
  last_login?: unknown;
  profile_avatar?: unknown;
  company?: unknown;
  job_title?: unknown;
  phone?: unknown;
  accepted_terms?: unknown;
  accepted_privacy?: unknown;
  deletion_requested_at?: unknown;
  deletion_scheduled_at?: unknown;
}

interface RawMessageResponse {
  message?: unknown;
}

interface RawUserDataExport {
  export_date?: unknown;
  user_id?: unknown;
  email?: unknown;
  username?: unknown;
  first_name?: unknown;
  last_name?: unknown;
  bio?: unknown;
  company?: unknown;
  job_title?: unknown;
  phone?: unknown;
  preferred_language?: unknown;
  created_at?: unknown;
  updated_at?: unknown;
  last_login?: unknown;
  email_verified?: unknown;
  verified_at?: unknown;
  status?: unknown;
  role?: unknown;
  accepted_terms?: unknown;
  accepted_privacy?: unknown;
}

interface RawAccountDeletionResponse {
  message?: unknown;
  deletion_scheduled_at?: unknown;
  grace_period_days?: unknown;
}

function asString(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }

  return null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  return null;
}

function asNullableString(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  return asString(value);
}

function mapRole(value: unknown): AuthRole {
  if (value === "creator" || value === "moderator" || value === "admin") {
    return value;
  }

  return "consumer";
}

function mapStatus(value: unknown): AccountStatus {
  if (value === "inactive" || value === "suspended" || value === "deleted") {
    return value;
  }

  if (value === "active") {
    return value;
  }

  return "inactive";
}

function mapUserProfile(raw: RawUserProfile): UserProfile {

  return {
    id: asString(raw.id) ?? "",
    email: asString(raw.email) ?? "",
    username: asString(raw.username) ?? "",
    firstName: asNullableString(raw.first_name),
    lastName: asNullableString(raw.last_name),
    bio: asNullableString(raw.bio),
    preferredLanguage: asString(raw.preferred_language) ?? "de",
    status: mapStatus(raw.status),
    role: mapRole(raw.role),
    emailVerified: asBoolean(raw.email_verified),
    verifiedAt: asNullableString(raw.verified_at),
    createdAt: asString(raw.created_at) ?? "",
    updatedAt: asString(raw.updated_at) ?? "",
    lastLogin: asNullableString(raw.last_login),
    profileAvatar: asNullableString(raw.profile_avatar),
    company: asNullableString(raw.company),
    jobTitle: asNullableString(raw.job_title),
    phone: asNullableString(raw.phone),
    acceptedTerms: asNullableString(raw.accepted_terms),
    acceptedPrivacy: asNullableString(raw.accepted_privacy),
    deletionRequestedAt: asNullableString(raw.deletion_requested_at),
    deletionScheduledAt: asNullableString(raw.deletion_scheduled_at),
  };
}

function mapUserDataExport(raw: RawUserDataExport): UserDataExport {
  return {
    exportDate: asString(raw.export_date) ?? "",
    userId: asString(raw.user_id) ?? "",
    email: asString(raw.email) ?? "",
    username: asString(raw.username) ?? "",
    firstName: asNullableString(raw.first_name),
    lastName: asNullableString(raw.last_name),
    bio: asNullableString(raw.bio),
    company: asNullableString(raw.company),
    jobTitle: asNullableString(raw.job_title),
    phone: asNullableString(raw.phone),
    preferredLanguage: asString(raw.preferred_language) ?? "de",
    createdAt: asString(raw.created_at) ?? "",
    updatedAt: asString(raw.updated_at) ?? "",
    lastLogin: asNullableString(raw.last_login),
    emailVerified: asBoolean(raw.email_verified),
    verifiedAt: asNullableString(raw.verified_at),
    status: asString(raw.status) ?? "active",
    role: asString(raw.role) ?? "consumer",
    acceptedTerms: asNullableString(raw.accepted_terms),
    acceptedPrivacy: asNullableString(raw.accepted_privacy),
  };
}

function mapAccountDeletionResponse(raw: RawAccountDeletionResponse): AccountDeletionResponse {
  return {
    message: asString(raw.message) ?? "",
    deletionScheduledAt: asString(raw.deletion_scheduled_at) ?? "",
    gracePeriodDays: asNumber(raw.grace_period_days) ?? 30,
  };
}

function getErrorCode(error: unknown): AccountSettingsApiErrorCode {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail ?? "";

    if (status === 401) {
      // Coupled to backend message in app/modules/auth/router.py (change password route).
      // Prefer a machine-readable API error code when backend support is available.
      if (detail === "Current password is incorrect") {
        return "current-password-incorrect";
      }

      return "unauthorized";
    }

    if (status === 403) {
      return "forbidden";
    }

    if (status === 409) {
      return "deletion-already-requested";
    }

    if (status === 400 || status === 422) {
      return "validation";
    }

    if (status === 503) {
      return "service-unavailable";
    }

    if (status) {
      return "request-failed";
    }
  }

  return "unknown";
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    if (!error.response) {
      return "Request failed. Please try again.";
    }

    return error.response.data?.detail ?? "Request failed. Please try again.";
  }


  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed. Please try again.";
}

export class AccountSettingsApiError extends Error {
  code: AccountSettingsApiErrorCode;

  constructor(message: string, code: AccountSettingsApiErrorCode = "unknown") {
    super(message);
    this.name = "AccountSettingsApiError";
    this.code = code;
  }
}

export async function getMyProfile(): Promise<UserProfile> {
  try {
    const response = await httpClient.get<RawUserProfile>("/api/v1/auth/me");
    return mapUserProfile(response.data);
  } catch (error) {
    throw new AccountSettingsApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function updateMyProfile(
  payload: UserProfileUpdateRequest,
): Promise<UserProfile> {
  try {
    const response = await httpClient.patch<RawUserProfile>("/api/v1/auth/me", {
      first_name: payload.firstName,
      last_name: payload.lastName,
      bio: payload.bio,
      company: payload.company,
      job_title: payload.jobTitle,
      phone: payload.phone,
      preferred_language: payload.preferredLanguage,
    });

    return mapUserProfile(response.data);
  } catch (error) {
    throw new AccountSettingsApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function changeMyPassword(payload: PasswordChangeRequest): Promise<string> {
  try {
    const response = await httpClient.post<RawMessageResponse>("/api/v1/auth/me/change-password", {
      current_password: payload.currentPassword,
      new_password: payload.newPassword,
    });

    return asString(response.data.message) ?? "Password changed successfully";
  } catch (error) {
    throw new AccountSettingsApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function exportMyData(): Promise<UserDataExport> {
  try {
    const response = await httpClient.get<RawUserDataExport>("/api/v1/auth/me/export");
    return mapUserDataExport(response.data);
  } catch (error) {
    throw new AccountSettingsApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function requestMyAccountDeletion(
  payload: AccountDeletionRequest,
): Promise<AccountDeletionResponse> {
  try {
    const response = await httpClient.post<RawAccountDeletionResponse>("/api/v1/auth/me/delete", {
      confirm: payload.confirm,
      reason: payload.reason,
    });

    return mapAccountDeletionResponse(response.data);
  } catch (error) {
    throw new AccountSettingsApiError(getErrorMessage(error), getErrorCode(error));
  }
}
