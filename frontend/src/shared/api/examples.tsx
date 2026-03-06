/**
 * Example: Using HTTP Client in React Components
 *
 * This file demonstrates how to use the centralized HTTP client
 * for API communication in React components.
 *
 * This is an example file showing best practices.
 * Not part of the actual app - included for reference.
 */

import { useState, useEffect } from "react";
import { httpClient } from "../api";

/**
 * Example Hook: useAuth
 * Demonstrates login/logout flow with HTTP client
 */
export function useAuthExample() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Login request - this call obtains tokens; interceptor injects a token only if one already exists
      const response = await httpClient.post("/api/v1/auth/login", {
        email,
        password,
      });

      // Store tokens in localStorage
      const { access_token, refresh_token, expires_in } = response.data;
      localStorage.setItem(
        "auth_tokens",
        JSON.stringify({
          accessToken: access_token,
          refreshToken: refresh_token,
          expiresIn: expires_in,
        })
      );

      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Logout request - token is automatically injected
      await httpClient.post("/api/v1/auth/logout", {});

      // Clear tokens from localStorage
      localStorage.removeItem("auth_tokens");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Logout failed";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return { login, logout, isLoading, error };
}

/**
 * Example Hook: useFetchData
 * Demonstrates data fetching with error handling
 */
export function useFetchDataExample<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // HTTP client automatically includes auth token if stored
        const response = await httpClient.get<T>(url);
        if (mounted) {
          setData(response.data);
        }
      } catch (err) {
        if (mounted) {
          const message = err instanceof Error ? err.message : "Failed to fetch";
          setError(message);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      mounted = false;
    };
  }, [url]);

  return { data, isLoading, error };
}

/**
 * Example Component: LoginForm
 * Shows how to use useAuth hook
 */
export function LoginFormExample() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error } = useAuthExample();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Redirect to dashboard or home page
      window.location.href = "/dashboard";
    } catch (err) {
      // Error is handled in hook, displayed via error state
      console.error("Login error:", err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        disabled={isLoading}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? "Logging in..." : "Login"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </form>
  );
}

/**
 * Example Component: UserProfile
 * Shows how to use useFetchData hook with HTTP client
 */
interface User {
  id: string;
  email: string;
  first_name: string;
  username: string;
}

export function UserProfileExample() {
  // HTTP client automatically injects token for authenticated request
  const { data: user, isLoading, error } = useFetchDataExample<User>(
    "/api/v1/auth/me"
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user found</div>;

  return (
    <div>
      <h1>{user.first_name}</h1>
      <p>Email: {user.email}</p>
      <p>Username: {user.username}</p>
    </div>
  );
}

/**
 * Understanding the Token Flow in Examples
 *
 * 1. Login Flow:
 *    - User submits email/password
 *    - login() calls httpClient.post("/api/v1/auth/login", {...})
 *    - Response includes access_token and refresh_token
 *    - Tokens stored in localStorage under key "auth_tokens"
 *
 * 2. Authenticated Requests:
 *    - Any subsequent request via httpClient.get/post/etc. is intercepted
 *    - Request interceptor reads tokens from localStorage
 *    - Adds Authorization header: "Bearer {accessToken}"
 *    - Request sent with auth header
 *
 * 3. Error Handling:
 *    - On 401 (unauthorized):
 *      - Response interceptor clears tokens from localStorage
 *      - Dispatches "auth:unauthorized" event for app to handle
 *      - App should redirect to login
 *    - On other errors:
 *      - Error passed to catch block for app-specific handling
 *
 * 4. Token Refresh (Sprint 3):
 *    - Currently: 401 clears tokens, user must re-login
 *    - Sprint 3: Will use refresh_token to get new access_token
 *    - Retry original request with new token
 */
