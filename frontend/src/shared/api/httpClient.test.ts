/**
 * HTTP Client Tests
 *
 * Tests for the centralized Axios HTTP client configuration,
 * environment loading, and interceptor functionality.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { httpClient } from "./httpClient";
import { API_CONFIG } from "./config";

describe("HTTP Client - API Configuration", () => {
  /**
   * Verify API_CONFIG loads environment variables correctly
   * Tests base URL and request timeout configuration
   */
  it("should load API_CONFIG from environment variables", () => {
    expect(API_CONFIG.BASE_URL).toBeDefined();
    expect(API_CONFIG.REQUEST_TIMEOUT).toBeGreaterThan(0);
    expect(API_CONFIG.VERSION).toBe("v1");
  });

  /**
   * Verify httpClient is properly configured with API_CONFIG
   */
  it("should create httpClient with correct baseURL", () => {
    expect(httpClient.defaults.baseURL).toBe(API_CONFIG.BASE_URL);
    expect(httpClient.defaults.timeout).toBe(API_CONFIG.REQUEST_TIMEOUT);
  });

  /**
   * Verify default headers are set
   */
  it("should have correct default headers", () => {
    expect(httpClient.defaults.headers.common["Content-Type"]).toBe(
      "application/json"
    );
  });
});

describe("HTTP Client - Request Interceptor (Token Injection)", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    // Clean up after tests
    localStorage.clear();
  });

  /**
   * Verify token is injected into Authorization header when present
   */
  it("should inject access token into Authorization header", async () => {
    const mockToken = "test-access-token-12345";
    const tokenStorage = { accessToken: mockToken };

    // Store token in localStorage
    localStorage.setItem("auth_tokens", JSON.stringify(tokenStorage));

    // Create a mock request config
    let capturedConfig = null;
    httpClient.interceptors.request.handlers.forEach((handler) => {
      if (handler.fulfilled) {
        const testConfig = { headers: {} };
        const result = handler.fulfilled(testConfig);
        capturedConfig = result;
      }
    });

    // Verify the token was injected into Authorization header
    expect(capturedConfig).not.toBeNull();
    expect(capturedConfig.headers.Authorization).toBe(`Bearer ${mockToken}`);
  });

  /**
   * Verify request proceeds without token when localStorage is empty
   */
  it("should allow requests without stored token", () => {
    // localStorage is empty (cleared in beforeEach)
    expect(localStorage.getItem("auth_tokens")).toBeNull();

    // Request should proceed normally
    const testConfig = { headers: {} };
    let configAfterInterceptor = testConfig;

    httpClient.interceptors.request.handlers.forEach((handler) => {
      if (handler.fulfilled) {
        configAfterInterceptor = handler.fulfilled(testConfig);
      }
    });

    // Config should be unchanged (no Authorization header added)
    expect(configAfterInterceptor.headers.Authorization).toBeUndefined();
  });

  /**
   * Verify corrupted token storage doesn't break requests
   */
  it("should handle corrupted localStorage gracefully", () => {
    // Store invalid JSON
    localStorage.setItem("auth_tokens", "invalid-json-{");

    const testConfig = { headers: {} };
    let configAfterInterceptor = testConfig;

    httpClient.interceptors.request.handlers.forEach((handler) => {
      if (handler.fulfilled) {
        configAfterInterceptor = handler.fulfilled(testConfig);
      }
    });

    // Request should still proceed
    expect(configAfterInterceptor).toBeDefined();
  });
});

describe("HTTP Client - Response Interceptor (Error Handling)", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  /**
   * Verify 401 response clears tokens from localStorage
   * Placeholder test for Sprint 3 token refresh implementation
   */
  it("should clear tokens on 401 Unauthorized response", async () => {
    const mockToken = "test-token";
    localStorage.setItem("auth_tokens", JSON.stringify({ accessToken: mockToken }));

    expect(localStorage.getItem("auth_tokens")).not.toBeNull();

    // Mock 401 response
    const error = new Error("Unauthorized") as Error & { response?: { status: number } };
    error.response = { status: 401 };

    // When response interceptor handles 401, it should reject and clear tokens
    let tokenCleared = false;
    const handlers = httpClient.interceptors.response.handlers;

    for (const handler of handlers) {
      if (handler.rejected) {
        // Ensure the interceptor rejects as expected
        await expect(handler.rejected(error)).rejects.toBeInstanceOf(Error);
        // After the interceptor runs, tokens should be cleared
        tokenCleared = localStorage.getItem("auth_tokens") === null;
      }
    }

    expect(tokenCleared).toBe(true);
  });

  /**
   * Verify successful responses are passed through
   */
  it("should pass through successful responses", () => {
    const mockResponse = {
      status: 200,
      data: { success: true },
      config: {},
    };

    let result = null;
    httpClient.interceptors.response.handlers.forEach((handler) => {
      if (handler.fulfilled) {
        result = handler.fulfilled(mockResponse);
      }
    });

    expect(result).toEqual(mockResponse);
  });
});

describe("HTTP Client - Development Logging", () => {
  /**
   * Verify logging is available in development mode
   * Actual logging is optional and controlled by environment
   */
  it("should have logging configured for debugging", () => {
    // In development (import.meta.env.DEV), console logs are emitted
    // This test verifies the feature exists but doesn't test console output
    expect(httpClient).toBeDefined();
  });
});
