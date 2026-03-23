/**
 * Nano Detail API Contract Tests
 *
 * Verifies request/response mapping between frontend detail client and backend
 * `GET /api/v1/nanos/{id}/detail` + `GET /api/v1/nanos/{id}/download-info`.
 */

import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import { getNanoDetail, getNanoDownloadInfo, NanoDetailApiError } from "./nanoDetail";

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

describe("getNanoDetail", () => {
  it("maps backend detail envelope to frontend detail model", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: {
          nano_id: "nano-1",
          title: "React Basics",
          metadata: {
            description: "Intro",
            duration_minutes: 15,
            competency_level: "beginner",
            language: "en",
            format: "video",
            status: "published",
            version: "1.0.0",
            categories: [{ id: "cat-1", name: "Frontend", rank: 0 }],
            license: "CC-BY",
            thumbnail_url: "https://example.com/thumb.png",
            uploaded_at: "2026-03-20T10:00:00Z",
            published_at: "2026-03-20T11:00:00Z",
            updated_at: "2026-03-20T12:00:00Z",
          },
          creator: {
            id: "creator-1",
            username: "alice",
          },
          rating_summary: {
            average_rating: 4.8,
            rating_count: 21,
            download_count: 144,
          },
          download_info: {
            requires_authentication: true,
            can_download: true,
            download_path: "nanos/nano-1/content.mp4",
          },
        },
        meta: {
          visibility: "public",
          request_user_id: null,
        },
        timestamp: "2026-03-20T12:00:00Z",
      })
    );

    const result = await getNanoDetail("nano-1");

    expect(getSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/detail");
    expect(result.nanoId).toBe("nano-1");
    expect(result.title).toBe("React Basics");
    expect(result.metadata.durationMinutes).toBe(15);
    expect(result.creator.username).toBe("alice");
    expect(result.ratingSummary.averageRating).toBe(4.8);
    expect(result.downloadInfo.canDownload).toBe(true);
    expect(result.metadata.categories).toEqual([
      {
        categoryId: "cat-1",
        categoryName: "Frontend",
      },
    ]);
  });

  it("maps HTTP 404 to typed not-found error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 404,
        data: {
          detail: "Nano with ID nano-unknown not found",
        },
      },
    });

    await expect(getNanoDetail("nano-unknown")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "not-found",
    });
  });

  it("maps HTTP 401 to typed unauthorized error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          detail: "Authentication required",
        },
      },
    });

    await expect(getNanoDetail("nano-protected")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "unauthorized",
      message: "Authentication required",
    });
  });

  it("maps HTTP 403 to typed forbidden error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          detail: "Access denied",
        },
      },
    });

    await expect(getNanoDetail("nano-private")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "forbidden",
      message: "Access denied",
    });
  });

  it("maps HTTP 500 to typed request-failed error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 500,
        data: {
          detail: "Internal server error",
        },
      },
    });

    await expect(getNanoDetail("nano-1")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "request-failed",
      message: "Internal server error",
    });
  });
});

describe("getNanoDownloadInfo", () => {
  it("maps download info endpoint response", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(
      createAxiosResponse({
        success: true,
        data: {
          nano_id: "nano-1",
          can_download: true,
          download_url: "https://storage.example.com/nanos/nano-1/content.mp4?signature=test",
        },
        meta: {
          visibility: "public",
          request_user_id: "user-1",
        },
        timestamp: "2026-03-20T12:00:00Z",
      })
    );

    const result = await getNanoDownloadInfo("nano-1");

    expect(getSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/download-info");
    expect(result).toEqual({
      nanoId: "nano-1",
      canDownload: true,
      downloadUrl: "https://storage.example.com/nanos/nano-1/content.mp4?signature=test",
    });
  });

  it("maps HTTP 401 to typed unauthorized error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          detail: "Token missing",
        },
      },
    });

    await expect(getNanoDownloadInfo("nano-1")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "unauthorized",
      message: "Token missing",
    });
  });

  it("maps HTTP 403 to typed forbidden error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          detail: "Not allowed",
        },
      },
    });

    await expect(getNanoDownloadInfo("nano-1")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "forbidden",
      message: "Not allowed",
    });
  });

  it("maps HTTP 503 to typed request-failed error", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 503,
        data: {
          detail: "Download URL is temporarily unavailable",
        },
      },
    });

    await expect(getNanoDownloadInfo("nano-1")).rejects.toMatchObject<NanoDetailApiError>({
      name: "NanoDetailApiError",
      code: "request-failed",
      message: "Download URL is temporarily unavailable",
    });
  });
});
