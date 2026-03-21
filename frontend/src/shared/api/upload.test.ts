/**
 * Upload Wizard API Contract Tests
 *
 * Verifies request mapping for upload, metadata update, and publish actions.
 */

import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import { publishNano, updateNanoMetadata, uploadNanoZip } from "./upload";

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

describe("upload api", () => {
  it("posts zip file to upload endpoint", async () => {
    const postSpy = vi.spyOn(httpClient, "post").mockResolvedValue(
      createAxiosResponse({
        nano_id: "nano-1",
        status: "draft",
        title: "Untitled",
        uploaded_at: "2026-03-20T12:00:00Z",
        message: "Upload successful",
      })
    );

    const file = new File(["zip-content"], "lesson.zip", { type: "application/zip" });
    const result = await uploadNanoZip(file);

    const args = postSpy.mock.calls[0];
    expect(args[0]).toBe("/api/v1/upload/nano");
    expect(args[1]).toBeInstanceOf(FormData);
    expect(args[2]).toEqual({
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    expect(result.nano_id).toBe("nano-1");
  });

  it("posts metadata update to nanos metadata endpoint", async () => {
    const postSpy = vi.spyOn(httpClient, "post").mockResolvedValue(
      createAxiosResponse({
        nano_id: "nano-1",
        status: "draft",
        message: "Metadata updated successfully",
        updated_fields: ["title"],
      })
    );

    await updateNanoMetadata("nano-1", { title: "My title", language: "de" });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/metadata", {
      title: "My title",
      language: "de",
    });
  });

  it("patches status endpoint for publish transition", async () => {
    const patchSpy = vi.spyOn(httpClient, "patch").mockResolvedValue(
      createAxiosResponse({
        nano_id: "nano-1",
        old_status: "draft",
        new_status: "published",
        message: "ok",
        published_at: "2026-03-20T12:01:00Z",
        archived_at: null,
      })
    );

    await publishNano("nano-1");

    expect(patchSpy).toHaveBeenCalledWith("/api/v1/nanos/nano-1/status", {
      status: "published",
    });
  });
});
