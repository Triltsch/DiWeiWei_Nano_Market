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

### 1.2 Deployment-Modell: Vendor-Neutral (Open-Source First)

**MVP Options:** Docker Compose, Self-Hosted, or Traditional VPS  
**Later (Phase 2):** Kubernetes for advanced scaling

```
┌───────────────────────────────────────────────────────────┐
│                    INTERNET / CDN                         │
├───────────────────────────────────────────────────────────┤
│              Nginx/Caddy Reverse Proxy                    │
│          (SSL Termination, Caching, CDN Alt)             │
│          or: Cloudflare Free Tier (optional CDN)          │
└──────────────────────┬──────────────────────┘
                       ↓
┌───────────────────────────────────────────┐
│        Nginx/Caddy Load Balancer          │
│        (Health Checks, SSL Termination)   │
└──────────┬──────────────────────┬─────────┘
           ↓                      ↓
    ┌─────────────────┐   ┌─────────────────┐
    │  Container 1    │   │  Container 2    │
    │  (FastAPI)      │   │  (FastAPI)      │
    │  Port 8000      │   │  Port 8000      │
    └────────┬────────┘   └────────┬────────┘
             │                     │
             └──────────┬──────────┘
                        ↓
           ┌────────────────────────┐
           │   Secrets Management   │
           │   (Vault or .env)      │
           └────────────────────────┘
                        ↓
        ┌───────────────────────────┐
        │   PostgreSQL Database     │
        │   (Self-Hosted or        │
        │    Managed Non-AWS)       │
        │   Primary + Read Replica  │
        │   or: Multi-Node Setup    │
        └───────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
   ┌─────────┐    ┌──────────┐   ┌─────────┐
   │  MinIO  │    │Elasticsearch│ Prometheus│
   │(S3-compat)   │ / Meilisearch│(Metrics) │
   │ (Nanos) │    │ (Search) │   │ (Logs)  │
   └─────────┘    └──────────┘   └─────────┘
                        │
                   ┌────┴──────┬────────┐
                   ↓           ↓        ↓
            ┌─────────┐  ┌────────┐ ┌────────┐
            │  Redis  │  │ Celery │ │ Grafana│
            │(Cache)  │  │(Jobs)  │ │(Dashbrd│
            └─────────┘  └────────┘ └────────┘
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

## 3. Deployment-Architektur (Vendor-Agnostic, Open-Source)

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

**Registry:** Docker Hub, GitHub Container Registry, or Self-Hosted

### 3.2 Orchestration Options

**Option A: Docker Compose (MVP - Simplest)**

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app1
      - app2

  app1:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/nano_db
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - postgres
      - redis
      - elasticsearch

  app2:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/nano_db
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - postgres
      - redis
      - elasticsearch

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=nano_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  minio:  # S3-compatible object storage
    image: minio/minio:latest
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"  # Web UI
    volumes:
      - minio_data:/data

  prometheus:  # Metrics
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:  # Dashboards
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  minio_data:
  prometheus_data:
```

**Deployment:** `docker-compose up -d`

**Option B: Kubernetes (Phase 2 - if scaling needed)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nano-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nano-api
  template:
    metadata:
      labels:
        app: nano-api
    spec:
      containers:
      - name: api
        image: nano-marketplace:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: nano-api-service
spec:
  selector:
    app: nano-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deployment:** `kubectl apply -f deployment.yaml`

### 3.3 Load Balancing & Reverse Proxy

**Nginx (Recommended):**

```nginx
upstream backend {
    server app1:8000;
    server app2:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name nano-marketplace.de;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health checks
    location /health {
        access_log off;
        proxy_pass http://backend;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    location /api/v1/auth/login {
        limit_req zone=login;
        proxy_pass http://backend;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name nano-marketplace.de;
    return 301 https://$server_name$request_uri;
}
```

**Alternative: Caddy (Simpler TLS):**

```
nano-marketplace.de {
    encode gzip
    
    reverse_proxy localhost:8000 {
        healthuri /health
        unhealthy_status 500
    }

    # Rate limiting
    rate_limit /api/v1/auth/login 5/1m
}
```

---

## 4. Persistenz-Strategie (Open-Source)

### 4.1 Datenbank

**Primary:** PostgreSQL (Self-Hosted or Managed Non-AWS)

```yaml
# Docker Compose Example
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=nano_db
    - POSTGRES_USER=nano_user
    - POSTGRES_PASSWORD=${DB_PASSWORD}
    - POSTGRES_INITDB_ARGS: "-c shared_buffers=256MB -c max_connections=100"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./backups:/backups
  ports:
    - "5432:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U nano_user"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Configuration (MVP):**
- Single Instance (or Primary + 1 Read Replica)
- Backup: Daily snapshots to external storage
- Replication: Binary logs shipped to S3 or MinIO
- Encryption: pgcrypto for sensitive fields
- Connection Pool: PgBouncer (optional, for scaling)

**Alternatives:**
- **PostgreSQL on Managed Service:** Managed PostgreSQL (DigitalOcean, Render, Railway)
- **Traditional VPS:** Self-hosted on hetzner.com, Linode, DigitalOcean VPS

### 4.2 Object Storage

**Primary:** MinIO (S3-Compatible, Open-Source)

```dockerfile
# MinIO Installation (Docker)
minio:
  image: minio/minio:latest
  environment:
    - MINIO_ROOT_USER=minioadmin
    - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
  command: server /data --console-address ":9001"
  volumes:
    - minio_data:/data
  ports:
    - "9000:9000"      # API
    - "9001:9001"      # Web Console
