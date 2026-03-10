/**
 * HTTP Request/Response Interceptors
 *
 * Handles:
 * - JWT access token injection in Authorization header
 * - Automatic token refresh and request retry on 401
 * - Request logging in development mode
 */

import axios, {
  AxiosHeaders,
  type AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

import { clearAuthSession, getAccessToken, getRefreshToken, updateAuthTokens } from "./authSession";

interface TokenRefreshResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

function setAuthorizationHeader(config: InternalAxiosRequestConfig, token: string): void {
  if (!config.headers) {
    config.headers = new AxiosHeaders();
  }

  if (config.headers instanceof AxiosHeaders) {
    config.headers.set("Authorization", `Bearer ${token}`);
    return;
  }

  (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
}

function handleUnauthorized(): void {
  clearAuthSession();
  window.dispatchEvent(new CustomEvent("auth:unauthorized"));
}

export function setupRequestInterceptor(instance: AxiosInstance): void {
  instance.interceptors.request.use(
    (config) => {
      const accessToken = getAccessToken();

      if (accessToken) {
        setAuthorizationHeader(config, accessToken);
      }

      if (import.meta.env.DEV) {
        console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data || "");
      }

      return config;
    },
    (error) => Promise.reject(error)
  );
}

export function setupResponseInterceptor(instance: AxiosInstance): void {
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      if (import.meta.env.DEV) {
        console.debug(`[API] Response ${response.status}:`, response.data);
      }

      return response;
    },
    async (error: AxiosError) => {
      const statusCode = error.response?.status;
      const originalRequest = error.config as RetriableRequestConfig | undefined;

      if (
        statusCode === 401 &&
        originalRequest &&
        !originalRequest._retry &&
        !originalRequest.url?.includes("/api/v1/auth/refresh-token")
      ) {
        const storedRefreshToken = getRefreshToken();

        if (!storedRefreshToken) {
          handleUnauthorized();
          return Promise.reject(error);
        }

        originalRequest._retry = true;

        try {
          const response = await axios.post<TokenRefreshResponse>(
            `${instance.defaults.baseURL}/api/v1/auth/refresh-token`,
            { refresh_token: storedRefreshToken },
            {
              timeout: instance.defaults.timeout,
              withCredentials: true,
              headers: {
                "Content-Type": "application/json",
              },
            }
          );

          updateAuthTokens({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresIn: response.data.expires_in,
          });

          setAuthorizationHeader(originalRequest, response.data.access_token);
          return instance.request(originalRequest);
        } catch (refreshError) {
          handleUnauthorized();
          return Promise.reject(refreshError);
        }
      }

      if (statusCode === 401) {
        handleUnauthorized();
      }

      if (import.meta.env.DEV) {
        console.error(`[API] Error ${statusCode || "unknown"}:`, error.message);
      }

      return Promise.reject(error);
    }
  );
}

export function setupInterceptors(instance: AxiosInstance): void {
  setupRequestInterceptor(instance);
  setupResponseInterceptor(instance);
}
