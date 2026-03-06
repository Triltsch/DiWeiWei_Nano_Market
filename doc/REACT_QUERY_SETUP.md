# React Query Configuration & App Providers

This document describes the React Query integration and centralized provider composition for the DiWeiWei Nano Market frontend.

## Overview

React Query (TanStack Query) is configured to manage server state and asynchronous data fetching across the application. All providers are centrally composed in `AppProviders` for clean application setup.

## Files

- `src/shared/queryClient.ts` - React Query client configuration with sensible defaults
- `src/shared/AppProviders.tsx` - Centralized provider composition (React Query + Router)
- `src/shared/api/useUserProfile.ts` - Sample query hook for smoke validation
- `vitest.setup.ts` - Test environment configuration

## Query Client Configuration

The React Query client uses these sensible defaults:

| Setting | Value | Purpose |
|---------|-------|---------|
| **staleTime** | 1 minute | Data is considered fresh for 1 minute |
| **gcTime** (formerly cacheTime) | 5 minutes | Cached data retained for 5 minutes before garbage collection |
| **retry** | 1 | Failed queries retry once before giving up |
| **retryDelay** | Exponential backoff (1s, 2s, 4s...) | Prevent server overload on failures |

These defaults balance between:
- **User experience**: Fresh data, quick acknowledgment of errors
- **Network efficiency**: Reduced redundant requests via caching
- **Server load**: Controlled retry behavior with exponential backoff

### Configuration Location

```typescript
// src/shared/queryClient.ts
export const queryClient = createQueryClient();
```

To adjust defaults, edit `queryClient.ts`:

```typescript
queryClient: {
  staleTime: 1000 * 60,           // Change fresh data duration
  gcTime: 1000 * 60 * 5,           // Change cache retention
  retry: 2,                        // Increase retry attempts
  retryDelay: (attempt) => ...    // Customize retry timing
}
```

## App Providers Setup

The `AppProviders` component centralizes all application-level providers:

```tsx
// src/shared/AppProviders.tsx
<QueryClientProvider client={queryClient}>
  <BrowserRouter>
    {children}
  </BrowserRouter>
</QueryClientProvider>
```

### Integration in Application Root

```tsx
// src/main.tsx
import { AppProviders } from "./shared/AppProviders"
import { App } from "./app/App"

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>
)
```

This ensures:
- React Query client is available to all components
- Router context is available for navigation
- Both providers are composed in correct order (Query first, then Router)

## Query Hooks

### Sample Query Hook: useUserProfile

A sample query hook demonstrates React Query integration:

```typescript
// src/shared/api/useUserProfile.ts
export function useUserProfile() {
  return useQuery({
    queryKey: ["auth", "profile"],
    queryFn: () => httpClient.get("/api/v1/auth/me"),
    enabled: false,  // Don't fetch until explicitly enabled
  })
}
```

**Usage in components:**

```tsx
import { useUserProfile } from "../shared/api"

function Profile() {
  const { data: profile, isLoading, error, refetch } = useUserProfile()

  return (
    <div>
      <button onClick={() => refetch()}>Load Profile</button>
      {isLoading && <div>Loading...</div>}
      {error && <div>Error: {error.message}</div>}
      {profile && <div>Hello {profile.name}</div>}
    </div>
  )
}
```

## Creating New Query Hooks

Follow this pattern when creating new query hooks:

```typescript
/**
 * Fetch items from the API
 */
async function fetchItems(): Promise<Item[]> {
  const response = await httpClient.get<Item[]>("/api/v1/items")
  return response.data
}

/**
 * Hook to fetch items
 */
export function useItems() {
  return useQuery({
    queryKey: ["items"],           // Unique cache key
    queryFn: fetchItems,           // Fetch function
    staleTime: 1000 * 60 * 5,      // Override default staletime if needed
    enabled: true,                 // Fetch immediately
  })
}
```

### Query Key Convention

Use array query keys with hierarchical structure for proper cache management:

```typescript
// Top-level resources
["users"]
["items"]
["search"]

// Resource-specific
["users", userId]
["items", itemId]
["search", query]

// Nested relationships
["users", userId, "posts"]
["items", itemId, "reviews"]
```

## Testing Query Hooks

Tests for query hooks should wrap them with `QueryClientProvider`:

```typescript
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook } from "@testing-library/react"

function createWrapper() {
  const testQueryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }  // Disable retries in tests
    }
  })

  return ({ children }) => (
    <QueryClientProvider client={testQueryClient}>
      {children}
    </QueryClientProvider>
  )
}

it("should fetch data", () => {
  const { result } = renderHook(() => useItems(), {
    wrapper: createWrapper()
  })
  
  // Test assertions...
})
```

## Mutation Hooks (Sprint 3)

Mutations for POST/PUT/DELETE operations will follow similar patterns:

```typescript
import { useMutation } from "@tanstack/react-query"

export function useCreateItem() {
  return useMutation({
    mutationFn: async (item) => {
      const response = await httpClient.post("/api/v1/items", item)
      return response.data
    },
    onSuccess: (newItem) => {
      // Invalidate cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ["items"] })
    }
  })
}
```

## Integration with API Client

React Query hooks always use the centralized `httpClient` (src/shared/api/httpClient.ts):

```typescript
import { httpClient } from "./httpClient"

async function fetchUserProfile() {
  // httpClient automatically injects JWT token in Authorization header
  const response = await httpClient.get("/api/v1/auth/me")
  return response.data
}
```

This ensures:
- Consistent error handling across API calls
- Automatic JWT token injection for authenticated requests
- Centralized request/response logging (dev mode)
- Unified retry and timeout configuration

## Environment Configuration

React Query defaults work with any backend. No additional environment variables needed.

For custom behavior per environment, set in `queryClient.ts`:

```typescript
const isDev = import.meta.env.DEV

return new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: isDev ? 0 : 1000 * 60,  // Disable caching in dev
      retry: isDev ? false : 1,          // No retries in dev
    }
  }
})
```

## DevTools (Optional)

For debugging React Query in browser, install React Query DevTools in Sprint 3:

```bash
npm install @tanstack/react-query-devtools
```

Then add to app:

```tsx
import TanStackQueryDevtools from "@tanstack/react-query-devtools"

<QueryClientProvider client={queryClient}>
  {/* ... app content ... */}
  <TanStackQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

This provides a browser panel showing:
- All queries and their states
- Cache life cycle
- Query history and debugging tools

## Acceptance Criteria Progress

✅ Query client configured with sane defaults  
✅ Provider wiring active in app root  
✅ Sample query path included for smoke validation

## Sprint 3 Integration

In Sprint 3, this foundation will support:
- Query invalidation on mutations
- Dependent queries for data relationships
- Mutation state management for form submissions
- Background refetch strategies
- Optimistic updates for better UX
