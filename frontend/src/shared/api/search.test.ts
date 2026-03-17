/**
 * Search API Contract Tests
 *
 * Verifies request/response mapping between the frontend discovery client and
 * the backend `GET /api/v1/search` contract.
 */

import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import { searchNanos } from "./search";

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

describe("searchNanos", () => {
  /**
   * Verifies the client maps the backend `success/data/meta/timestamp` payload
   * into the frontend search response shape used by `SearchPage`.
   */
  it("maps backend contract response including pagination metadata", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: [
          {
            id: "nano-1",
            title: "React Basics",
            creator: "Alice",
            average_rating: 4.7,
            duration_minutes: 15,
          },
        ],
        meta: {
          pagination: {
            current_page: 2,
            page_size: 20,
            total_results: 41,
            total_pages: 3,
            has_next_page: true,
            has_prev_page: true,
          },
        },
        timestamp: "2026-03-17T12:00:00Z",
      })
    );

    const result = await searchNanos({
      query: "react",
      filters: {
        category: "Programming",
        level: "2",
        duration: "15-30",
        language: "en",
      },
      limit: 20,
      page: 2,
    });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/search", {
      params: {
        q: "react",
        category: "Programming",
        level: "2",
        duration: "15-30",
        language: "en",
        page: 2,
        limit: 20,
      },
    });
    expect(result).toEqual({
      items: [
        {
          id: "nano-1",
          title: "React Basics",
          creator: "Alice",
          averageRating: 4.7,
          durationMinutes: 15,
        },
      ],
      total: 41,
      page: 2,
      pageSize: 20,
      totalPages: 3,
      hasNextPage: true,
      hasPrevPage: true,
    });
  });

  /**
   * Verifies backward-compatible request normalization for older caller state:
   * legacy textual levels and offset-based pagination are translated to the
   * backend page contract before the request is sent.
   */
  it("normalizes legacy level values and offset pagination to backend params", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: [],
        meta: {
          pagination: {
            current_page: 3,
            page_size: 20,
            total_results: 50,
            total_pages: 3,
            has_next_page: false,
            has_prev_page: true,
          },
        },
        timestamp: "2026-03-17T12:00:00Z",
      })
    );

    await searchNanos({
      query: "excel",
      filters: {
        level: "advanced",
      },
      limit: 20,
      offset: 40,
    });

    expect(getSpy).toHaveBeenCalledWith("/api/v1/search", {
      params: {
        q: "excel",
        category: undefined,
        level: "3",
        duration: undefined,
        language: undefined,
        page: 3,
        limit: 20,
      },
    });
  });
});
