/**
 * Nano flag API contract tests for POST /flags and GET /flags/my-flag.
 */

import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import { createNanoFlag, getMyNanoFlag, NanoFlagApiError } from "./nanoFlags";

afterEach(() => {
  vi.restoreAllMocks();
});

function createAxiosResponse<T>(data: T, status = 200): AxiosResponse<T> {
  return {
    data,
    status,
    statusText: status === 201 ? "Created" : "OK",
    headers: {},
    config: {
      headers: new AxiosHeaders(),
    } as InternalAxiosRequestConfig,
  };
}

const flagPayload = {
  id: "flag-1",
  nano_id: "nano-1",
  flagging_user_id: "user-1",
  reason: "spam",
  comment: "Looks like ads.",
  status: "pending",
  created_at: "2026-03-20T12:00:00Z",
  reviewed_at: null,
  moderator_id: null,
};

describe("getMyNanoFlag", () => {
  it("maps a flat backend flag payload to the frontend model", async () => {
    const getSpy = vi.spyOn(httpClient, "get").mockResolvedValue(createAxiosResponse(flagPayload));

    const result = await getMyNanoFlag("nano-1");

    expect(getSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/flags/my-flag");
    expect(result?.id).toBe("flag-1");
    expect(result?.nanoId).toBe("nano-1");
    expect(result?.reason).toBe("spam");
    expect(result?.status).toBe("pending");
    expect(result?.comment).toBe("Looks like ads.");
  });

  it("returns null when the caller has not flagged the nano (404)", async () => {
    vi.spyOn(httpClient, "get").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 404,
        data: { detail: "Not found" },
      },
    });

    await expect(getMyNanoFlag("nano-1")).resolves.toBeNull();
  });
});

describe("createNanoFlag", () => {
  it("posts reason and optional comment and maps the created flag", async () => {
    const postSpy = vi
      .spyOn(httpClient, "post")
      .mockResolvedValue(createAxiosResponse(flagPayload, 201));

    const result = await createNanoFlag("nano-1", { reason: "spam", comment: "  Looks like ads.  " });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/flags", {
      reason: "spam",
      comment: "Looks like ads.",
    });
    expect(result.id).toBe("flag-1");
    expect(result.reason).toBe("spam");
  });

  it("maps 409 duplicate flags to a typed conflict error", async () => {
    vi.spyOn(httpClient, "post").mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { detail: "Already flagged" },
      },
    });

    await expect(createNanoFlag("nano-1", { reason: "other" })).rejects.toMatchObject({
      name: "NanoFlagApiError",
      code: "conflict",
    } satisfies Partial<NanoFlagApiError>);
  });
});
