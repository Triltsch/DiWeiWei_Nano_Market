# HTTP Client Usage Documentation

This file documents how to use the centralized HTTP client for API communication in the DiWeiWei Nano Market frontend.

## Overview

The HTTP client provides:

- Environment-based configuration (base URL, timeout)
- Automatic JWT token injection in request headers
- Error handling with placeholder for token refresh (Sprint 3)
- Request/response logging in development mode

## Files

- `shared/api/httpClient.ts` - Main HTTP client instance (export: `httpClient`)
- `shared/api/config.ts` - API configuration from environment variables
- `shared/api/interceptors.ts` - Request/response interceptors
- `shared/api/index.ts` - Module exports

## Environment Configuration

Create `.env.local` in the `frontend/` directory with:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_API_REQUEST_TIMEOUT=30000
VITE_DEV_SERVER_HOST=localhost
```

Or copy from `.env.example`:

```bash
cp frontend/.env.example frontend/.env.local
```

## Usage Examples

### Basic GET Request

```typescript
import { httpClient } from "../shared/api";

async function fetchUserProfile() {
  try {
    const response = await httpClient.get("/api/v1/auth/me");
    console.log("User profile:", response.data);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch profile:", error);
  }
}
```

### POST Request with Data

```typescript
import { httpClient } from "../shared/api";

async function login(email: string, password: string) {
  try {
    const response = await httpClient.post("/api/v1/auth/login", {
      email,
      password,
    });

    // Store tokens
    localStorage.setItem(
      "auth_tokens",
      JSON.stringify({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in,
      })
    );

    return response.data;
  } catch (error) {
    console.error("Login failed:", error);
  }
}
```

### Authenticated Request (Token Auto-Injected)

```typescript
import { httpClient } from "../shared/api";

async function uploadNano(file: File) {
  try {
    // Token is automatically injected by request interceptor
    const formData = new FormData();
    formData.append("file", file);

    const response = await httpClient.post("/api/v1/upload/nano", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Upload failed:", error);
  }
}
```

### Error Handling

```typescript
import { httpClient } from "../shared/api";
import type { AxiosError } from "axios";

async function fetchData() {
  try {
    const response = await httpClient.get("/api/v1/data");
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;

    if (axiosError.response?.status === 401) {
      // Unauthorized - token is cleared by response interceptor
      // App should redirect to login
      window.location.href = "/login";
    } else if (axiosError.response?.status === 403) {
      // Forbidden - user doesn't have permission
      console.error("Access denied");
    } else if (axiosError.response?.status === 404) {
      // Not found
      console.error("Resource not found");
    } else if (axiosError.code === "ECONNABORTED") {
      // Request timeout
      console.error("Request timeout - server not responding");
    } else {
      // Other error
      console.error("Request failed:", axiosError.message);
    }
  }
}
```

## Token Flow

### Token Storage

Access and refresh tokens are stored in localStorage:

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresIn": 900
}
```

Storage key: `auth_tokens`

### Request Interceptor

1. Checks localStorage for stored tokens
2. If access token exists, adds it to Authorization header: `Bearer <token>`
3. Passes request to backend

### Response Interceptor (Sprint 3 TODO)

1. On 401 response:
   - Gets refresh token from localStorage
   - Calls POST /api/v1/auth/refresh-token
   - Updates access token in localStorage
   - Retries original request with new token
2. On other errors:
   - Passes error through for app-specific handling

Current Status: Placeholder for Sprint 3

- 401 responses clear tokens and dispatch auth:unauthorized event
- App should listen for this event and redirect to login

## Logging

In development mode (Vite dev server), all requests and responses are logged:

```
[API] GET /api/v1/auth/me
[API] Response 200: {success: true, data: {...}}
```

Errors are also logged:

```
[API] Unauthorized request - 401
[API] Error 401: Unauthorized
```

## API Endpoints

All endpoints are at `/api/v1/{endpoint}`:

### Authentication

- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh-token` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/verify-email` - Verify email with token

### Uploads

- `POST /api/v1/upload/nano` - Upload Nano ZIP file

### Admin (Audit)

- `GET /api/v1/admin/audit-logs` - Query audit logs
- `GET /api/v1/admin/audit-logs/recent` - Get recent logs
- `GET /api/v1/admin/audit-logs/suspicious/{user_id}` - Detect suspicious activity

Full API documentation: http://localhost:8000/docs

---

**Note**: This file serves as documentation only. Import the httpClient from `shared/api/httpClient.ts` for actual usage.
