# 05 — Systemarchitektur

---

## 1. Architektur-Übersicht

### 1.1 Die Wahl: Modular Monolith + Cloud-Native

Nach Analyse des Prototyps und der Anforderungen wird folgende Architektur empfohlen:

**Architektur-Modell:** **Modular Monolith** (MVP) → **Microservices** (Phase 2+)

**Begründung:**
- MVP braucht schnelle Entwicklung (Monolith ist schneller)
- Klar abgegrenzte Module ermöglichen später einfache Migration zu Services
- Single Deployment Unit für MVP
- Cost-efficient auf AWS (ein ALB, ein RDS Cluster)

### 1.2 Deployment-Modell: Cloud-Native (AWS)

```
┌───────────────────────────────────────────────────────────┐
│                    INTERNET / CDN                         │
├───────────────────────────────────────────────────────────┤
│                  CloudFront (CDN)                         │
│            (Static Assets, Nano-ZIPs)                     │
└──────────────────────┬──────────────────────┘
                       ↓
┌───────────────────────────────────────────┐
│        Application Load Balancer          │
│        (Health Checks, SSL Termination)   │
└──────────┬──────────────────────┬─────────┘
           ↓                      ↓
    ┌─────────────────┐   ┌─────────────────┐
    │  App Server 1   │   │  App Server 2   │
    │  (ECS/EC2)      │   │  (ECS/EC2)      │
    │  Port 8000      │   │  Port 8000      │
    └────────┬────────┘   └────────┬────────┘
             │                     │
             └──────────┬──────────┘
                        ↓
           ┌────────────────────────┐
           │   Secrets Manager      │
           │   (API Keys, Certs)    │
           └────────────────────────┘
                        ↓
        ┌───────────────────────────┐
        │ RDS Aurora MySQL          │
        │ (Primary + Read Replica)  │
        │ Multi-AZ Deployment       │
        └───────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
   ┌─────────┐    ┌──────────┐   ┌─────────┐
   │   S3    │    │ ElastiCA-│   │CloudWatch│
   │ (Nanos) │    │ che      │   │ (Logs)  │
   └─────────┘    └──────────┘   └─────────┘
                        │
                   ┌────┴───┐
                   ↓        ↓
            ┌─────────┐  ┌────────┐
            │ Redis   │  │Lambda  │
            │(Cache)  │  │(Jobs)  │
            └─────────┘  └────────┘
```

---

## 2. Komponenten-Design

### 2.1 Frontend Layer

**Technologie Stack:**
- **Framework:** React 18+ oder Vue.js 3+ (später HTMX für lightweight MVP)
- **Build:** Vite (schneller als Webpack)
- **CSS:** Tailwind CSS + BEM Namenskonvention
- **State:** Zustand oder Pinia (leicht vs. Redux)
- **API Client:** Axios + React Query (Data Fetching)

**Deployment:**
- über S3 + CloudFront
- Static Site (no server-side rendering initially)
- Gzip + Minification

**Performance-Targets:**
- Lighthouse Score: >85
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms

### 2.2 Backend/API Layer

**Technologie Stack (Prototyp: Python/Solara, Produktiv: Python/FastAPI):**

