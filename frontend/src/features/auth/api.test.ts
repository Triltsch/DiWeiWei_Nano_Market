import { describe, expect, it, vi } from "vitest";

import { httpClient } from "../../shared/api/httpClient";
import { registerUser } from "./api";

vi.mock("../../shared/api/httpClient", () => ({
  httpClient: {
    post: vi.fn(),
  },
}));

const mockedHttpPost = vi.mocked(httpClient.post);

describe("registerUser", () => {
  it("maps 409 responses to email-already-registered even with varying backend detail", async () => {
    mockedHttpPost.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { detail: "Benutzer schon vorhanden" },
      },
    });

    await expect(
      registerUser({
        email: "user@example.com",
        username: "user123",
        password: "StrongPass1!",
        acceptTerms: true,
        acceptPrivacy: true,
      })
    ).rejects.toMatchObject({
      code: "email-already-registered",
    });
  });

  it("keeps non-409 register errors on generic request-failed code", async () => {
    mockedHttpPost.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 400,
        data: { detail: "Some unrelated validation message" },
      },
    });

    await expect(
      registerUser({
        email: "user@example.com",
        username: "user123",
        password: "StrongPass1!",
        acceptTerms: true,
        acceptPrivacy: true,
      })
    ).rejects.toMatchObject({
      code: "request-failed",
    });
  });
});
