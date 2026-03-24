# 08 — Backlog & Roadmap

---

## 1. Product Backlog (MVP-Fokus)

### High-Level Epics für MVP (Q3 2025)

> **Tech Stack Note:** The MVP uses a vendor-neutral, open-source stack as defined in `05_system_architecture.md`.
> Backend: FastAPI + PostgreSQL + Redis (self-hosted) + MinIO + Prometheus/Grafana
> Frontend: React 18 + Vite + Tailwind CSS
> Deployment: Docker Compose (no cloud vendor lock-in)

```
EPIC 1: Foundation & Security (2 Wochen)
├─ Story 1.1: User Registration & Login
├─ Story 1.2: JWT Token Management
├─ Story 1.3: Password Hashing Implementation
├─ Story 1.4: DSGVO Compliance Basics
└─ Story 1.5: Audit Logging Framework

EPIC 2: Core Nano Management (3 Wochen)
├─ Story 2.1: Nano Upload with ZIP Validation
├─ Story 2.2: Nano Metadata Capture & Storage
├─ Story 2.3: Nano Versioning System
├─ Story 2.4: Status Workflow (draft→published)
└─ Story 2.5: Nano Detail View & Display

EPIC 3: Discovery & Search (2 Wochen)
├─ Story 3.1: Full-Text Search Implementation (Meilisearch)
├─ Story 3.2: Faceted Filtering (Category, Level, Duration)
├─ Story 3.3: Search Result Ranking
├─ Story 3.4: Pagination & Performance
└─ Story 3.5: Search UI / Frontend

EPIC 4: Feedback System (1 Woche)
├─ Story 4.1: Star Rating (1-5)
├─ Story 4.2: Comments / Reviews
├─ Story 4.3: Average Rating Display
└─ Story 4.4: Rating Moderation

EPIC 5: Communication (1 Woche)
├─ Story 5.1: Chat Session Creation
├─ Story 5.2: Chat Message Persistence
├─ Story 5.3: Chat UI with Polling
├─ Story 5.4: Message Encryption (TLS)
└─ Story 5.5: Spam Prevention

EPIC 6: Moderation & Trust (1 Woche)
├─ Story 6.1: Moderation Queue Interface
├─ Story 6.2: Content Review Workflow
├─ Story 6.3: Flag System (User Reporting)
└─ Story 6.4: Admin Takedown Functions

EPIC 7: DevOps & Infrastructure (Parallel, 2 Wochen)
├─ Story 7.1: Docker Compose Environment Setup
├─ Story 7.2: PostgreSQL Setup & Schema Migrations
├─ Story 7.3: MinIO Object Storage Setup
├─ Story 7.4: Redis Cache Setup (Self-Hosted)
├─ Story 7.5: Prometheus/Grafana Monitoring
├─ Story 7.6: CI/CD Pipeline (GitHub Actions)
└─ Story 7.7: SSL/TLS & Security Hardening (Caddy/Nginx)

EPIC 8: Frontend & Web Application (3 Wochen, parallel ab Sprint 2)
├─ Story 8.1: Frontend Project Setup (React 18 + Vite + Tailwind CSS)
├─ Story 8.2: Landing Page & Global Navigation
├─ Story 8.3: Auth Pages (Register, Login, Email Verification)
├─ Story 8.4: Nano Discovery Page & Search UI
├─ Story 8.5: Nano Detail Page (incl. ratings & chat CTA)
├─ Story 8.6: Creator Dashboard (upload, manage Nanos)
├─ Story 8.7: User Profile & Account Settings
└─ Story 8.8: Admin Panel UI

TOTAL: ~10 Wochen (2.5 Monate) für MVP (inkl. Frontend)
```

---

## 2. User Stories mit Akzeptanzkriterien

### Story 1.1: User Registration & Login

