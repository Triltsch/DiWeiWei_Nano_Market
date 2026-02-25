# 07 — Moduldesign

---

## 1. Modulübersicht

Der Nano-Marktplatz wird als **Modular Monolith** architekturiert. Dies ermöglicht:
- Klare Verantwortlichkeiten
- Einfache Unit Testing
- Später einfache Migration zu Microservices

### Module-Abhängigkeiten

```
┌─────────────────────────────────────────────────────────┐
│ API Gateway (HTTP/REST Routing)                         │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ Core Modules (Independent, reusable)                    │
- Identity & Auth (User registration, JWT)               │
├─ Nano Catalog (CRUD Nanos)                              │
├─ Search & Discovery (Full-text search)                  │
└─────────────────────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ Feature Modules (Depend on Core)                         │
├─ Feedback System (Ratings, Comments)                    │
├─ Messaging / Chat                                        │
├─ Favorites & Lists                                       │
├─ Profiles & Organizations                               │
└─────────────────────────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ Admin & Compliance Modules                               │
├─ Moderation & Abuse Prevention                          │
├─ DSGVO & Audit Logging                                   │
├─ Analytics & Reporting                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Module Details

### Module 1: Identity & Auth

**Verantwortlichkeiten:**
- Benutzerregistrierung
- Authentifizierung (Login/Logout)
- JWT Token Verwaltung
- Password Hashing
- 2FA (Phase 1)
- Role Management

**APIs:**
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh-token
POST   /api/v1/auth/change-password
POST   /api/v1/auth/2fa/setup  (Phase 1)
POST   /api/v1/auth/2fa/verify (Phase 1)
```

**Daten:**
```sql
Tables:
- users (id, email, username, password_hash, role, status)
- user_2fa_secrets (user_id, secret, backup_codes) -- Phase 1
- refresh_tokens (token, user_id, expires_at, created_at)
```

**Externe Abhängigkeiten:** JWT Library, bcrypt, Redis (Sessions)

**Tests:**
- [ ] Registration Validation (email unique, pw strength)
- [ ] Login Success/Failure
- [ ] JWT Token Expiry
- [ ] Password Reset Flow
- [ ] 2FA Setup/Verification (Phase 1)

---

### Module 2: Nano Catalog

**Verantwortlichkeiten:**
- Nano Upload / Create
- Nano Version Management
- Nano Metadata Validation
- Nano Status Workflow (draft → published)
- Nano Deletion / Archival

**APIs:**
```
GET    /api/v1/nanos
GET    /api/v1/nanos/{id}
POST   /api/v1/nanos (multipart: file + metadata)
PATCH  /api/v1/nanos/{id}
DELETE /api/v1/nanos/{id} (soft-delete)
GET    /api/v1/nanos/{id}/versions (Phase 1)
```

**Daten:**
```sql
Tables:
- nanos (id, creator_id, title, description, duration_minutes, 
         competency_level, status, published_at, file_storage_path, ...)
- nano_versions (nano_id, version, changelog, file_storage_path)
- nano_categories (nano_id, category_id)
```

**Externe Abhängigkeiten:**
- Identity Module (Creator Validation)
- Search Module (Index nach Upload)
- Object Storage Client (MinIO/S3-compatible)
- Moderation Module (Status Workflow)

**Workflows:**
```
1. Creator Upload ZIP:
   a. Validate: File size, format
   b. Store to object storage
   c. Extract Metadata
   d. Create Nano record (Status: draft)
   e. Trigger Moderation review (Status: pending_review)

2. Moderator Approves:
   a. Trigger Moderation Module → status = published
   b. Publish to Search Index

3. Creator Updates Nano:
   a. Create new Nano_Version record
   b. Update file in object storage
   c. Status back to pending_review
```

---

### Module 3: Search & Discovery

**Verantwortlichkeiten:**
- Full-Text Search
- Faceted Filtering
- Result Ranking
- Search Analytics

**APIs:**
```
GET /api/v1/search?q=excel&category=business&level=1&limit=20&page=1
GET /api/v1/search/suggestions?q=ex (autocomplete, Phase 1)
GET /api/v1/search/trending (Phase 1)
```

