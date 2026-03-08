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
npm test -- --run  # Run tests once and exit
```

## Development Proxy

The Vite dev server (`npm run dev`) includes a dev proxy that forwards API requests to the backend:

- Dev server runs on `http://localhost:5173`
- Proxy forwards `/api/*` requests to `http://localhost:8000` (configurable via `VITE_API_BASE_URL`)
- Backend must be running on port 8000 for API calls to work

### Example
```bash
# Terminal 1: Start backend (should run on :8000)
cd ..
python -m uvicorn app.main:app --reload

# Terminal 2: Start frontend dev server
cd frontend
npm run dev
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

## Docker Deployment

Frontend is included in the Docker Compose stack:

```bash
docker compose up frontend  # Builds and serves static assets on :3000
```

The `Dockerfile.frontend` uses multi-stage build:
1. Build stage: Node.js 20 Alpine - runs TypeScript check and Vite build
2. Serve stage: Nginx Alpine - serves `/dist` content with SPA routing

## Structure

- `src/app` - app entry and global styles
- `src/features` - feature modules
- `src/shared` - shared UI/components/utilities including HTTP client and React Query setup

## Routing Baseline

React Router v6 skeleton is wired in `src/app/router.tsx` with placeholder pages for:

- `/`
- `/search`
- `/nano/:id`
- `/login`
- `/register`
- `/dashboard`
- `/profile`
- `/admin`

Unknown routes are handled via wildcard fallback (`*`).

Protected-route structure is scaffolded through `ProtectedRouteLayout` so Sprint 3 can
add auth guards without reorganizing route definitions.

## HTTP Client & Queries

- **Axios**: Centralized HTTP client with request/response interceptors for token injection and error handling
- **React Query**: TanStack Query v5 with custom `useUserProfile` hook (sample implementation)
- See `src/shared/api/README.md` for HTTP client and API integration details

## Notes

- TypeScript strict mode is enabled in `tsconfig.app.json`.
- ESLint and Prettier are configured for consistent code style across the team.
- All npm scripts are designed to run on Windows PowerShell and Unix-like shells.
- This workspace is intentionally modular and ready for feature-specific follow-up issues.

