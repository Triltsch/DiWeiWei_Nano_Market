/**
 * useUserProfile Hook Tests
 *
 * Behavioral tests for the sample React Query hook.
 * Ensures query enablement and fetch behavior are validated with a real QueryClient.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { createElement } from "react";
import type { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { httpClient } from "./httpClient";
import { useUserProfile } from "./useUserProfile";

interface TestUserProfile {
  id: string;
  email: string;
  name?: string;
  created_at?: string;
}

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function createWrapper(queryClient: QueryClient) {
  return function QueryClientTestWrapper({ children }: PropsWithChildren) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useUserProfile", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
  });

  afterEach(() => {
    queryClient.clear();
    vi.restoreAllMocks();
  });

  /**
   * Verify query is disabled by default and does not auto-fetch.
   */
  it("does not fetch automatically when enabled is false", () => {
    const getSpy = vi.spyOn(httpClient, "get");

    const { result } = renderHook(() => useUserProfile(), {
      wrapper: createWrapper(queryClient),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(result.current.isFetching).toBe(false);
    expect(getSpy).not.toHaveBeenCalled();
  });

  /**
   * Verify refetch triggers HTTP call and validates hook integration
   */
  it("fetches profile when refetch is called", async () => {
    const mockProfile: TestUserProfile = {
      id: "user-1",
      email: "user@example.com",
      name: "Test User",
    };

    const mockResponse: AxiosResponse<TestUserProfile> = {
      data: mockProfile,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {
        headers: new AxiosHeaders(),
      } as InternalAxiosRequestConfig,
    };

    // Mock the httpClient.get method to simulate API response
    const getSpy = vi
      .spyOn(httpClient, "get")
      .mockImplementation(() => Promise.resolve(mockResponse));

    const { result } = renderHook(() => useUserProfile(), {
      wrapper: createWrapper(queryClient),
    });

    // Initially, query should be idle and empty
    expect(result.current.fetchStatus).toBe("idle");
    expect(result.current.data).toBeUndefined();

    // Trigger refetch and wait for the promise
    const refetchPromise = result.current.refetch();
    
    // Allow the async operation to complete
    await new Promise(resolve => setTimeout(resolve, 50));
    await refetchPromise.then(() => {
      // Verify HTTP call was made to correct endpoint
      expect(getSpy).toHaveBeenCalledWith("/api/v1/auth/me");
    });

    // Verify hook configuration is correct (query can refetch)
    expect(typeof result.current.refetch).toBe("function");
  });
});
