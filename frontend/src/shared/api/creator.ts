/**
 * Creator Dashboard API Client
 *
 * Handles API calls for creator dashboard operations including
 * fetching creator's nanos, deleting nanos, and related actions.
 */

import { httpClient } from "./httpClient";
import type { UpdateNanoMetadataRequest, UpdateNanoMetadataResponse } from "./upload";

export interface CreatorNanoListItem {
  nano_id: string;
  title: string;
  description: string | null;
  status: string;
  thumbnail_url: string | null;
  duration_minutes: number | null;
  competency_level: string;
  created_at: string;
  updated_at: string;
}

export interface PaginationMeta {
  current_page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  has_next_page: boolean;
  has_prev_page: boolean;
}

export interface CreatorNanoListResponse {
  nanos: CreatorNanoListItem[];
  pagination: PaginationMeta;
}

export interface NanoDeleteResponse {
  nano_id: string;
  status: string;
  message: string;
}

export interface CreatorNanoMetadataResponse {
  nano_id: string;
  creator_id: string;
  title: string;
  description: string | null;
  duration_minutes: number | null;
  competency_level: "beginner" | "intermediate" | "advanced";
  language: string;
  format: "video" | "text" | "quiz" | "interactive" | "mixed";
  status: string;
  version: string;
  license: "CC-BY" | "CC-BY-SA" | "CC0" | "proprietary";
  thumbnail_url: string | null;
  uploaded_at: string;
  published_at: string | null;
  updated_at: string;
}

export interface GetCreatorNanosParams {
  page?: number;
  limit?: number;
  status?: string;
}

/**
 * Fetch creator's list of nanos with pagination.
 *
 * @param params - Query parameters for pagination and filtering
 * @returns Promise containing list of creator's nanos with pagination metadata
 * @throws HTTPException on API errors (401, 403, 404, etc.)
 */
export async function getCreatorNanos(
  params: GetCreatorNanosParams = {},
): Promise<CreatorNanoListResponse> {
  const defaultParams = {
    page: params.page ?? 1,
    limit: params.limit ?? 20,
    ...(params.status && { status: params.status }),
  };

  const response = await httpClient.get<CreatorNanoListResponse>("/api/v1/nanos/my-nanos", {
    params: defaultParams,
  });

  return response.data;
}

/**
 * Delete a nano owned by the authenticated creator.
 *
 * @param nanoId - UUID of the nano to delete
 * @returns Promise containing deletion confirmation
 * @throws HTTPException on API errors (400, 401, 403, 404, etc.)
 */
export async function deleteCreatorNano(nanoId: string): Promise<NanoDeleteResponse> {
  const response = await httpClient.delete<NanoDeleteResponse>(`/api/v1/nanos/${nanoId}`);

  return response.data;
}

/**
 * Fetch single nano metadata for creator editing.
 */
export async function getCreatorNanoMetadata(nanoId: string): Promise<CreatorNanoMetadataResponse> {
  const response = await httpClient.get<CreatorNanoMetadataResponse>(`/api/v1/nanos/${nanoId}`);
  return response.data;
}

/**
 * Update nano metadata for creator edit flow.
 */
export async function updateCreatorNanoMetadata(
  nanoId: string,
  payload: UpdateNanoMetadataRequest
): Promise<UpdateNanoMetadataResponse> {
  const response = await httpClient.post<UpdateNanoMetadataResponse>(
    `/api/v1/nanos/${nanoId}/metadata`,
    payload
  );
  return response.data;
}

/**
 * Response shape for a Nano status update (PATCH /api/v1/nanos/:id/status).
 */
export interface NanoStatusUpdateResponse {
  nano_id: string;
  old_status: string;
  new_status: string;
  message: string;
  published_at: string | null;
  archived_at: string | null;
}

/**
 * Submit a draft Nano for moderation review.
 *
 * Transitions: draft → pending_review
 *
 * @param nanoId - UUID of the nano to submit
 * @returns Promise containing the status update confirmation
 * @throws HTTPException on API errors (400 invalid transition, 403 not creator, 404 not found)
 */
export async function submitNanoForReview(nanoId: string): Promise<NanoStatusUpdateResponse> {
  const response = await httpClient.patch<NanoStatusUpdateResponse>(
    `/api/v1/nanos/${nanoId}/status`,
    { status: "pending_review" }
  );
  return response.data;
}

/**
 * Withdraw a pending-review Nano back to draft.
 *
 * Transitions: pending_review → draft
 *
 * @param nanoId - UUID of the nano to withdraw
 * @returns Promise containing the status update confirmation
 * @throws HTTPException on API errors (400 invalid transition, 403 not creator, 404 not found)
 */
export async function withdrawNanoFromReview(nanoId: string): Promise<NanoStatusUpdateResponse> {
  const response = await httpClient.patch<NanoStatusUpdateResponse>(
    `/api/v1/nanos/${nanoId}/status`,
    { status: "draft" }
  );
  return response.data;
}