```gherkin
Feature: User Registration & Authentication

Scenario: New User Registration
  Given: User lands on signuppage
  When: User enters email, password, username
  And:  User clicks "Register"
  Then: Account is created in DB
  And:  E-Mail-Verification-Link sent
  And:  User redirected to "Check E-Mail" page

  Acceptance Criteria:
  ✓ Email must be unique (case-insensitive)
  ✓ Username must be 3-20 chars, alphanumeric + underscore
  ✓ Password must be ≥8 chars (1 Upper, 1 Digit, 1 Special)
  ✓ Verification token expires after 24h
  ✓ User can resend verification link
  ✓ After verification, user can login

Scenario: Existing User Login
  Given: User has verified account
  When: User enters email + password
  And:  User clicks "Login"
  Then: User is authenticated
  And:  JWT access_token issued (15 min expiry)
  And:  Refresh token issued (7 day expiry)
  And:  User redirected to dashboard

  Acceptance Criteria:
  ✓ Invalid password → 3 attempts → Account locked (1h)
  ✓ Successful login → Account last_login updated
  ✓ Session timeout after 30 min inactivity
  ✓ Logout deletes refresh_token
```

**Effort Estimate:** 8 Personentage  
**Dependencies:** Auth Module setup  
**Done Criteria:**
- [ ] Unit tests ≥ 90% coverage
- [ ] Integration tests passing
- [ ] Swagger/OpenAPI docs updated
- [ ] Security audit passed (no hardcoded secrets)

---

### Story 2.1: Nano Upload with ZIP Validation

```gherkin
Feature: Nano Upload

Scenario: Creator Uploads Nano
  Given: Creator logged in as "creator" role
  When: Creator selects ZIP file (max 100 MB)
  And:  File is validated (format, structure)
  And:  ZIP extracted to temporary storage
  And:  File uploaded to S3
  Then: Nano record created with Status = "draft"
  And:  Creator redirected to Metadata Entry form

  Acceptance Criteria:
  ✓ Supported formats: ZIP only
  ✓ Max size: 100 MB
  ✓ ZIP contains: At least 1 file (PDF, video, etc.)
  ✓ Duplicate uploads: Allowed (new Nano)
  ✓ UploadProgress shown (0-100%)
  ✓ Upload timeout after 10 min
  ✓ Failed uploads → retry available
  ✓ MinIO ACL: Private (only authenticated users via pre-signed URLs)
```

**Effort Estimate:** 10 Personentage  
**Done Criteria:**
- [ ] Upload handler tests passing
- [ ] S3 integration tests (mock + real)
- [ ] ZIP validation edge cases covered
- [ ] Error messages user-friendly

---

### Story 3.1: Full-Text Search

```gherkin
Feature: Search published Nanos

Scenario: User searches for Nanos
  Given: At least 10 published Nanos in system
  When: User enters search term "Excel"
  And:  User optional filters by: Category, Level, Duration
  And:  User clicks "Search"
  Then: Results displayed (max 20 per page)
  And:  Results ranked by relevance
  And:  Each result shows: Title, Duration, Avg Rating, Creator

  Acceptance Criteria:
  ✓ Search case-insensitive
  ✓ Partial matches: "Exce" matches "Excel"
  ✓ Filter combinations work (e.g., Category AND Duration)
  ✓ Results cached (Redis) for 30 min
  ✓ Performance: <500ms for typical queries
  ✓ Pagination: "Load More" or page numbers
  ✓ No results → "No nanos found. Try different search."
```

**Effort Estimate:** 12 Personentage  
**Dependencies:** Meilisearch setup, Nano indexing pipeline  
**Done Criteria:**
- [ ] Meilisearch service and index operational
- [ ] Search query tests ≥85% coverage
- [ ] Performance benchmarks baseline

---

### Story 4.1: Star Rating System

```gherkin
Feature: Rate a Nano

Scenario: Consumer rates Nano
  Given: Consumer authenticated
  When: Consumer opens published Nano
  And:  Consumer clicks 1-5 star button
  Then: Rating recorded in database
  And:  Average rating recalculated
  And:  UI updates immediately (stars highlight)

  Acceptance Criteria:
  ✓ One rating per user per Nano (max)
  ✓ Ratings only for published Nanos
  ✓ Rating displayed: "4.2 ★ (230 votes)"
  ✓ Creator sees all ratings in dashboard
  ✓ Ratings aggregated (avg, median, distribution)
```

**Effort Estimate:** 5 Personentage  
**Done Criteria:**
- [ ] Database schema correct
- [ ] Rating aggregation queries optimized