```
FastAPI Monolith Architecture:

app/
├── main.py                    # Entry Point + Route Registration
├── config.py                  # Configuration, Env Vars
├── dependencies.py            # DI Container
│
├── api/
│   ├── __init__.py
│   ├── auth/
│   │   ├── router.py         # POST /auth/register, /auth/login
│   │   ├── schemas.py        # Pydantic Models
│   │   └── service.py        # Business Logic
│   ├── nanos/
│   │   ├── router.py         # GET /nanos, POST /nanos
│   │   ├── schemas.py
│   │   └── service.py
│   ├── search/
│   │   ├── router.py         # GET /search?q=...
│   │   └── service.py
│   ├── chat/
│   │   ├── router.py         # WebSocket + REST
│   │   └── service.py
│   ├── ratings/
│   │   ├── router.py         # POST /nanos/{id}/ratings
│   │   └── service.py
│   └── admin/
│       ├── router.py         # Admin endpoints
│       └── service.py
│
├── domain/
│   ├── models.py             # SQLAlchemy ORM Models
│   ├── enums.py              # Enum-Definitionen
│   └── repositories.py       # Data Access Layer
│
├── infrastructure/
│   ├── database.py           # DB Connections
│   ├── s3_service.py         # AWS S3 Integration
│   ├── elasticsearch.py      # Search Client
│   ├── redis_cache.py        # Caching
│   └── email_service.py      # Email Sending
│
├── security/
│   ├── jwt_handler.py        # JWT Token Gen/Validation
│   ├── password_hasher.py    # bcrypt/Argon2
│   └── permissions.py        # RBAC/ABAC
│
├── tasks/
│   ├── celery_config.py      # Async Job Queue
│   ├── moderation_jobs.py    # Background Moderation
│   └── notification_jobs.py  # Email/Notifications
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

**Key Design Patterns:**
- Repository Pattern (Data Access)
- Service Layer (Business Logic)
- Dependency Injection (for testability)
- Middleware (Auth, CORS, Logging)

**Performance Characteristics:**
- SQLAlchemy Connection Pooling (20 connections)
- Query Optimization (indexed, paginated)
- Caching Layer (Redis for Sessions + Frequent Queries)
- Background Jobs via Celery (large uploads, moderation)

### 2.3 Search Service

**Technologie:** Elasticsearch oder OpenSearch (AWS)

```yaml
# Index: nanos_v1
mappings:
  properties:
    id:
      type: keyword
    title:
      type: text
      fields:
        raw:
          type: keyword
    description:
      type: text
      analyzer: german  # German stemming
    categories:
      type: keyword
    created_at:
      type: date
    average_rating:
      type: float
    download_count:
      type: integer
    creator_id:
      type: keyword
```

**Query Logic (Python/Elasticsearch DSL):**
```python
# User searches for "Excel pivot"
query = {
  "bool": {
    "must": [
      {"multi_match": {
        "query": "Excel pivot",
        "fields": ["title^2", "description"]
      }}
    ],
    "filter": [
      {"term": {"status": "published"}},
      {"range": {"published_at": {"gte": "now-7d"}}}
    ]
  }
}
# Sorted by: _score (relevance), then average_rating DESC
```

### 2.4 Chat Service (Real-Time)

**MVP:** Polling (HTTP REST)  
**Phase 1:** WebSockets + Message Queue

```python
# MVP: REST Polling
GET /api/chats/{session_id}/messages?since=2025-02-24T10:00:00Z

# Phase 1: WebSocket Update
from fastapi import WebSocket
@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # Subscribe to Redis Pub/Sub
    # Broadcast new messages in real-time
```

---

## 3. Deployment-Architektur auf AWS

### 3.1 Container-Strategie (MVP + Phase 1)

```dockerfile
# Dockerfile for Fastapi Monolith
FROM python:3.11-slim as base
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/ ./app

# Expose Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Registry:** AWS ECR (Elastic Container Registry)

### 3.2 Orchestration: ECS (Elastic Container Service) oder EKS (Kubernetes)

**MVP:** ECS (Einfacher, AWS-Native)  
**Phase 2:** EKS (wenn Microservices-Bedarf wächst)

**ECS Cluster Setup:**
```
ECS Cluster: nano-prod
├── Service: api
│   └── Task Definition: api-service:1
│       ├── Container: app (FastAPI, 1 CPU, 2GB RAM)
│       ├── Logging: CloudWatch
│       └── Port: 8000
├── Service: background-jobs
│   └── Task Definition: jobs-worker:1
│       ├── Container: celery worker
│       ├── Logging: CloudWatch
│       └── Workers: 2
└── Auto Scaling:
    ├── Min Tasks: 1
    ├── Max Tasks: 5
    └── Target CPU: 70%
```

### 3.3 Load Balancing & Routing

```
Internet → CloudFront CDN
              ↓
      Application Load Balancer (ALB)
              ↓
         ┌────┴────┐
         ↓         ↓
    API Server  API Server
         ↓         ↓
         └────┬────┘
              ↓
          RDS Aurora

Health Checks: GET /health every 10s
Stickiness: Enabled for Chat Sessions (2h)
Idle Timeout: 60s
```

---

## 4. Persistenz-Strategie

### 4.1 Datenbank

**Primary:** AWS RDS Aurora MySQL (Multi-AZ)
```yaml
# AWS RDS Configuration
DBInstanceClass: db.t4g.medium (MVP) → db.r6g.large (Phase 1)
StorageType: io1 (15 IOPS per GB)
BackupRetention: 7 days
MultiAZ: Enabled (automatic failover)
EnableEncryption: true (RDS-managed keys)
PubliclyAccessible: false (VPC private)
```

### 4.2 Object Storage

