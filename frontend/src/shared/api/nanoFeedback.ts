import axios from "axios";

import { httpClient } from "./httpClient";
import type { PaginationMeta } from "./creator";

export interface NanoRatingDistributionItem {
  score: number;
  count: number;
}

export interface NanoRatingAggregation {
  averageRating: number;
  medianRating: number;
  ratingCount: number;
  distribution: NanoRatingDistributionItem[];
}

export interface NanoUserRating {
  ratingId: string;
  score: number;
  moderationStatus: string;
  updatedAt: string;
}

export interface NanoRatingsResponse {
  nanoId: string;
  aggregation: NanoRatingAggregation;
  currentUserRating: NanoUserRating | null;
}

export interface NanoComment {
  commentId: string;
  nanoId: string;
  userId: string;
  username: string | null;
  content: string;
  moderationStatus: string;
  createdAt: string;
  updatedAt: string;
  isEdited: boolean;
}

export interface NanoCommentsResponse {
  comments: NanoComment[];
  pagination: PaginationMeta;
}

export interface NanoCommentMutationResponse {
  comment: NanoComment;
}

export interface NanoRatingMutationResponse {
  nanoId: string;
  userRating: NanoUserRating;
  aggregation: NanoRatingAggregation;
}

export interface NanoCommentsRequest {
  page?: number;
  limit?: number;
}

type NanoFeedbackApiErrorCode =
  | "not-found"
  | "unauthorized"
  | "forbidden"
  | "conflict"
  | "validation"
  | "request-failed"
  | "unknown";

interface ErrorResponseBody {
  detail?: string;
}

interface RawNanoRatingDistributionItem {
  score?: unknown;
  count?: unknown;
}

interface RawNanoRatingAggregation {
  average_rating?: unknown;
  median_rating?: unknown;
  rating_count?: unknown;
  distribution?: unknown;
}

interface RawNanoUserRating {
  rating_id?: unknown;
  score?: unknown;
  moderation_status?: unknown;
  updated_at?: unknown;
}

interface RawNanoRatingsData {
  nano_id?: unknown;
  aggregation?: unknown;
  current_user_rating?: unknown;
}

interface RawNanoRatingsResponse {
  data?: unknown;
}

interface RawNanoComment {
  comment_id?: unknown;
  nano_id?: unknown;
  user_id?: unknown;
  username?: unknown;
  content?: unknown;
  moderation_status?: unknown;
  created_at?: unknown;
  updated_at?: unknown;
  is_edited?: unknown;
}

interface RawPaginationMeta {
  current_page?: unknown;
  page_size?: unknown;
  total_results?: unknown;
  total_pages?: unknown;
  has_next_page?: unknown;
  has_prev_page?: unknown;
}

interface RawNanoCommentsData {
  comments?: unknown;
  pagination?: unknown;
}

interface RawNanoCommentsResponse {
  data?: unknown;
}

interface RawNanoCommentMutationData {
  comment?: unknown;
}

interface RawNanoCommentMutationResponse {
  data?: unknown;
}

interface RawNanoRatingMutationData {
  nano_id?: unknown;
  user_rating?: unknown;
  aggregation?: unknown;
}

interface RawNanoRatingMutationResponse {
  data?: unknown;
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}

function mapPagination(raw: RawPaginationMeta | undefined, fallbackCount: number): PaginationMeta {
  return {
    current_page: asNumber(raw?.current_page) ?? 1,
    page_size: asNumber(raw?.page_size) ?? fallbackCount,
    total_results: asNumber(raw?.total_results) ?? fallbackCount,
    total_pages: asNumber(raw?.total_pages) ?? 1,
    has_next_page: asBoolean(raw?.has_next_page),
    has_prev_page: asBoolean(raw?.has_prev_page),
  };
}

function mapNanoRatingDistributionItem(
  raw: RawNanoRatingDistributionItem,
  index: number,
): NanoRatingDistributionItem {
  return {
    score: asNumber(raw.score) ?? index + 1,
    count: asNumber(raw.count) ?? 0,
  };
}

function mapNanoRatingAggregation(raw: RawNanoRatingAggregation | undefined): NanoRatingAggregation {
  const distribution = Array.isArray(raw?.distribution)
    ? (raw?.distribution as RawNanoRatingDistributionItem[])
    : [];

  return {
    averageRating: asNumber(raw?.average_rating) ?? 0,
    medianRating: asNumber(raw?.median_rating) ?? 0,
    ratingCount: asNumber(raw?.rating_count) ?? 0,
    distribution: distribution.map(mapNanoRatingDistributionItem),
  };
}

function mapNanoUserRating(raw: RawNanoUserRating | undefined): NanoUserRating | null {
  if (!raw) {
    return null;
  }

  const ratingId = asString(raw.rating_id);
  if (!ratingId) {
    return null;
  }

  return {
    ratingId,
    score: asNumber(raw.score) ?? 0,
    moderationStatus: asString(raw.moderation_status) ?? "pending",
    updatedAt: asString(raw.updated_at) ?? "",
  };
}