---

### Story 5.1: Chat Session Creation

```gherkin
Feature: Send Message to Nano Creator

Scenario: Consumer initiates Chat
  Given: Consumer viewing published Nano
  When: Consumer clicks "Message Creator"
  And:  Chat modal opens
  Then: Chat session created (if new)
  And:  Creator notified (Email optional)
  And:  Consumer can type message
  And:  Creator can reply (if online/later)

  Acceptance Criteria:
  ✓ Same nano → Reuse existing chat session
  ✓ Different nano → New session
  ✓ TLS encryption in transit
  ✓ Messages max 1000 chars
  ✓ Emoji support
  ✓ Links auto-linkified
```

**Effort Estimate:** 8 Personentage  
**Done Criteria:**
- [ ] Chat table schema correct
- [ ] Session management robust

---

### Story 8.1: Frontend Project Setup

**Tech Stack:** React 18 + Vite + Tailwind CSS + React Query + Axios + React Router v6

```
Acceptance Criteria:
✓ Vite project bootstrapped with TypeScript
✓ Tailwind CSS configured with design tokens (colors, fonts)
✓ React Router configured with routes: /, /search, /nano/:id, /login, /register,
    /dashboard, /profile, /admin
✓ Axios API client configured (base URL from .env, JWT header injection)
✓ React Query set up for server-state management
✓ ESLint + Prettier configured
✓ Proxy config for local dev → FastAPI backend on :8000
✓ Docker Compose service added for frontend (nginx static serve)
```

**Effort Estimate:** 3 Personentage  
**Done Criteria:**
- [ ] `npm run dev` works locally against backend
- [ ] `npm run build` produces deployable static bundle
- [ ] Linting & formatting checks pass

---

### Story 8.2: Landing Page & Global Navigation

```gherkin
Feature: Public Landing Page

Scenario: Visitor opens the website
  Given: User is not logged in
  When:  User navigates to /
  Then:  Landing page shows value proposition
  And:   Navigation shows: Logo, Search, Login, Register
  And:   CTA buttons link to /register and /search
  And:   Page renders in <2s (Lighthouse ≥85)

  Acceptance Criteria:
  ✓ Responsive (mobile, tablet, desktop)
  ✓ Navigation collapses to hamburger on mobile
  ✓ Authenticated users see: Dashboard, Profile, Logout in nav
  ✓ Language: German (de) default
```

**Effort Estimate:** 4 Personentage

---

### Story 8.3: Auth Pages

```gherkin
Feature: Register, Login, Email Verification flows

Scenario: Registration Form
  Given:  Visitor on /register
  When:   Visitor fills in email, username, password
  And:    Visitor accepts terms + privacy
  Then:   POST /api/v1/auth/register called
  And:    Success → redirect to "Check your email" page
  And:    Error → inline validation messages shown

Scenario: Login Form
  Given:  Visitor on /login
  When:   Visitor submits valid credentials
  Then:   Tokens stored (access: memory, refresh: httpOnly cookie)
  And:    Redirect to /dashboard

  Acceptance Criteria:
  ✓ Password strength indicator shown during registration
  ✓ Account locked state shows remaining lockout time
  ✓ "Resend verification email" link on verification-pending page
  ✓ Forgot password link (Phase 1 — placeholder for MVP)
  ✓ Protected routes redirect to /login if unauthenticated
```

**Effort Estimate:** 6 Personentage  
**Done Criteria:**
- [ ] Full auth flow works end-to-end (register → verify → login → logout)
- [ ] Token refresh handled transparently by Axios interceptor

---

### Story 8.4: Nano Discovery Page & Search UI

```gherkin
Feature: Browse and Search Nanos

Scenario: User browses Nanos
  Given:  User on /search
  Then:   Published Nanos shown (paginated, 20/page)
  And:    Filter sidebar: Category, Level, Duration, Language

Scenario: User enters search term
  When:   User types in search box
  Then:   Results update (debounced, 300ms)
  And:    Each result shows: Title, Creator, Avg Rating, Duration

  Acceptance Criteria:
  ✓ Empty state: "No Nanos found. Try different keywords."
  ✓ Loading skeleton shown during fetch
  ✓ URL reflects search term + active filters (shareable link)
  ✓ Pagination: page numbers or "Load more"
```

