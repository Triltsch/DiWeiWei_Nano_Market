/**
 * Moderator API Client
 *
 * Handles API calls for the moderation workflow: listing nanos pending review,
 * approving (publishing) them, and rejecting (returning to draft) them.
 *
 * All functions require the authenticated user to have the 'moderator' or
 * 'admin' role. The backend enforces this; the frontend restricts UI access.
 */

import { httpClient } from "./httpClient";
import type { NanoStatusUpdateResponse } from "./creator";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * A single Nano item in the moderation queue.
 */
export interface ModeratorQueueItem {
  nano_id: string;
  creator_id: string;
  creator_username: string | null;
  title: string;
  description: string | null;
  status: string;
  duration_minutes: number | null;
  competency_level: string;
  language: string;
  /** When the creator submitted the Nano for review (== updated_at at submission time). */
  submitted_at: string;
  created_at: string;
}

/**
 * Pagination metadata returned by list endpoints.
 */
export interface ModerationPaginationMeta {
  current_page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  has_next_page: boolean;
  has_prev_page: boolean;
}

/**
 * Response body for GET /api/v1/nanos/pending-moderation.
 */
export interface ModeratorQueueListResponse {
  nanos: ModeratorQueueItem[];
  pagination: ModerationPaginationMeta;
}

/**
 * Query parameters for fetching the moderation queue.
 */
export interface GetModerationQueueParams {
  page?: number;
  limit?: number;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * Fetch the list of Nanos currently pending moderation review.
 *
 * Requires moderator or admin role (enforced by backend; returns 403 otherwise).
 *
 * @param params - Optional pagination parameters
 * @returns Promise containing paginated moderation queue
 * @throws HTTPException on API errors (401, 403, etc.)
 */
export async function getModerationQueue(
  params: GetModerationQueueParams = {}
): Promise<ModeratorQueueListResponse> {
  const queryParams = {
    page: params.page ?? 1,
    limit: params.limit ?? 20,
  };

  const response = await httpClient.get<ModeratorQueueListResponse>(
    "/api/v1/nanos/pending-moderation",
    { params: queryParams }
  );

  return response.data;
}

/**
 * Approve a pending-review Nano (transition: pending_review → published).
 *
 * Requires moderator or admin role.
 *
 * @param nanoId - UUID of the nano to approve
 * @returns Promise containing the status update confirmation
 * @throws HTTPException on API errors (400 invalid transition, 403 not moderator, 404 not found)
 */
export async function approveNano(nanoId: string): Promise<NanoStatusUpdateResponse> {
  const response = await httpClient.patch<NanoStatusUpdateResponse>(
    `/api/v1/nanos/${nanoId}/status`,
    { status: "published" }
  );
  return response.data;
}

/**
 * Reject a pending-review Nano and return it to draft
 * (transition: pending_review → draft).
 *
 * The creator will need to revise their Nano and resubmit.
 * Requires moderator or admin role.
 *
 * @param nanoId - UUID of the nano to reject
 * @param reason - Optional reason shown in the audit log
 * @returns Promise containing the status update confirmation
 * @throws HTTPException on API errors (400 invalid transition, 403 not moderator, 404 not found)
 */
export async function rejectNano(
  nanoId: string,
  reason?: string
): Promise<NanoStatusUpdateResponse> {
  const response = await httpClient.patch<NanoStatusUpdateResponse>(
    `/api/v1/nanos/${nanoId}/status`,
    { status: "draft", reason: reason ?? undefined }
  );
  return response.data;
}
