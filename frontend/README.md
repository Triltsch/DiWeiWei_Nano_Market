# Frontend Workspace (S2-FE-03)

React 18 + Vite + TypeScript (strict mode) baseline for Nano Market frontend development.

## Commands

```bash
npm install
npm run dev
npm run build
npm run typecheck
```

## Structure

- `src/app` - app entry and global styles
- `src/features` - feature modules
- `src/shared` - shared UI/components/utilities

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

## Notes

- TypeScript strict mode is enabled in `tsconfig.app.json`.
- This workspace is intentionally minimal and ready for follow-up issues (Axios, React Query, auth guards).
