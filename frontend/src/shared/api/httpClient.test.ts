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
  it("loads API config", () => {
    expect(API_CONFIG.BASE_URL).toBeDefined();
    expect(API_CONFIG.REQUEST_TIMEOUT).toBeGreaterThan(0);
    expect(API_CONFIG.VERSION).toBe("v1");
  });

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
});