**Daten:**
```
Elasticsearch Index: nanos_v1
  - Fields: title, description, categories, created_at, 
           average_rating, download_count
  - Analyzer: German stemming
```

**Externe Abhängigkeiten:**
- Nano Catalog Module (Indexing trigger)
- Elasticsearch Client

**Operations:**
```
Indexing Strategy:
- Async: After Nano.publish, index to ES
- Refresh Interval: 1s
- Retention: Match DB (soft-delete synced)
```

---

### Module 4: Feedback System

**Verantwortlichkeiten:**
- Rating submission (1-5 stars)
- Comments / Reviews
- Moderation of comments
- Comment Notifications

**APIs:**
```
GET    /api/v1/nanos/{id}/ratings
POST   /api/v1/nanos/{id}/ratings
PATCH  /api/v1/ratings/{rating_id}
DELETE /api/v1/ratings/{rating_id}
GET    /api/v1/nanos/{id}/comments
POST   /api/v1/nanos/{id}/comments
```

**Daten:**
```sql
Tables:
- ratings (id, nano_id, rater_id, score, comment, created_at)
- rating_moderation (rating_id, status, reviewed_by, reviewed_at)
```

**Externe Abhängigkeiten:**
- Identity Module (Rater Validation)
- Notification Module (Optional, Phase 1)
- Moderation Module (Comment Review)

---

### Module 5: Messaging / Chat

**Verantwortlichkeiten:**
- Chat Session Management
- Message Storage & Retrieval
- Real-time Notifications (Phase 1)
- Message Encryption (Phase 2)

**APIs:**
```
POST   /api/v1/chats (create session)
GET    /api/v1/chats
GET    /api/v1/chats/{session_id}/messages?since=timestamp&limit=50
POST   /api/v1/chats/{session_id}/messages
WS     /api/v1/ws/chat/{session_id} (WebSocket, Phase 1)
```

**Daten:**
```sql
Tables:
- chat_sessions (id, nano_id, initiator_id, creator_id, created_at)
- chat_messages (id, session_id, from_user_id, text, created_at, read_at)
```

**Externe Abhängigkeiten:**
- Identity Module
- Nano Catalog (Session validation)
- Message Queue (for Phase 1 real-time)

---

### Module 6: Profiles & Organizations

**Verantwortlichkeiten:**
- User Profile Management
- Organization Creation / Management (Phase 1)
- Organization Roles (Phase 1)

**APIs:**
```
GET    /api/v1/users/{id}/profile
PATCH  /api/v1/users/{id}/profile
GET    /api/v1/organizations
POST   /api/v1/organizations (Phase 1)
PATCH  /api/v1/organizations/{id} (Phase 1)
PATCH  /api/v1/organizations/{id}/members (Phase 1)
```

**Daten:**
```sql
Tables:
- user_profiles (user_id, bio, avatar_url, ...)
- organizations (id, name, description, ...)
- organization_members (org_id, user_id, role, joined_at)
```

---

### Module 7: Favorites & Lists

**Verantwortlichkeiten:**
- Marking Nanos as Favorite
- Creating Curated Lists (Phase 1)
- List Sharing (Phase 1)

**APIs:**
```
POST   /api/v1/favorites/{nano_id}
DELETE /api/v1/favorites/{nano_id}
GET    /api/v1/users/{id}/favorites
POST   /api/v1/lists (Phase 1)
PATCH  /api/v1/lists/{id} (Phase 1)
```

**Daten:**
```sql
Tables:
- favorites (id, user_id, nano_id, created_at)
- saved_lists (id, user_id, name, is_public)
- saved_list_items (list_id, nano_id, rank)
```

---

### Module 8: Moderation & Abuse Prevention

**Verantwortlichkeiten:**
- Content Review Queue
- Flagging System
- User Warnings
- Content Takedown

**APIs:**
```
GET    /api/v1/admin/moderation/queue
POST   /api/v1/admin/moderation/{nano_id}/decision
GET    /api/v1/flags
POST   /api/v1/flags (user reports content)
POST   /api/v1/admin/users/{id}/suspend
```

**Daten:**
```sql
Tables:
- moderation_flags (id, content_type, content_id, reason, status)
- user_suspensions (id, user_id, reason, expires_at)
```

