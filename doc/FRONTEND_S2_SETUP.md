# Frontend Development - Sprint 2 Updates (S2-FE-05)

This document summarizes the frontend setup changes from Sprint 2 issues S2-FE-04 and S2-FE-05.

## Overview

The frontend now has a complete, production-ready data-fetching stack:

1. **React Query** (S2-FE-05) - Centralized async state management
2. **AppProviders** (S2-FE-05) - Centralized provider composition  
3. **Axios HTTP Client** (S2-FE-04) - Centralized API communication with JWT injection
4. **React Router** (S2-FE-03) - Client-side routing

## What Was Added in S2-FE-05

### 1. React Query Installation

```bash
npm install @tanstack/react-query
npm install --save-dev @testing-library/react @testing-library/jest-dom
```

### 2. Query Client Configuration (src/shared/queryClient.ts)

Central React Query configuration with sensible defaults:

```typescript
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,           // 1 minute - data fresh duration
      gcTime: 1000 * 60 * 5,          // 5 minutes - cache retention
      retry: 1,                       // Retry failed queries once
      retryDelay: (attempt) => Math.pow(2, attempt) * 1000,  // Exponential backoff
    },
  },
});
```

**Why these defaults?**
- **Stale time = 1 min**: Reduces unnecessary refetches while keeping data relatively fresh
- **GC time = 5 min**: Balances memory usage with cache benefits
- **Retry = 1**: Handles transient network issues without hammering the server
- **Exponential backoff**: Avoids server overload on widespread outages

### 3. Centralized Provider Composition (src/shared/AppProviders.tsx)

All app-level providers are composed in one component:

```typescript
export function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

**Advantage**: Clean application root without deeply nested providers

### 4. Integration in Application Root (src/main.tsx)

```typescript
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>
)
```

### 5. Sample Query Hook for Smoke Test (src/shared/api/useUserProfile.ts)

Demonstrates React Query integration:

```typescript
export function useUserProfile() {
  return useQuery({
    queryKey: ["auth", "profile"],
    queryFn: () => httpClient.get("/api/v1/auth/me"),
    enabled: false,
  })
}
```

### 6. Test Infrastructure Update (vitest.setup.ts)

Added test environment configuration:

```typescript
afterEach(() => {
  cleanup()  // Clean up components after each test
})

// Setup custom matchers
import "@testing-library/jest-dom"
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        App Root                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          AppProviders Component                     │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  QueryClientProvider                         │  │  │
│  │  │  (React Query State Management)              │  │  │
│  │  │                                              │  │  │
│  │  │  ┌────────────────────────────────────────┐ │  │  │
│  │  │  │  BrowserRouter                         │ │  │  │
│  │  │  │  (React Router Context)                │ │  │  │
│  │  │  │                                        │ │  │  │
│  │  │  │  ┌──────────────────────────────────┐ │ │  │  │
│  │  │  │  │  App Component                   │ │ │  │  │
│  │  │  │  │  - Can use useQuery hooks        │ │ │  │  │
│  │  │  │  │  - Can use React Router hooks    │ │ │  │  │
│  │  │  │  └──────────────────────────────────┘ │ │  │  │
│  │  │  └────────────────────────────────────────┘ │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## File Structure Changes

```
frontend/src/
├── shared/
│   ├── api/
│   │   ├── httpClient.ts          (existing - S2-FE-04)
│   │   ├── config.ts              (existing)
│   │   ├── interceptors.ts        (existing - S2-FE-04)
│   │   ├── index.ts               (updated to export hooks)
│   │   ├── useUserProfile.ts      (NEW - sample query hook)
│   │   ├── useUserProfile.test.ts (NEW - hook tests)
│   │   └── README.md              (existing)
│   ├── AppProviders.tsx           (NEW - provider composition)
│   └── queryClient.ts             (NEW - React Query config)
├── app/
│   ├── App.tsx                    (unchanged)
│   ├── router.tsx                 (updated - removed BrowserRouter wrapper)
│   └── styles.css                 (unchanged)
└── main.tsx                       (updated - uses AppProviders)

root/
├── vitest.setup.ts                (NEW - test configuration)
├── vite.config.ts                 (updated - references vitest.setup.ts)
├── package.json                   (updated - new dependencies)
└── ...
```

## Dependencies Added

### Production

- `@tanstack/react-query` - Server state management

### Development

- `@testing-library/react` - Component and hook testing utilities
- `@testing-library/jest-dom` - DOM custom matchers
- `@testing-library/user-event` - User interaction simulation (for future use)

## Migration Guide (If Calling from Components)

### Before (without React Query)

```typescript
function Profile() {
  const [profile, setProfile] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    setIsLoading(true)
    httpClient.get("/api/v1/auth/me")
      .then(res => setProfile(res.data))
      .finally(() => setIsLoading(false))
  }, [])

  return isLoading ? <div>Loading...</div> : <div>{profile?.name}</div>
}
```

### After (with React Query)

```typescript
import { useUserProfile } from "../shared/api"

function Profile() {
  const { data: profile, isLoading } = useUserProfile()

  return isLoading ? <div>Loading...</div> : <div>{profile?.name}</div>
}
```

**Benefits:**
- Less boilerplate
- Automatic caching
- Built-in error handling
- Automatic refetch on window focus
- DevTools support (optional)

## Testing Patterns

### Query Hook Tests

```typescript
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

function createWrapper() {
  return ({ children }) => (
    <QueryClientProvider client={new QueryClient()}>
      {children}
    </QueryClientProvider>
  )
}

it("should fetch data", async () => {
  const { result } = renderHook(() => useMyData(), { wrapper: createWrapper() })
  
  await waitFor(() => {
    expect(result.current.data).toBeDefined()
  })
})
```

### Component Tests Using Queries

```typescript
import { render, screen } from "@testing-library/react"
import { AppProviders } from "../shared/AppProviders"

it("should display user profile", async () => {
  render(
    <AppProviders>
      <Profile />
    </AppProviders>
  )

  await waitFor(() => {
    expect(screen.getByText(/Hello/)).toBeInTheDocument()
  })
})
```

## Known Limitations & Sprint 3 Work

- **No mutations yet**: Mutations for POST/PUT/DELETE will be added in Sprint 3
- **No query invalidation**: Automatic cache invalidation on mutations will be added in Sprint 3  
- **No dependent queries**: Complex data relationships handled in Sprint 3
- **No DevTools**: React Query DevTools can be added for debugging

## Acceptance Criteria Verification

✅ **Query client configured with sane defaults**
   - staleTime, gcTime, retry, and retryDelay all configured with production-ready values

✅ **Provider wiring active in app root**
   - AppProviders component wraps both QueryClientProvider and BrowserRouter
   - Integrated in main.tsx
   - All components can access both contexts

✅ **One sample query path included for smoke validation**
   - useUserProfile hook demonstrates complete React Query integration
   - Hooks exported from src/shared/api/index.ts
   - Tests verify export structure

## Running the Application

```bash
# Install dependencies (includes React Query)
npm install

# Start dev server
npm run dev

# Run tests
npm test

# Type check
npm run typecheck

# Build for production
npm run build
```

## See Also

- [React Query Setup Guide](./REACT_QUERY_SETUP.md) - Detailed configuration and patterns
- [HTTP Client Documentation](../frontend/src/shared/api/README.md) - Axios client features
- [Frontend README](../frontend/README.md) - Frontend workspace overview
