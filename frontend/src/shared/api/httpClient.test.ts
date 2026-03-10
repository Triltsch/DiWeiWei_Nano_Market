/**
 * HTTP Client Tests
 *
 * Tests for centralized Axios configuration and auth interceptor behavior.
 */

import axios, { AxiosHeaders } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";

import { API_CONFIG } from "./config";
import { setAuthSession, clearAuthSession, getAccessToken } from "./authSession";
import { httpClient } from "./httpClient";

function createRequestConfig(
  config: Partial<InternalAxiosRequestConfig> = {}
): InternalAxiosRequestConfig {
  return {
    headers: new AxiosHeaders(),
    url: "/api/v1/test",
    method: "get",
    ...config,
  } as InternalAxiosRequestConfig;
}

function getRequestHandlers() {
  const handlers = httpClient.interceptors.request.handlers;
  expect(handlers?.length).toBeGreaterThan(0);
  return handlers as NonNullable<typeof handlers>;
}

function getResponseHandlers() {
  const handlers = httpClient.interceptors.response.handlers;
  expect(handlers?.length).toBeGreaterThan(0);
  return handlers as NonNullable<typeof handlers>;
}

function runRequestInterceptors(
  initialConfig: InternalAxiosRequestConfig
): InternalAxiosRequestConfig {
  let config = initialConfig;

  for (const handler of getRequestHandlers()) {
    if (!handler.fulfilled) continue;

    const next = handler.fulfilled(config);
    if (next instanceof Promise) {
      throw new Error("Request interceptor unexpectedly returned a Promise");
    }

    config = next;
  }

  return config;
}

describe("HTTP Client - API Configuration", () => {
  /**
   * Verifies that API configuration constants are properly defined.
   * Ensures BASE_URL, REQUEST_TIMEOUT, and VERSION are available and valid.
   */
  it("loads API config", () => {
    expect(API_CONFIG.BASE_URL).toBeDefined();
    expect(API_CONFIG.REQUEST_TIMEOUT).toBeGreaterThan(0);
    expect(API_CONFIG.VERSION).toBe("v1");
  });

  /**
   * Verifies that httpClient is configured with required defaults.
   * Checks that baseURL, timeout, and withCredentials settings are correctly applied.
   */
  it("creates httpClient with expected defaults", () => {
    expect(httpClient.defaults.baseURL).toBe(API_CONFIG.BASE_URL);
    expect(httpClient.defaults.timeout).toBe(API_CONFIG.REQUEST_TIMEOUT);
    expect(httpClient.defaults.withCredentials).toBe(true);
  });
});

describe("HTTP Client - Request Interceptor", () => {
  beforeEach(() => {
    clearAuthSession();
  });

  afterEach(() => {
    clearAuthSession();
  });

  /**
   * Verifies that the request interceptor injects the access token from auth session.
   * When a valid access token exists, it should be added as Authorization: Bearer <token>.
   */
  it("injects access token into Authorization header", () => {
    setAuthSession(
      {
        accessToken: "access-token-1",
        refreshToken: "refresh-token-1",
        expiresIn: 900,
      },
      { email: "tester@example.com" }
    );

    const config = runRequestInterceptors(createRequestConfig());
    expect(config.headers.Authorization).toBe("Bearer access-token-1");
  });

  /**
   * Verifies that the request interceptor gracefully handles missing access token.
   * When no token is available in auth session, Authorization header should not be set.
   */
  it("does not inject Authorization when access token missing", () => {
    const config = runRequestInterceptors(createRequestConfig());
    expect(config.headers.Authorization).toBeUndefined();
  });
});