```

**Bucket Structure:**
```
nano-marketplace/
├── nanos/              # Nano ZIPs
├── avatars/            # User Avatars
├── thumbnails/         # Nano Previews
├── audit-logs/         # Compliance Logs
└── backups/            # DB Backups
```

**Features:**
- Versioning: Enabled (can restore old Nano versions)
- Lifecycle: Transition old audit-logs to cheaper storage after 2 years
- Replication: MinIO can replicate to remote server
- Access Control: IAM Policies (S3-compatible format)

**Alternatives:**
- **NFS/SFTP:** Traditional shared filesystem (simpler for small deployments, less scalable)
- **Seaweed:** Distributed object storage (lightweight)
- **Ceph:** Multi-node distributed storage (complex setup)

### 4.3 Search Index

**Primary:** Elasticsearch (Self-Hosted) or Meilisearch (Simpler)

**Option A: Elasticsearch (Feature-Rich)**

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - ES_JAVA_OPTS="-Xms512m -Xmx512m"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  ports:
    - "9200:9200"
```

**Index Configuration:**
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "german_analyzer": {
          "type": "standard",
          "stopwords": "_german_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "german_analyzer",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "description": {"type": "text", "analyzer": "german_analyzer"},
      "categories": {"type": "keyword"},
      "average_rating": {"type": "float"},
      "created_at": {"type": "date"}
    }
  }
}
```

**Option B: Meilisearch (Simpler, Faster Setup)**

```yaml
meilisearch:
  image: getmeili/meilisearch:latest
  environment:
    - MEILI_MASTER_KEY=${MEILI_KEY}
  volumes:
    - meilisearch_data:/meili_data
  ports:
    - "7700:7700"
```

Benefits: 
- Zero-configuration, comes with good defaults
- Typo-tolerant by default
- Faster to deploy than Elasticsearch

Trade-offs:
- Less customizable than Elasticsearch
- Fewer advanced features (no complex filtering)

### 4.4 Cache Layer

**Primary:** Redis (Self-Hosted)

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Configuration:**
```
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru   # Auto-evict when full
appendonly yes                 # Persistence
```

**Usage:**
- Session Storage: 1-hour TTL
- Search Results Cache: 30-min TTL
- User Profile Cache: 1-hour TTL
- Job Queue: Celery backed by Redis

**Alternative:** MemCached (simpler, if persistence not needed)

---

## 5. Skalierungs-Strategie (Vendor-Agnostic)

### 5.1 Vertical Scaling (Scale-Up)

```
Scenario: Database at 90% CPU

Manual Action:
1. Monitor metrics via Prometheus/Grafana
2. Identify resource bottleneck
3. Plan maintenance window
4. Increase container resources:
   - PostgreSQL: Request more memory/CPU in docker-compose
   - Restart container (downtime ~30-60 seconds)
   - Verify recovery
5. For zero-downtime: Use read replica promotion
```

### 5.2 Horizontal Scaling (Scale-Out)

**Application Scaling (Easy):**
```yaml
# docker-compose.yml - Scale API Workers
services:
  app:
    build: .
    deploy:
      replicas: 3  # Increase replicas as needed
    # ... container config ...
```

**Command:**
```bash
docker-compose up -d --scale app=5  # Scale to 5 instances
```

**Load Distribution:**
- Nginx round-robin distributes requests across all app instances
- Stateless FastAPI allows any instance to handle any request

### 5.3 Database Scaling

**Read Replicas (for Read-Heavy Workloads):**

```
Primary PostgreSQL (Read + Write)
        │
        ├─→ Read Replica 1
        ├─→ Read Replica 2
        └─→ Read Replica 3

Setup:
- Primary: Write all data
- Replicas: Replicate via WAL (Write-Ahead Logging)
- Application: Route SELECT queries to replicas
- Fallback: Use primary if replica fails
```

**Sharding (for Write-Heavy Workloads - Phase 2):**
```
Shard by Creator_ID:
- Shard 1: Creator IDs 0-999 → PostgreSQL 1
- Shard 2: Creator IDs 1000-1999 → PostgreSQL 2
- Shard 3: Creator IDs 2000+ → PostgreSQL 3

Router logic: creator_id % 3 = shard_number
```

### 5.4 Caching & Performance

**Multi-Level Caching:**
```
1. Browser Cache:
   - Static assets: 1-year cache headers
   - Versioned filenames

2. Reverse Proxy Cache (Nginx):
   - GET endpoints: cache 5 minutes
   - Invalidate on POST/PATCH/DELETE

3. Application Cache (Redis):
   - Search results: 30 min TTL
   - User profiles: 1 hour TTL

4. Database:
   - Query optimization (indexes)
   - Connection pooling (PgBouncer: 50 connections)