**Primary:** AWS S3
```
Bucket: nano-marketplace-prod
├── /nanos/                  # Nano ZIPs
├── /avatars/                # User Avatars
├── /thumbnails/             # Nano Thumbnails
├── /audit-logs/             # Compliance Logs
└── /backups/                # DB Snapshots
```

**Versioning:** Enabled (for audit, can restore old nano versions)  
**Lifecycle:**  
- Audit logs: Transition to Glacier after 90 days  
- Deleted nanos: Delete after 2 years (retention per DSGVO 6 years, reduce after)

### 4.3 Search Index

**Primary:** AWS OpenSearch (managed Elasticsearch)
```yaml
OpenSearch Domain: nano-marketplace
NodeType: t3.small.search (2 nodes)
StorageSize: 100 GB (autoscaling enabled)
Backups: Daily to S3
Indexes:
  - nanos_v1 (live)
  - nanos_v0 (for migration)
```

### 4.4 Cache Layer

**Primary:** AWS ElastiCache (Redis)
```yaml
CacheNodeType: cache.t4g.micro (MVP)
NumCacheNodes: 1 (standalone, no failover)
ParameterGroup:
  maxmemory-policy: allkeys-lru  # Auto-evict when full
  appendonly: yes               # Persistence enabled
TTLs:
  Session: 1 hour
  Search Results: 30 minutes
  User Profile: 1 hour
```

---

## 5. Skalierungs-Strategie

### 5.1 Vertical Scaling (Scale-Up)

```
Scenario: RDS at 90% CPU

Action Sequence:
1. CloudWatch Alert triggered
2. Plan maintenance window
3. Modify RDS Instance:
   db.t4g.medium → db.t4g.large (double CPU/RAM)
   Multi-AZ handles downtime (~2-3 min)
4. Auto-rebalance from Replica
5. Monitor metrics
```

### 5.2 Horizontal Scaling (Scale-Out)

```
Scenario: ECS Service at 80% CPU

Auto Scaling Rules:
- Metric: ECS CPU Utilization
- Target: 70%
- Scale-up: +1 task if > 75% for 2 min
- Scale-down: -1 task if < 60% for 5 min
- Min: 1 task | Max: 5 tasks

Result: Auto-scale from 1 → 3 → 5 tasks
Load Balancer routes across all 5
```

### 5.3 Database Scaling

```
Read-Heavy Workload (Search, Browsing):
- Primary: RDS Aurora (writes)
- Read-Replicas: 1-2 Replicas
- Application: Read-Write Splitting
  - SELECT queries → Replica
  - INSERT/UPDATE → Primary

Write-Heavy Workload (Future):
- Sharding Strategy
  - Shard by Creator_ID or Organization
  - Requires application-layer routing
```

### 5.4 Caching & CDN

```
Static Assets:
  React SPA → CloudFront → S3
  Caching: 1 year (versioned filenames)
  
API Responses:
  GET /nanos → Redis Cache (30 min)
  Invalidates on: Update/Delete
  
Database Connections:
  SQLAlchemy Pool: 20 connections
  Overflow: queue 10 requests
  Max retries: 3
```

---

## 6. API Design & Versioning

### 6.1 RESTful Endpoints

```
Authentication:
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh-token
GET    /api/v1/auth/me

Nanos (CRU-D):
GET    /api/v1/nanos?page=1&limit=20&category=excel&level=1
GET    /api/v1/nanos/{id}
POST   /api/v1/nanos (requires auth + creator role)
PATCH  /api/v1/nanos/{id} (creator or admin only)
DELETE /api/v1/nanos/{id} (soft-delete: archive)

Ratings:
GET    /api/v1/nanos/{id}/ratings
POST   /api/v1/nanos/{id}/ratings (requires auth)
PATCH  /api/v1/ratings/{rating_id} (owner or admin)

Chat:
GET    /api/v1/chats?nano_id={id}
POST   /api/v1/chats (start new chat)
GET    /api/v1/chats/{session_id}/messages?since={timestamp}
POST   /api/v1/chats/{session_id}/messages (send message)
WS     /api/v1/ws/chat/{session_id} (WebSocket, Phase 1)

Search:
GET    /api/v1/search?q=excel&category=business

Admin:
GET    /api/v1/admin/dashboard
GET    /api/v1/admin/moderation/queue
POST   /api/v1/admin/moderation/{flag_id}/decision
GET    /api/v1/admin/audit-logs?user_id={id}&action={action}
```