describe("HTTP Client - Response Interceptor", () => {
  beforeEach(() => {
    clearAuthSession();
  });

  afterEach(() => {
    clearAuthSession();
    vi.restoreAllMocks();
  });

  /**
   * Verifies 401 response handler refreshes token and retries the original request.
   * When a request fails with 401, the response interceptor should:
   * 1. Call the refresh token endpoint
   * 2. Update stored tokens with fresh ones
   * 3. Retry the original request with the new access token
   * 4. Return the successful retry response
   */
  it("refreshes and retries request after 401", async () => {
    const retryResponse = { data: { ok: true } } as AxiosResponse<{ ok: boolean }>;

    setAuthSession(
      {
        accessToken: "expired-access",
        refreshToken: "refresh-token-1",
        expiresIn: 900,
      },
      { email: "tester@example.com" }
    );

    const axiosPostSpy = vi.spyOn(axios, "post").mockResolvedValue({
      data: {
        access_token: "fresh-access",
        refresh_token: "fresh-refresh",
        expires_in: 900,
      },
    } as AxiosResponse);

    const instanceSpy = vi.spyOn(httpClient, "request").mockResolvedValue(retryResponse);

    const rejectedHandler = getResponseHandlers().find((handler) => handler.rejected)?.rejected;
    if (!rejectedHandler) {
      throw new Error("Response interceptor rejected handler missing");
    }

    const error = {
      response: { status: 401 },
      config: createRequestConfig({ url: "/api/v1/protected" }),
      message: "Unauthorized",
    } as unknown as Error;

    const result = await rejectedHandler(error);

    expect(axiosPostSpy).toHaveBeenCalledOnce();
    expect(instanceSpy).toHaveBeenCalledOnce();
    expect(getAccessToken()).toBe("fresh-access");
    expect(result).toEqual(retryResponse);
  });

  /**
   * Verifies error handling when token refresh fails.
   * When refresh endpoint returns an error, the response interceptor should:
   * 1. Clear the auth session (tokens and user)
   * 2. Dispatch auth:unauthorized event to notify listeners
   * 3. Reject the promise to propagate the error
   */
  it("clears session when refresh fails", async () => {
    const unauthorizedEventSpy = vi.fn();
    window.addEventListener("auth:unauthorized", unauthorizedEventSpy);

    setAuthSession(
      {
        accessToken: "expired-access",
        refreshToken: "refresh-token-1",
        expiresIn: 900,
      },
      { email: "tester@example.com" }
    );

    vi.spyOn(axios, "post").mockRejectedValue(new Error("refresh failed"));

    const rejectedHandler = getResponseHandlers().find((handler) => handler.rejected)?.rejected;
    if (!rejectedHandler) {
      throw new Error("Response interceptor rejected handler missing");
    }

    const error = {
      response: { status: 401 },
      config: createRequestConfig({ url: "/api/v1/protected" }),
      message: "Unauthorized",
    } as unknown as Error;

    await expect(rejectedHandler(error)).rejects.toBeInstanceOf(Error);
    expect(getAccessToken()).toBeNull();
    expect(unauthorizedEventSpy).toHaveBeenCalled();

    window.removeEventListener("auth:unauthorized", unauthorizedEventSpy);
  });

  /**
   * Verifies that concurrent 401 responses share a single refresh request.
   * When multiple requests fail at the same time, they should await one in-flight
   * refresh operation instead of issuing parallel refresh calls with the same token.
   */
  it("reuses an in-flight refresh request for concurrent 401 responses", async () => {
    const retryResponses = [
      { data: { ok: "first" } } as AxiosResponse<{ ok: string }>,
      { data: { ok: "second" } } as AxiosResponse<{ ok: string }>,
    ];

    setAuthSession(
      {
        accessToken: "expired-access",
        refreshToken: "shared-refresh-token",
        expiresIn: 900,
      },
      { email: "tester@example.com" }
    );

    let resolveRefresh: ((value: AxiosResponse) => void) | undefined;
    const refreshPromise = new Promise<AxiosResponse>((resolve) => {
      resolveRefresh = resolve;
    });

    const axiosPostSpy = vi.spyOn(axios, "post").mockReturnValue(refreshPromise);
    const instanceSpy = vi
      .spyOn(httpClient, "request")
      .mockResolvedValueOnce(retryResponses[0])
      .mockResolvedValueOnce(retryResponses[1]);

    const rejectedHandler = getResponseHandlers().find((handler) => handler.rejected)?.rejected;
    if (!rejectedHandler) {
      throw new Error("Response interceptor rejected handler missing");
    }

    const firstError = {
      response: { status: 401 },
      config: createRequestConfig({ url: "/api/v1/protected/one" }),
      message: "Unauthorized",
    } as unknown as Error;

    const secondError = {
      response: { status: 401 },
      config: createRequestConfig({ url: "/api/v1/protected/two" }),
      message: "Unauthorized",
    } as unknown as Error;

    const firstRetryPromise = rejectedHandler(firstError);
    const secondRetryPromise = rejectedHandler(secondError);

    expect(axiosPostSpy).toHaveBeenCalledOnce();

    resolveRefresh?.({
      data: {
        access_token: "fresh-access",
        refresh_token: "fresh-refresh",
        expires_in: 900,
      },
    } as AxiosResponse);

    const [firstResult, secondResult] = await Promise.all([firstRetryPromise, secondRetryPromise]);

    expect(instanceSpy).toHaveBeenCalledTimes(2);
    expect(getAccessToken()).toBe("fresh-access");
    expect(firstResult).toEqual(retryResponses[0]);
    expect(secondResult).toEqual(retryResponses[1]);
  });
});