**Effort Estimate:** 6 Personentage

---

### Story 8.5–8.8: Nano Detail, Creator Dashboard, User Profile, Admin Panel

```
Story 8.5: Nano Detail Page
- Full Nano information, file preview/download CTA
- Star rating widget, comment list
- "Message Creator" button → opens chat modal
- Acceptance: Authenticated download only; unauthenticated → /login

Story 8.6: Creator Dashboard
- List of creator's own Nanos with status badges
- Upload wizard (ZIP select → metadata form → submit)
- Edit/delete draft Nanos
- Acceptance: Accessible to `creator`, `moderator`, `admin` (role-based route guards); `consumer` denied

Story 8.7: User Profile & Account Settings
- Display username, bio, language preference
- Change password form
- GDPR: Export my data / Request account deletion buttons
- Acceptance: All DSGVO endpoints wired up

Story 8.8: Admin Panel UI
- User list with role management
- Audit log viewer (paginated)
- Moderation queue for flagged Nanos
- Acceptance: Only accessible to 'admin' role (401/403 otherwise)
```

### Rollen-Policy (verbindlich, MVP)

- Primäre aktive Rollen: `creator`, `moderator`, `admin`
- `consumer` bleibt als niedrigste Legacy-/Read-Rolle erhalten, erhält aber keinen Zugriff auf Creator-, Moderation- oder Admin-Bereiche
- Default-Rolle bei Registrierung: `creator`
- Frontend-Navigation und Route-Guards müssen dieselbe Rollenmatrix wie Backend-RBAC verwenden
- 401 = nicht authentifiziert, 403 = authentifiziert aber fehlende Berechtigung

**Effort Estimate:** 16 Personentage (combined)

---

## 3. Sprint Planning (MVP: 10 Sprints à 1 Woche)

> **Two parallel tracks from Sprint 2 onwards:**
> - **Backend Track:** API, business logic, database, infrastructure
> - **Frontend Track:** React application (can be developed alongside backend by second developer or sequentially)

```
Sprint 1 (Week 1): Foundation
├─ Story 1.1: Auth & Login (Backend)
├─ Story 1.3: Password Hashing (Backend)
├─ Story 1.4: DSGVO Basics (Backend)
└─ Story 7.1: Docker Compose Environment Setup
Goal: Secure API baseline + local dev environment running

Sprint 2 (Week 2): Nano Upload & Storage + Frontend Bootstrap
├─ Story 2.1: Nano Upload (Backend)
├─ Story 7.2: PostgreSQL Setup & Migrations
├─ Story 7.3: MinIO Object Storage Setup
└─ Story 8.1: Frontend Project Setup (React + Vite + Tailwind)
Goal: Can upload Nanos to MinIO; frontend scaffold ready

Sprint 3 (Week 3): Metadata, Status & Auth Frontend
├─ Story 2.2: Nano Metadata Capture (Backend)
├─ Story 2.4: Status Workflow (Backend)
├─ Story 8.2: Landing Page & Global Navigation (Frontend)
└─ Story 8.3: Auth Pages (Register, Login, Email Verification) (Frontend)
Goal: Full Nano management backend; working auth UI

Sprint 4 (Week 4): Search Infrastructure & Discovery UI
├─ Story 3.1: Full-Text Search (Meilisearch) (Backend)
├─ Story 7.4: Redis Cache Setup
├─ Story 8.4: Nano Discovery Page & Search UI (Frontend)
└─ Story 3.5: Search UI integration with backend API
Goal: Search operational end-to-end

Sprint 5 (Week 5): Monitoring, Nano Detail & Creator Dashboard
├─ Story 7.5: Prometheus/Grafana Monitoring
├─ Story 2.5: Nano Detail View (Backend)
├─ Story 8.5: Nano Detail Page (Frontend)
├─ Story 8.6: Creator Dashboard (upload, manage Nanos) (Frontend)
└─ QA/Operations Gate: Detail + Dashboard + Monitoring Abnahme (Issue #74)
Goal: Creators can publish Nanos; monitoring live

Sprint 6 (Week 6): Feedback System
├─ Story 4.1: Star Rating (Backend)
├─ Story 4.2: Comments / Reviews (Backend)
├─ Story 4.4: Rating Moderation (Backend)
└─ Rating UI integrated into Nano Detail Page (Frontend)
Goal: Users can provide feedback end-to-end

Sprint 7 (Week 7): Communication
├─ Story 5.1: Chat Sessions (Backend)
├─ Story 5.2: Messages (Backend)
├─ Story 5.4: Encryption TLS (Backend)
└─ Story 5.3: Chat UI with Polling (Frontend)
Goal: Direct messaging works end-to-end

Sprint 8 (Week 8): User Profile, Moderation & Admin UI
├─ Story 8.7: User Profile & Account Settings (Frontend)
├─ Story 6.2: Content Review Workflow (Backend)
├─ Story 6.4: Admin Takedown Functions (Backend)
└─ Story 8.8: Admin Panel UI (Frontend)
Goal: Full admin + user profile functionality

Sprint 9 (Week 9): Security Hardening & CI/CD
├─ Story 7.6: CI/CD Pipeline (GitHub Actions)
├─ Story 7.7: SSL/TLS & Security Hardening (Caddy/Nginx)
├─ Story 6.3: Flag System (User Reporting)
└─ Story 5.5: Spam Prevention
Goal: Production-safe deployment pipeline

Sprint 10 (Week 10): Testing, QA & Go-Live
├─ Integration tests (full stack)
├─ Security audit
├─ Load testing & performance tuning
├─ Go-Live prep & documentation
└─ Story 8.2 polish (landing page final)
Goal: Production-ready

TOTAL: 10 Sprints = 2.5 Monate MVP (inkl. Frontend)
```

