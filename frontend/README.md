# Frontend Workspace (S2-FE-03 / S2-FE-06)

React 18 + Vite + TypeScript (strict mode) baseline for Nano Market frontend development.

## Commands

### Development & Building

```bash
npm install
npm run dev        # Start dev server with API proxy to http://localhost:8000
npm run build      # TypeScript check + Vite production build
npm run preview    # Preview production build locally
npm run typecheck  # Run TypeScript type checking
```

### Code Quality & Testing

```bash
npm run lint       # Run ESLint checks on src/
npm run lint:fix   # Auto-fix ESLint issues
npm run format     # Format code with Prettier
npm test           # Run Vitest in watch mode
npm run test -- --run
npx vitest run     # Run tests once and exit
```

## Development Proxy

The Vite dev server (`npm run dev`) includes a dev proxy that forwards API requests to the backend:

- Dev server runs on `http://localhost:5173`
- Proxy forwards `/api/*` requests to `http://localhost:8000` (configurable via `VITE_API_BASE_URL`)
- **Path preservation**: Requests keep the `/api` prefix when forwarded (backend routes are mounted at `/api/v1/*`)
- Backend must be running on port 8000 for API calls to work

### Example
```bash
# Terminal 1: Start backend (should run on :8000)
cd ..
python -m uvicorn app.main:app --reload

# Terminal 2: Start frontend dev server
cd frontend
npm run dev

# Frontend call to /api/v1/auth/me → proxied to → http://localhost:8000/api/v1/auth/me
```

## Code Quality

- **Linting**: ESLint v8 with React and TypeScript plugins
- **Formatting**: Prettier with enforced LF line endings
- **Type Safety**: TypeScript strict mode enabled
- **Testing**: Vitest with React Testing Library

Run all checks:
```bash
npm run lint && npm run format && npm run typecheck && npm test -- --run
```

## Docker Development

Frontend is included in the Docker Compose stack:

```bash
docker compose up frontend  # Starts Vite dev server with live reload on :3000
```

The Compose frontend service is optimized for day-to-day UI development:

- Source code is bind-mounted from `./frontend` into the container
- `node_modules` lives in a named Docker volume to avoid host/container conflicts
- Vite file watching uses polling so changes are detected reliably on Docker Desktop / Windows
- The browser still uses `http://localhost:3000`, while the Vite dev server runs on port `5173` inside the container
- API proxying is configured to reach the backend service at `http://app:8000`

The `Dockerfile.frontend` now supports two modes:
1. `development` stage: Node.js 20 Alpine - runs Vite dev server for Compose live reload
2. `builder` + `production` stages: builds and serves `/dist` with Nginx for static production-style delivery

## Structure

- `src/app` - app entry and global styles
- `src/features` - feature modules
- `src/shared` - shared UI/components/utilities including HTTP client and React Query setup

## Routing Baseline

React Router v6 routes are wired in `src/app/router.tsx` with implemented auth flow:

- `/` landing page
- `/search` discovery/search UI (debounced keyword search, backend-aligned filters, load-more pagination backed by page-based API metadata, URL query sync)
- `/nano/:id` nano detail page (backend detail contract integration, loading/error/not-found states, auth-gated download CTA, ratings and chat CTA areas)
- `/register` registration form (React Hook Form + client validation)
- `/login` login form with remember-email support
- `/verify-email` verification pending + token auto-verification flow
- `/profile` protected for authenticated users
- `/dashboard`, `/creator-dashboard`, `/upload`, `/nanos/:id/edit` protected for roles `creator|moderator|admin`
- `/moderator/queue` protected for roles `moderator|admin`
- `/admin` protected for role `admin`
- `/forbidden` role-guard fallback page for authenticated but unauthorized users

Unknown routes are handled via wildcard fallback (`*`).

`ProtectedRouteLayout` redirects unauthenticated users to `/login?redirect=<target>` and authenticated users lacking a required role (insufficient permissions) to `/forbidden`.

## HTTP Client & Queries

- **Axios**: Centralized HTTP client with request interceptors, automatic refresh token flow on 401, and retry handling
- **Auth State**: React Context (`features/auth/AuthContext.tsx`) manages login/logout/session bootstrap
- **React Query**: TanStack Query v5 with custom `useUserProfile` hook (sample implementation)
- See `src/shared/api/README.md` for HTTP client and API integration details

## Notes

- TypeScript strict mode is enabled in `tsconfig.app.json`.
- ESLint and Prettier are configured for consistent code style across the team.
- All npm scripts are designed to run on Windows PowerShell and Unix-like shells.
- This workspace is intentionally modular and ready for feature-specific follow-up issues.

