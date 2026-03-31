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
  it("maps 409 username conflicts to username-already-taken", async () => {
    mockedHttpPost.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { detail: "Username already taken" },
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
      code: "username-already-taken",
    });
  });

  it("maps 409 email conflicts to email-already-registered", async () => {
    mockedHttpPost.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { detail: "Email already registered" },
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

  it("keeps unknown 409 register errors on generic request-failed code", async () => {
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
      code: "request-failed",
    });
  });
});
