import axios from "axios";

import { httpClient } from "./httpClient";

export const NANO_FLAG_REASONS = [
  "spam",
  "copyright",
  "offensive",
  "misinformation",
  "other",
] as const;

export type NanoFlagReason = (typeof NANO_FLAG_REASONS)[number];

export const NANO_FLAG_COMMENT_MAX_LENGTH = 500;

export interface NanoFlag {
  id: string;
  nanoId: string;
  flaggingUserId: string;
  reason: NanoFlagReason;
  comment: string | null;
  status: string;
  createdAt: string;
  reviewedAt: string | null;
  moderatorId: string | null;
}

export interface CreateNanoFlagRequest {
  reason: NanoFlagReason;
  comment?: string;
}

type NanoFlagApiErrorCode =
  | "not-found"
  | "unauthorized"
  | "forbidden"
  | "conflict"
  | "validation"
  | "bad-request"
  | "request-failed"
  | "unknown";

interface ErrorResponseBody {
  detail?: string;
}

interface RawNanoFlag {
  id?: unknown;
  nano_id?: unknown;
  flagging_user_id?: unknown;
  reason?: unknown;
  comment?: unknown;
  status?: unknown;
  created_at?: unknown;
  reviewed_at?: unknown;
  moderator_id?: unknown;
  data?: unknown;
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  return null;
}

function isNanoFlagReason(value: string): value is NanoFlagReason {
  return (NANO_FLAG_REASONS as readonly string[]).includes(value);
}

function unwrapFlagPayload(data: unknown): RawNanoFlag {
  if (!data || typeof data !== "object") {
    return {};
  }

  const raw = data as RawNanoFlag;
  if (asString(raw.id) || asString(raw.nano_id)) {
    return raw;
  }

  if (raw.data && typeof raw.data === "object") {
    return raw.data as RawNanoFlag;
  }

  return raw;
}

function mapNanoFlag(raw: RawNanoFlag): NanoFlag {
  const reasonRaw = asString(raw.reason) ?? "other";

  return {
    id: asString(raw.id) ?? "",
    nanoId: asString(raw.nano_id) ?? "",
    flaggingUserId: asString(raw.flagging_user_id) ?? "",
    reason: isNanoFlagReason(reasonRaw) ? reasonRaw : "other",
    comment: asString(raw.comment),
    status: asString(raw.status) ?? "pending",
    createdAt: asString(raw.created_at) ?? "",
    reviewedAt: asString(raw.reviewed_at),
    moderatorId: asString(raw.moderator_id),
  };
}

function getErrorCode(error: unknown): NanoFlagApiErrorCode {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const status = error.response?.status;
    if (status === 404) {
      return "not-found";
    }
    if (status === 401) {
      return "unauthorized";
    }
    if (status === 403) {
      return "forbidden";
    }
    if (status === 409) {
      return "conflict";
    }
    if (status === 400) {
      return "bad-request";
    }
    if (status === 422) {
      return "validation";
    }
    if (status) {
      return "request-failed";
    }
  }

  return "unknown";
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const detail = error.response?.data?.detail;
    if (detail && detail.trim().length > 0) {
      return detail;
    }
    return "Request failed";
  }

  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return "Request failed";
}

export class NanoFlagApiError extends Error {
  code: NanoFlagApiErrorCode;

  constructor(message: string, code: NanoFlagApiErrorCode) {
    super(message);
    this.name = "NanoFlagApiError";
    this.code = code;
  }
}

export async function getMyNanoFlag(nanoId: string): Promise<NanoFlag | null> {
  try {
    const response = await httpClient.get<RawNanoFlag>(`/api/v1/nanos/${nanoId}/flags/my-flag`);
    return mapNanoFlag(unwrapFlagPayload(response.data));
  } catch (error) {
    if (getErrorCode(error) === "not-found") {
      return null;
    }
    throw new NanoFlagApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function createNanoFlag(
  nanoId: string,
  payload: CreateNanoFlagRequest
): Promise<NanoFlag> {
  try {
    const comment = payload.comment?.trim();
    const response = await httpClient.post<RawNanoFlag>(`/api/v1/nanos/${nanoId}/flags`, {
      reason: payload.reason,
      comment: comment && comment.length > 0 ? comment : null,
    });
    return mapNanoFlag(unwrapFlagPayload(response.data));
  } catch (error) {
    throw new NanoFlagApiError(getErrorMessage(error), getErrorCode(error));
  }
}
