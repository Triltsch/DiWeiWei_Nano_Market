# 08 — Backlog & Roadmap

---

## 1. Product Backlog (MVP-Fokus)

### High-Level Epics für MVP (Q3 2025)

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
├─ Story 3.1: Full-Text Search Implementation
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
├─ Story 7.1: AWS Environment Setup
├─ Story 7.2: RDS Aurora MySQL Config
├─ Story 7.3: S3 Upload Pipeline
├─ Story 7.4: ElastiCache Setup
├─ Story 7.5: CloudWatch Monitoring
├─ Story 7.6: CI/CD Pipeline (GitHub Actions)
└─ Story 7.7: SSL/TLS & Security Hardening

TOTAL: ~8 Wochen (2 Monate) für MVP
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
  ✓ S3 ACL: Private (only authenticated users)
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
**Dependencies:** Elasticsearch setup, Nano indexing pipeline  
**Done Criteria:**
- [ ] Elasticsearch cluster operational
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

## 3. Sprint Planning (MVP: 8 Sprints à 1 Woche)

```
Sprint 1 (Week 1): Foundation
├─ Story 1.1: Auth & Login
├─ Story 1.3: Password Hashing
└─ Story 1.4: DSGVO Basics
Goal: Secure API baseline

Sprint 2 (Week 2): Nano Upload
├─ Story 2.1: Nano Upload
├─ Story 7.1: AWS Setup
└─ Story 7.3: S3 Pipeline
Goal: Can upload Nanos to cloud

Sprint 3 (Week 3): Metadata & Status
├─ Story 2.2: Nano Metadata Capture
├─ Story 2.4: Status Workflow
└─ Story 6.2: Moderation Queue
Goal: Full Nano Management cycle

Sprint 4 (Week 4): Search Infrastructure
├─ Story 3.1: Full-Text Search
├─ Story 7.4: ElastiCache
└─ Story 7.5: CloudWatch
Goal: Search operational

Sprint 5 (Week 5): Feedback
├─ Story 4.1: Star Rating
├─ Story 4.2: Comments
└─ Story 4.4: Rating Moderation
Goal: Users can provide feedback

Sprint 6 (Week 6): Communication
├─ Story 5.1: Chat Sessions
├─ Story 5.2: Messages
└─ Story 5.4: Encryption (TLS)
Goal: Direct messaging works

Sprint 7 (Week 7): Frontend & UX
├─ Story 3.5: Search UI
├─ Story 5.3: Chat UI
├─ Story 2.5: Nano Detail View
└─ Story 6.4: Admin UI
Goal: All UIs integrated

Sprint 8 (Week 8): Testing & Hardening
├─ Integration tests
├─ Security audit
├─ Load testing
├─ Go-Live prep
└─ Documentation
Goal: Production-ready

TOTAL: 8 Sprints = 2 Monate MVP
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
- [ ] Performance verified (<100ms p95)
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] QA sign-off
- [ ] Product Owner approval

---

## Referenzen

- [01 — Stakeholder & Rollen](./01_stakeholder_roles.md)
- [02 — Fachliche Anforderungen](./02_requirements.md) (Anforderungen→Stories)
- [03 — User Journeys](./03_user_journeys.md) (Inspiration für Stories)