**Externe Abhängigkeiten:**
- Identity Module
- All Content Modules (Nanos, Comments, Chat)
- Audit Module (Logging)

---

### Module 9: Audit & DSGVO

**Verantwortlichkeiten:**
- Audit Log Generation
- DSGVO Request Handling
- Data Export
- User Anonymization
- Data Retention Policies

**APIs:**
```
GET    /api/v1/admin/audit-logs
POST   /api/v1/dsgvo/data-export (User)
POST   /api/v1/dsgvo/account-delete (User)
POST   /api/v1/admin/dsgvo/requests (Admin)
```

**Daten:**
```sql
Tables:
- audit_logs (id, action, actor_id, target_id, timestamp, details)
- dsgvo_requests (id, user_id, request_type, status, created_at)
```

**Batch Jobs:**
```
Retention Policy:
- Every night (2 AM UTC):
  - DELETE FROM audit_logs WHERE created_at < NOW() - 7 YEARS
  - ANONYMIZE inactive user accounts (12M+)
```

---

### Module 10: Analytics & Reporting

**Verantwortlichkeiten:**
- User Analytics
- Content Analytics
- Engagement Metrics
- Reporting Dashboards

**APIs:**
```
GET /api/v1/admin/analytics/dashboard
GET /api/v1/creators/{id}/analytics/nanos
GET /api/v1/analytics/trending
(All read-only, cacheable)
```

**Data Sources:**
- Database queries (aggregation)
- Prometheus/Grafana Metrics
- Custom event logs

---

## 3. Modular Code Structure (Example: Nano Catalog)

```python
# app/modules/nano_catalog/
├── __init__.py
├── router.py              # FastAPI router
├── schemas.py             # Pydantic models (request/response)
├── models.py              # SQLAlchemy ORM models
├── service.py             # Business logic
├── repository.py          # Data access
├── dependencies.py        # DI (injected services)
├── events.py              # Domain events
└── tests/
    ├── test_router.py
    ├── test_service.py
    └── fixtures.py

# Usage in main app
from app.modules.nano_catalog import router as nano_router
app.include_router(nano_router, prefix="/api/v1")
```

---

## 4. Inter-Module Communication

```python
# Example: Nano Upload Workflow

# 1. API Router (Entry point)
@router.post("/nanos")
async def create_nano(
    file: UploadFile,
    metadata: NanoMetadata,
    current_user = Depends(get_current_user)  # From Identity Module
):
    # 2. Service (business logic)
    nano = await nano_service.create_nano(
        creator_id=current_user.id,
        file=file,
        metadata=metadata
    )
    
    # 3. Trigger external module events
    await search_service.index_nano(nano)  # Search Module
    await moderation_service.queue_review(nano)  # Moderation Module
    
    return nano

# Dependency Injection (loose coupling)
# services_container.register(NanoService, SearchService, ModerationService)
```

---

## 5. Migration Path: Monolith → Microservices

| Phase | Module | Deployment |
|-------|--------|-----------|
| MVP | All | Single Process |
| Phase 1 | Auth | Separate Service (Keycloak) |
| Phase 1 | Chat | Separate Service (Node.js) |
| Phase 2 | Nano Catalog | Separate Service (Java) |
| Phase 2 | Search | Separate Service (ES only) |

**Database Per Service (Future):**
```
Auth Service → PostgreSQL
Nano Service → MongoDB (flexible schema)
Chat Service → TimescaleDB (time-series optimized)
```

---

## 6. Open Questions & Decisions

1. **Notification Module:** Separate module or integrated?
   - Decision (MVP): Inline in services, Phase 1 → separate
   
2. **Analytics Module:** Real-time or batch?
   - Decision (MVP): Batch (nightly), Phase 1 → Real-time via Message Queue

3. **Organization Multi-Tenancy:** How to enforce isolation?
   - Decision: Row-level security (RLS) in PostgreSQL

---

## Referenzen

- [05 — Systemarchitektur](./05_system_architecture.md) (Deployment)
- [08 — Backlog & Roadmap](./08_backlog_roadmap.md) (User Stories per Module)