### 6.2 Response Format

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Excel für Anfänger",
    "...": "..."
  },
  "meta": {
    "page": 1,
    "total": 150,
    "per_page": 20
  },
  "timestamp": "2025-02-24T10:15:00Z"
}
```

### 6.3 Error Handling

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid authorization token",
    "details": {
      "field": "Authorization header",
      "expected": "Bearer <jwt_token>"
    }
  },
  "timestamp": "2025-02-24T10:15:00Z"
}
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
┌─────┐                                              ┌────────┐
│User │                                              │FastAPI │
└──┬──┘                                              └───┬────┘
   │                                                     │
   │ POST /auth/login                                    │
   │ {email, password}                                   │
   ├────────────────────────────────────────────────>   │
   │                                                     │ Hash & Compare
   │                                                     │ vs DB
   │ 200 OK                                              │
   │ {access_token, refresh_token, expires_in}          │
   │ <─────────────────────────────────────────────     │
   │                                                     │
   │ Subsequent Request                                  │
   │ GET /nanos                                          │
   │ Authorization: Bearer {access_token}                │
   ├────────────────────────────────────────────────>   │
   │                                                     │ Validate JWT
   │ 200 OK + Nanos List                                 │
   │ <─────────────────────────────────────────────     │
   │                                                     │
   │ Token Expired                                       │
   │ POST /auth/refresh-token                            │
   │ Authorization: Bearer {refresh_token}               │
   ├────────────────────────────────────────────────>   │
   │ 200 OK {new_access_token}                           │
   │ <─────────────────────────────────────────────     │
```

### 7.2 Authorization (RBAC)

```python
# Middleware: Check JWT + Extract User Claims
from fastapi import Depends, HTTPException

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        user_id = payload.get("sub")
        role = payload.get("role")
    except:
        raise HTTPException(401, "Invalid token")
    return {"user_id": user_id, "role": role}

# Endpoint: Check Permission
@router.post("/nanos/{nano_id}/ratings")
async def create_rating(
    nano_id: str,
    rating: RatingCreate,
    current_user = Depends(get_current_user)
):
    # RBAC Check: Only "consumer" can rate
    if current_user["role"] not in ["consumer", "creator", "admin"]:
        raise HTTPException(403, "Not authorized")
    # ... create rating
```

---

## 8. Fehlertoleranz & Backup

### 8.1 Hochverfügbarkeit (HA)

```
Target: 99.95% Uptime (51 Minuten Downtime/Jahr)

Strategies:
- Multi-AZ Deployment (ALB across AZ-a, AZ-b)
- RDS Aurora Multi-AZ (automatic failover)
- ElastiCache with Multi-AZ (replication)
- CloudFront Global Distribution
- Health Checks every 10s
  * ALB pings ECS tasks
  * ECS replaces failed tasks (within 30s)
```

### 8.2 Disaster Recovery (DR)

```
RTO (Recovery Time Objective): <1 Hour
RPO (Recovery Point Objective): <15 Minutes

Backup Strategy:
- DB Snapshots: Daily (automated)
- S3 Versioning: Enabled (can restore old versions)
- Audit Logs: Sent to S3 (immutable)

Restore Procedure:
1. Detect failure alert
2. Validate last good snapshot
3. Restore RDS from snapshot
4. Restore S3 data (if needed)
5. Point DNS to new infrastructure
6. Smoke tests
```

---

## 9. Monitoring & Observability

```
┌──────────────────┐
│  Application     │ → Logs: CloudWatch
│  (Requests)      │ → Metrics: CloudWatch
│  (Errors)        │ → Traces: X-Ray
└──────────────────┘

Dashboards:
- Real-time API Latency (p50, p95, p99)
- Error Rate (5xx, 4xx)
- Active Users / Sessions
- Database Connections
- Cache Hit Rate
- S3 Upload/Download Rate
```

---

## 10. Migration Path: Monolith → Microservices

```
MVP (Q3 2025):
  Monolithic FastAPI
  └─ Single Deployment

Phase 1 (Q1 2026):
  Still Monolithic but
  Code organized as modules
  └─ Easy to extract later

Phase 2 (Q3 2026):
  Microservices:
  ├─ Auth Service (Keycloak)
  ├─ Nano Service (Java/Go, separate DB)
  ├─ Chat Service (Node.js, WebSocket focus)
  ├─ Search Service (ES, dedicated)
  └─ Shared Infrastructure (API Gateway, Message Queue)
```

---

## Referenzen

- [04 — Domänenmodell](./04_domain_model.md) (Datenbank-Design)
- [06 — Security & Compliance](./06_security_compliance.md) (Security Details)
- [10 — Operations & Observability](./10_operations_observability.md) (Monitoring)