function mapNanoComment(raw: RawNanoComment, index: number): NanoComment {
  return {
    commentId: asString(raw.comment_id) ?? `comment-${index}`,
    nanoId: asString(raw.nano_id) ?? "",
    userId: asString(raw.user_id) ?? "",
    username: asString(raw.username),
    content: asString(raw.content) ?? "",
    moderationStatus: asString(raw.moderation_status) ?? "approved",
    createdAt: asString(raw.created_at) ?? "",
    updatedAt: asString(raw.updated_at) ?? "",
    isEdited: asBoolean(raw.is_edited),
  };
}

function getErrorCode(error: unknown): NanoFeedbackApiErrorCode {
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

export class NanoFeedbackApiError extends Error {
  code: NanoFeedbackApiErrorCode;

  constructor(message: string, code: NanoFeedbackApiErrorCode) {
    super(message);
    this.name = "NanoFeedbackApiError";
    this.code = code;
  }
}

export async function getNanoRatings(nanoId: string): Promise<NanoRatingsResponse> {
  try {
    const response = await httpClient.get<RawNanoRatingsResponse>(`/api/v1/nanos/${nanoId}/ratings`);
    const rawData = (response.data.data as RawNanoRatingsData | undefined) ?? {};

    return {
      nanoId: asString(rawData.nano_id) ?? nanoId,
      aggregation: mapNanoRatingAggregation(rawData.aggregation as RawNanoRatingAggregation | undefined),
      currentUserRating: mapNanoUserRating(rawData.current_user_rating as RawNanoUserRating | undefined),
    };
  } catch (error) {
    throw new NanoFeedbackApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function createNanoRating(
  nanoId: string,
  score: number,
): Promise<NanoRatingMutationResponse> {
  try {
    const response = await httpClient.post<RawNanoRatingMutationResponse>(
      `/api/v1/nanos/${nanoId}/ratings`,
      { score }
    );
    const rawData = (response.data.data as RawNanoRatingMutationData | undefined) ?? {};

    return {
      nanoId: asString(rawData.nano_id) ?? nanoId,
      userRating:
        mapNanoUserRating(rawData.user_rating as RawNanoUserRating | undefined) ?? {
          ratingId: "",
          score,
          moderationStatus: "pending",
          updatedAt: "",
        },
      aggregation: mapNanoRatingAggregation(rawData.aggregation as RawNanoRatingAggregation | undefined),
    };
  } catch (error) {
    throw new NanoFeedbackApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function updateMyNanoRating(
  nanoId: string,
  score: number,
): Promise<NanoRatingMutationResponse> {
  try {
    const response = await httpClient.patch<RawNanoRatingMutationResponse>(
      `/api/v1/nanos/${nanoId}/ratings/me`,
      { score }
    );
    const rawData = (response.data.data as RawNanoRatingMutationData | undefined) ?? {};

    return {
      nanoId: asString(rawData.nano_id) ?? nanoId,
      userRating:
        mapNanoUserRating(rawData.user_rating as RawNanoUserRating | undefined) ?? {
          ratingId: "",
          score,
          moderationStatus: "pending",
          updatedAt: "",
        },
      aggregation: mapNanoRatingAggregation(rawData.aggregation as RawNanoRatingAggregation | undefined),
    };
  } catch (error) {
    throw new NanoFeedbackApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function getNanoComments(
  nanoId: string,
  request: NanoCommentsRequest = {},
): Promise<NanoCommentsResponse> {
  try {
    const response = await httpClient.get<RawNanoCommentsResponse>(`/api/v1/nanos/${nanoId}/comments`, {
      params: {
        page: request.page ?? 1,
        limit: request.limit ?? 20,
      },
    });
    const rawData = (response.data.data as RawNanoCommentsData | undefined) ?? {};
    const comments = Array.isArray(rawData.comments)
      ? (rawData.comments as RawNanoComment[]).map(mapNanoComment)
      : [];

    return {
      comments,
      pagination: mapPagination(rawData.pagination as RawPaginationMeta | undefined, comments.length),
    };
  } catch (error) {
    throw new NanoFeedbackApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function createNanoComment(
  nanoId: string,
  content: string,
): Promise<NanoCommentMutationResponse> {
  try {
    const response = await httpClient.post<RawNanoCommentMutationResponse>(
      `/api/v1/nanos/${nanoId}/comments`,
      { content }
    );
    const rawData = (response.data.data as RawNanoCommentMutationData | undefined) ?? {};
    const comment = rawData.comment as RawNanoComment | undefined;

    return {
      comment: mapNanoComment(comment ?? {}, 0),
    };
  } catch (error) {
    throw new NanoFeedbackApiError(getErrorMessage(error), getErrorCode(error));
  }
}