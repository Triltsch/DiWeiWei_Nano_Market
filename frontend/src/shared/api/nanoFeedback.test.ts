/**
 * Nano Feedback API Contract Tests
 *
 * Verifies request/response mapping between frontend feedback client and the
 * backend ratings/comments endpoints for nano detail feedback integration.
 */

import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import {
  createNanoComment,
  createNanoRating,
  getNanoComments,
  getNanoRatings,
  NanoFeedbackApiError,
  updateMyNanoRating,
} from "./nanoFeedback";

afterEach(() => {
  vi.restoreAllMocks();
});

function createAxiosResponse<T>(data: T): AxiosResponse<T> {
  return {
    data,
    status: 200,
    statusText: "OK",
    headers: {},
    config: {
      headers: new AxiosHeaders(),
    } as InternalAxiosRequestConfig,
  };
}

describe("getNanoRatings", () => {
  /**
   * Verifies aggregation and caller rating fields are mapped from snake_case
   * backend payloads into the frontend feedback model.
   */
  it("maps backend rating aggregation envelope to frontend feedback model", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: {
          nano_id: "nano-1",
          aggregation: {
            average_rating: 4.6,
            median_rating: 5,
            rating_count: 10,
            distribution: [
              { score: 5, count: 7 },
              { score: 4, count: 3 },
            ],
          },
          current_user_rating: {
            rating_id: "rating-1",
            score: 4,
            moderation_status: "approved",
            updated_at: "2026-03-20T12:00:00Z",
          },
        },
      })
    );

    const result = await getNanoRatings("nano-1");

    expect(getSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/ratings");
    expect(result.nanoId).toBe("nano-1");
    expect(result.aggregation.averageRating).toBe(4.6);
    expect(result.aggregation.medianRating).toBe(5);
    expect(result.aggregation.ratingCount).toBe(10);
    expect(result.currentUserRating?.ratingId).toBe("rating-1");
    expect(result.currentUserRating?.moderationStatus).toBe("approved");
  });

  /**
   * Verifies client errors normalize backend 404 responses to a typed feedback
   * API error that page code can branch on safely.
   */
  it("maps HTTP 404 to typed not-found error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 404,
        data: {
          detail: "Nano not found",
        },
      },
    });

    await expect(getNanoRatings("nano-missing")).rejects.toMatchObject<NanoFeedbackApiError>({
      name: "NanoFeedbackApiError",
      code: "not-found",
      message: "Nano not found",
    });
  });
});

describe("getNanoComments", () => {
  /**
   * Verifies comment lists and pagination metadata are mapped into the shared
   * frontend model used by the detail page.
   */
  it("maps backend comment list envelope to frontend comments model", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: {
          comments: [
            {
              comment_id: "comment-1",
              nano_id: "nano-1",
              user_id: "user-1",
              username: "alice",
              content: "Helpful and concise.",
              moderation_status: "approved",
              created_at: "2026-03-20T10:00:00Z",
              updated_at: "2026-03-20T10:05:00Z",
              is_edited: true,
            },
          ],
          pagination: {
            current_page: 2,
            page_size: 5,
            total_results: 6,
            total_pages: 2,
            has_next_page: false,
            has_prev_page: true,
          },
        },
      })
    );

    const result = await getNanoComments("nano-1", { page: 2, limit: 5 });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/comments", {
      params: {
        page: 2,
        limit: 5,
      },
    });
    expect(result.comments[0]).toMatchObject({
      commentId: "comment-1",
      username: "alice",
      content: "Helpful and concise.",
      isEdited: true,
    });
    expect(result.pagination.total_pages).toBe(2);
    expect(result.pagination.has_prev_page).toBe(true);
  });
});

describe("rating and comment mutations", () => {
  /**
   * Verifies create/update mutation responses are mapped consistently so the
   * page can update local UI state without refetching.
   */
  it("maps rating create and update mutation envelopes", async () => {
    vi.spyOn(httpClient, "post").mockResolvedValueOnce(
      createAxiosResponse({
        success: true,
        data: {
          nano_id: "nano-1",
          user_rating: {
            rating_id: "rating-1",
            score: 5,
            moderation_status: "pending",
            updated_at: "2026-03-21T10:00:00Z",
          },
          aggregation: {
            average_rating: 4.7,
            median_rating: 5,
            rating_count: 12,
            distribution: [],
          },
        },
      })
    );
    vi.spyOn(httpClient, "patch").mockResolvedValueOnce(
      createAxiosResponse({
        success: true,
        data: {
          nano_id: "nano-1",
          user_rating: {
            rating_id: "rating-1",
            score: 4,
            moderation_status: "pending",
            updated_at: "2026-03-21T11:00:00Z",
          },
          aggregation: {
            average_rating: 4.5,
            median_rating: 4,
            rating_count: 12,
            distribution: [],
          },
        },
      })
    );

    const createResult = await createNanoRating("nano-1", 5);
    const updateResult = await updateMyNanoRating("nano-1", 4);

    expect(createResult.userRating.score).toBe(5);
    expect(createResult.userRating.moderationStatus).toBe("pending");
    expect(updateResult.userRating.score).toBe(4);
    expect(updateResult.aggregation.averageRating).toBe(4.5);
  });

  /**
   * Verifies moderation-sensitive create-comment conflicts map to a typed 409
   * error so the UI can distinguish duplicate-comment cases from generic failures.
   */
  it("maps HTTP 409 comment creation to typed conflict error", async () => {
    vi.spyOn(httpClient, "post").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: {
          detail: "A comment for this Nano by the current user already exists",
        },
      },
    });

    await expect(createNanoComment("nano-1", "Already posted")).rejects.toMatchObject<NanoFeedbackApiError>({
      name: "NanoFeedbackApiError",
      code: "conflict",
      message: "A comment for this Nano by the current user already exists",
    });
  });

  /**
   * Verifies auth failures map to typed unauthorized errors so UI routes can
   * redirect users to login consistently.
   */
  it("maps HTTP 401 rating creation to typed unauthorized error", async () => {
    vi.spyOn(httpClient, "post").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          detail: "Not authenticated",
        },
      },
    });

    await expect(createNanoRating("nano-1", 5)).rejects.toMatchObject<NanoFeedbackApiError>({
      name: "NanoFeedbackApiError",
      code: "unauthorized",
      message: "Not authenticated",
    });
  });

  /**
   * Verifies role and permission failures map to typed forbidden errors that
   * page-level handlers can surface as access messages.
   */
  it("maps HTTP 403 comments fetch to typed forbidden error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          detail: "Insufficient permissions",
        },
      },
    });

    await expect(getNanoComments("nano-1", { page: 1, limit: 5 })).rejects.toMatchObject<NanoFeedbackApiError>({
      name: "NanoFeedbackApiError",
      code: "forbidden",
      message: "Insufficient permissions",
    });
  });

  /**
   * Verifies input/schema failures map to typed validation errors for precise
   * form feedback in the detail page comment composer.
   */
  it("maps HTTP 422 comment creation to typed validation error", async () => {
    vi.spyOn(httpClient, "post").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 422,
        data: {
          detail: "Comment content must not be blank",
        },
      },
    });

    await expect(createNanoComment("nano-1", "   ")).rejects.toMatchObject<NanoFeedbackApiError>({
      name: "NanoFeedbackApiError",
      code: "validation",
      message: "Comment content must not be blank",
    });
  });
});