```

**Performance Targets:**
```
- Homepage load: <2s (3G network)
- Search: <500ms
- API response: <100ms (p95)
- Uptime: 99.5%
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

## 8. Fehlertoleranz & Backup (Open-Source Stack)

### 8.1 Hochverfügbarkeit (HA)

```
Target: 99.5% Uptime (51 Minuten Downtime/Jahr)

Strategies:
- Multi-Container Deployment (docker-compose or Kubernetes)
- PostgreSQL with Streaming Replicas
- Redis with Replication or Sentinel
- Nginx/Caddy load balancing
- Health checks every 10s
  * Nginx monitors app health
  * Replaces failed instances automatically
```

**Docker Compose with Health Checks:**
```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
```

**Kubernetes Self-Healing:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 8.2 Disaster Recovery (DR)

```
RTO (Recovery Time Objective): <1 Hour
RPO (Recovery Point Objective): <15 Minutes

Backup Strategy:
- PostgreSQL: WAL archival to MinIO (continuous)
- MinIO buckets: Mirrored to external storage daily
- Point-in-Time Recovery (PITR) available from WAL archive
- Test restores monthly
```

**Backup Automation (Bash + Cron):**
```bash
#!/bin/bash
# Daily PostgreSQL backup

BACKUP_DIR="/backups"
DB_NAME="nano_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -h localhost -U nano_user $DB_NAME | gzip > $BACKUP_DIR/db_${TIMESTAMP}.sql.gz

# Upload to MinIO
aws s3 cp $BACKUP_DIR/db_${TIMESTAMP}.sql.gz s3://nano-marketplace-backups/ \
  --endpoint-url http://minio:9000

# Retain last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

**Restore Procedure:**
```bash
# 1. Retrieve backup from MinIO
aws s3 cp s3://nano-marketplace-backups/db_20250224_100000.sql.gz . \
  --endpoint-url http://minio:9000

# 2. Restore database
gunzip < db_20250224_100000.sql.gz | psql -h localhost -U nano_user -d nano_db

# 3. Validate
psql -h localhost -U nano_user -d nano_db -c "SELECT COUNT(*) FROM users;"

# 4. Point DNS to new infrastructure
```

---

## 9. Monitoring & Observability (Open-Source Stack)

```
┌──────────────────┐
│  Application     │ → Logs: Loki or ELK Stack
│  (Requests)      │ → Metrics: Prometheus
│  (Errors)        │ → Traces: Jaeger or Zipkin
│  (Business Logic)│ → Dashboards: Grafana
└──────────────────┘

Collection:
- App: Emit metrics via StatsD or Prometheus client
- Nginx: Nginxprometheus module or Prometheus exporter
- PostgreSQL: postgres_exporter
- Redis: redis_exporter
- System: Node exporter
```

**Prometheus Stack (Recommended):**

```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'

grafana:
  image: grafana/grafana:latest
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=securepassword
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
  ports:
    - "3000:3000"
  depends_on:
    - prometheus

loki:
  image: grafana/loki:latest
  volumes:
    - ./loki-config.yml:/etc/loki/local-config.yml:ro
    - loki_data:/loki
  ports:
    - "3100:3100"

prometheus-exporter-postgres:
  image: prometheuscommunity/postgres-exporter:latest
  environment:
    - DATA_SOURCE_NAME=postgresql://user:pass@postgres:5432/nano_db
  ports:
    - "9187:9187"

prometheus-exporter-redis:
  image: oliver006/redis_exporter:latest
  command: -redis-addr=redis://redis:6379
  ports:
    - "9121:9121"
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
```

**Key Metrics to Monitor:**
```
Application:
- http_request_duration_seconds (histogram)
- http_requests_total (counter)
- http_errors_total (counter)
- active_users (gauge)

Database:
- pg_stat_database_tup_fetched (tuples fetched)
- pg_stat_database_tup_inserted (inserts)
- pg_connections_used (connection count)
- pg_cache_hit_ratio (cache performance)

System:
- node_cpu_usage_percent
- node_memory_usage_bytes
- node_disk_usage_bytes
- node_network_transmit_bytes
```

**Grafana Dashboards:**
- API Performance (request rate, latency, errors)
- Database Health (connections, query time, cache hit ratio)
- Infrastructure (CPU, memory, disk, network)
- Business Metrics (active creators, nanos uploaded, ratings)

**Alerting (Prometheus AlertManager):**
```yaml
groups:
  - name: Application
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowAPI
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 10m
        annotations:
          summary: "API p95 latency > 2 seconds"

  - name: Database
    rules:
      - alert: HighDiskUsage
        expr: pg_database_size_bytes > 80000000000
        annotations:
          summary: "DB size > 80GB"

      - alert: HighConnectionCount
        expr: pg_connections_used > 90
        annotations:
          summary: "DB connections > 90% capacity"
```

**AlertManager Routing:**
```yaml
# alertmanager.yml
route:
  receiver: 'team-notifications'
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'team@nano-marketplace.de'
        from: 'alerts@nano-marketplace.de'
        smarthost: 'smtp.example.com:587'
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