---

## 4. Priorisierung (WSJF)

```
Formula: Priority = (Value + TimeSensitivity + RiskReduction + Size) / JobSize

Critical Path (MVP Blockers):
1. Auth (Priority: 100) - Blocks all else
2. Nano Upload (95) - Core value prop
3. Search (85) - Discovery
4. Moderation (80) - Trust/Compliance
5. Chat (75) - Engagement

Nice-to-Have (MVP):
- Analytics Dashboard (30) - Can track manual
- 2FA (25) - MVP login is simple
- Favorites (40) - Can add in Phase 1
```

---

## 5. Phase 1 Roadmap (Q4 2025 - Q1 2026)

| Feature | Effort | Timeline | Value |
|---------|--------|----------|-------|
| WebSocket Chat (Real-time) | 15 PT | Q4 | High |
| Organization Multi-Tenancy | 20 PT | Q4-Q1 | High |
| AI Content Filter | 25 PT | Q4 | Medium |
| Nano Analytics for Creators | 10 PT | Q4 | High |
| SSO (Azure AD) | 15 PT | Q1 | Medium |
| Saved Lists | 8 PT | Q4 | Low |
| Payment Integration (Stripe) | 20 PT | Q1 | Medium |
| SCORM Export | 15 PT | Q1 | Medium |

---

## 6. Release Plan

```
MVP: v1.0.0 (Week 8, Q3 2025)
├─ Core features working
├─ Security audit passed
└─ Docs completed

v1.1.0 (2 weeks Post-launch)
├─ Bug fixes from users
├─ Search optimizations
└─ Chat improvements

Phase 1: v2.0.0 (Q4 2025)
├─ WebSocket Chat
├─ Organizations
└─ Analytics

Phase 2: v3.0.0 (H1 2026)
├─ Payment system
├─ API for Integrations
└─ Mobile app
```

---

## 7. Definition of Done

**For all User Stories:**
- [ ] Code written & reviewed
- [ ] Unit tests ≥80% coverage
- [ ] Integration tests passing
- [ ] Swagger/API docs updated
- [ ] Security checklist complete
- [ ] Performance verified (<500ms p95)
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] QA sign-off
- [ ] Product Owner approval

---

## Referenzen

- [01 — Stakeholder & Rollen](./01_stakeholder_roles.md)
- [02 — Fachliche Anforderungen](./02_requirements.md) (Anforderungen→Stories)
- [03 — User Journeys](./03_user_journeys.md) (Inspiration für Stories)
