# 11 — Risiken, Annahmen & Architekturentscheidungen

---

## 1. Risiko-Register

### 1.1 Kritische Risiken (🔴 ROTE FLAGGE)

| Risiko | Probability | Impact | Score | Mitigation | Owner |
|--------|------------|--------|-------|-----------|-------|
| **DSGVO Violation** | Mittel (40%) | Kritisch | 40 | Audit pre-launch, Legal review | Legal |
| **Data Breach** | Gering (20%) | Kritisch | 20 | Penetration test, Incident plan | Security |
| **Service Outage >24h** | Gering (10%) | Hoch | 10 | Multi-region DR, Auto-scaling | Ops |
| **Chat Privacy Leak** | Mittel (35%) | Kritisch | 35 | E2E encryption Phase 1, TLS MVP | Security |
| **SQL Injection** | Gering (15%) | Kritisch | 15 | Parameterized queries, SAST | Dev |

### 1.2 Hohe Risiken (🟠 ORANGE)

| Risiko | Probability | Impact | Mitigation |
|--------|------------|--------|-----------|
| **Marketplace Coldstart** | Hoch (70%) | Hoch | Pre-seed with 20+ Nanos, Partner launches |
| **Creator/Consumer Imbalance** | Hoch (60%) | Hoch | Targeted GTM per segment |
| **Quality Moderation Fails** | Mittel (50%) | Hoch | Automated filters Phase 1, SLA enforcement |
| **Scaling Under Load** | Mittel (40%) | Hoch | Load testing baseline, Auto-scaling Group |
| **Payment Integration Delays** | Gering (25%) | Mittel | Tausch-Modell MVP, Stripe ready Phase 1 |

### 1.3 Mittlere Risiken (🟡 GELB)

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **Key Person Dependency** | Mittel (45%) | Mittel | Documentation, Knowledge transfer |
| **Budget Overruns** | Mittel (50%) | Mittel | 20% contingency buffer, Weekly tracking |
| **Scope Creep** | Hoch (65%) | Mittel | Strict MVP scope, Change control board |
| **Integration Complexity** | Mittel (35%) | Mittel | API-first design, Early partner testing |
| **OSS Configuration Drift** | Mittel (40%) | Mittel | Terraform/Ansible IaC, Configuration audits |
| **Self-Hosted Backup Failure** | Gering (25%) | Hoch | Automated validation, External B2 archive |
| **DevOps Staffing Gap** | Mittel (45%) | Mittel | Sprint 0 onboarding, Cross-training developers |
| **Single Docker Host SPOF** | Gering (20%) | Mittel | Phase 2 Kubernetes migration pre-planned |

---

## 2. Annahmenliste (Assumptions)

### 2.1 Markt-Annahmen

| Annahme | Kritikalität | Validierung | Evidence |
|--------|--------------|------------|----------|
| **There is market demand for Nano-LMS** | KRITISCH | Q3 Pilot | Studienarbeit + 3 interviews |
| **Weiterbilder wollen Nanos teilen** | KRITISCH | Q3 Pilot | Target: 20+ Creator in MVP |
| **Unternehmen zahlen für Kuration** | HOCH | Q1 2026 | Revenue model TBD |
| **Tausch-Modell ist nachhaltig** | MITTEL | Ongoing | Monitor adoption rate |

### 2.2 Technische Annahmen

| Annahme | Kritikalität | Fallback |
|--------|--------------|----------|
| **Docker Compose skaliert zu 5k DAU** | MITTEL | Migrate to Kubernetes for >5k DAU |
| **PostgreSQL skaliert zu 10k+ DAU** | MITTEL | Sharding or read-replicas (Phase 2) |
| **FastAPI kann 1000 RPS handhaulen** | MITTEL | Upgrade zu Node.js / Go if needed |
| **Elasticsearch ist "good enough"** | GERING | Use Meilisearch or Algolia as SaaS |
| **MinIO self-hosted durability adequate** | MITTEL | Switch to managed PostgreSQL all-DBs if issues |
| **Prometheus/Loki overhead <5% CPU** | MITTEL | Simplify metrics or use SaaS if overhead high |
| **Managed PostgreSQL backup 100% reliable** | HOCH | Implement additional external backup layer |

### 2.3 Organisatorische Annahmen

| Annahme | Kritikalität |
|--------|--------------|
| DI haben ausreichend Budget (180k€ MVP) | KRITISCH |
| Team wächst um 2 FTE in Q4 | HOCH |
| 1 Moderator reicht bis 500 Nanos | MITTEL |
| Admin-Onboarding <1 Woche | GERING |

---

## 3. Architektur-Entscheidungen (ADRs)

### ADR-001: Monolith vs Microservices

**Decision:** Modular Monolith for MVP → Microservices Phase 2

**Context:**
- MVP needed in 2 months
- Team: 3 engineers (small)
- Unknown scale & demand
- YAGNI principle

**Options Evaluated:**
1. **Monolith (Selected):** Fast, simple, cheaper
2. Microservices from day 1: Over-engineered, slower delivery
3. Serverless (Lambda): Good for scaling, weak for real-time chat

**Consequences:**
- ✅ Faster MVP delivery
- ✅ Simpler deployment & debugging
- ✅ Lower operational overhead
- ❌ Harder to scale individual components
- ❌ Temp codebases mixing concerns (mitigated by modular structure)

**Revisit:** After 10k DAU or 12 months, evaluate Microservices migration

---

### ADR-002: Database: PostgreSQL vs MySQL

**Decision:** PostgreSQL (managed or self-hosted)

**Evaluated Options:**
1. **PostgreSQL (Selected):** Better JSON support, strong ACID, superior indexing
2. MySQL: Simpler, wider adoption, but weaker JSON/Full-text search
3. DynamoDB: NoSQL, good for scale, but complex queries hard
4. MongoDB: Flexible schema, but consistency/ACID guarantees weaker

**Decision Factors:**
- JSONB support for flexible metadata (future)
- Full-text search with German tokenizer
- ACID guarantees critical for financial data (future)
- Managed PostgreSQL reduces operational overhead

**Tradeoffs:**
- PostgreSQL: Steeper learning curve, but stronger guarantees
- MySQL: Easier migration path from prototype (which uses MySQL)

---

### ADR-003: Frontend: React vs Vue

**Decision:** React 18+ (Framework TBD, but React preferred)

**Context:**
- Team has React experience
- Larger ecosystem (libraries, staffing)
- State management options (Zustand, Recoil)

**Alternatives Considered:**
- Vue.js: Smaller bundle, easier learning curve
- Svelte: Modern, reactive, but less mature
- HTMX: Lightweight, but less interactive

**Justification:** Stick with team strengths, abundant hiring market

---

### ADR-004: Authentication Method

**Decision:** JWT + Refresh Token (MVP), 2FA TOTP (Phase 1)

**Alternatives:**
1. Session-based (PHP-style): Stateful, simpler, outdated
2. **JWT (Selected):** Stateless, scalable, industry-standard
3. OAuth2/OIDC: More complex, needed only for SSO (Phase 1)

**Token Details:**
- Access Token: 15 min expiry, HttpOnly cookie only (NO localStorage - XSS risk)
- Refresh Token: 7 day expiry, HttpOnly Secure SameSite=Strict cookie only  
- Claim: {user_id, email, role, exp, iat}
- **Security Note:** HttpOnly cookie prevents XSS exfiltration, SameSite prevents CSRF

---

### ADR-005: Nano Storage Format

**Decision:** ZIP files in object storage (MinIO) + Metadata in PostgreSQL

**Alternatives:**
1. **ZIP in MinIO (Selected):** Immutable, versioned, cost-efficient, follows prototype
2. Unzipped in object storage: More granular, but complex deduplication
3. Database BLOB: Simple, but scales poorly
4. Git-like versioning (gitsync): Complex, overkill

**Rationale:** ZIP matches creator's mental model, easy to export/import

**Versioning:** Via nano_versions table + object storage versioning

---

### ADR-006: Search Backend

**Decision:** Elasticsearch (self-hosted) or Meilisearch

**Alternatives:**
1. **Elasticsearch (Selected):** Full-text, faceted search, German tokenizer, industry-standard
2. Database full-text (PostgreSQL): OK for MVP, but weaker ranking
3. Algolia SaaS: Expensive, but zero-ops
4. Solr: OpenSource, but more setup

**Rationale:** 
- Nano descriptions + metadata-rich queries need advanced search
- Relevance ranking important for discovery
- German stemming built-in

---

### ADR-007: Real-time Architecture

**Decision:** HTTP Polling (MVP) → WebSocket (Phase 1)

**Alternatives:**
1. **Polling (MVP):** Simple, no infrastructure, works for low-frequency messages
2. WebSocket: Real-time, but stateful, needs message queue for scale
3. Server-Sent Events (SSE): Middle ground, unidirectional
4. MQTT: Overkill for this use case

**Rationale (MVP):** 
- Chat messages are not super time-critical (<15 min is fine)
- Reduces infrastructure complexity
- Manual "Refresh" button acceptable

**Phase 1 Plan:** Migrate to WebSocket + Redis Pub/Sub

---

### ADR-008: Payment Processing (Future)

**Decision:** Defer payments to Phase 2, use Tausch-Modell MVP

**Rationale:**
- MVP focus on supply/demand matching, not monetization
- Payment adds regulatory complexity (PSD2, VAT)
- Stripe/PayPal mature enough for Phase 1

**When to Trigger Move:** When:
- >80% marketplace participants want paid options
- Legal clarifies tax treatment
- Platform revenue model crystallizes

---

### ADR-009: Chat Encryption Strategy

**Decision:** TLS in transit (MVP) → E2E optional (Phase 2)

**Reasoning:**
- TLS sufficient for MVP (all party is within platform)
- E2E adds client-side complexity, no server-side search
- Optional feature appeals to privacy-conscious users

**Implementation:**
- MVP: All chat over HTTPS/TLS
- Phase 1: Optional E2E toggle (Signal protocol or similar)

---

### ADR-010: Infrastructure Foundation - Open-Source vs. AWS

**Decision:** Open-source, self-hosted stack (Vendor-agnostic, no AWS lock-in)

**Context:**
- Production-grade MVP requires robust infrastructure
- Cost efficiency critical for pre-revenue startup
- Long-term flexibility and community support valued
- DSGVO compliance requires EU data residency control

**Alternatives Considered:**
1. **Open-Source Stack (Selected):** PostgreSQL, Nginx, Docker, Prometheus, Loki, MinIO
2. AWS-managed: ALB, RDS, S3, CloudWatch, but vendor lock-in risk
3. Hybrid: AWS compute + open-source databases (complexity/cost middle ground)

**Technology Mapping:**
| Function | AWS (Old) | Open-Source (New) |
|----------|-----------|------------------|
| Load Balancing | ALB | Nginx / Caddy |
| Database | RDS Aurora | PostgreSQL |
| Object Storage | S3 | MinIO |
| Search | OpenSearch | Elasticsearch |
| Cache | ElastiCache | Redis |
| Metrics | CloudWatch | Prometheus |
| Logs | CloudWatch Logs | Loki |
| Traces | X-Ray | Jaeger |
| Alerting | SNS/CloudWatch | Prometheus AlertManager |
| Container Mgmt | ECS | Docker Compose (MVP) / Kubernetes (Phase 2) |

**Justification:**
- Cost: 30-40% annual savings (€13-14k/month ops vs €18-25k AWS)
- Control: Full infrastructure visibility, disaster recovery, backup strategy
- Vendor independence: Avoid AWS re-lock-in, community-driven evolution
- Scalability: Clear upgrade path (Docker Compose → Kubernetes Phase 2)

**Tradeoffs:**
- Operations: Higher DevOps expertise required (self-hosting vs managed AWS)
- Staffing: Needs dedicated DevOps engineer (vs AWS console click-ops)
- Single points of failure: Docker Compose MVP has no built-in redundancy
- Learning: Team must master new tool ecosystem (Prometheus, Loki, etc)

**Deployment Models:**
1. **Docker Compose (MVP):** Single VPS, simplest, suitable for <10k users
2. **Managed hybrid:** PostgreSQL managed (DigitalOcean/Render) + app VPS
3. **Kubernetes (Phase 2):** Multi-node, auto-scaling, when >10k DAU expected

**Cost Analysis (Annual):**
- MVP (6M): €10-15k infrastructure + €30k ops + €60k dev = €100-105k ✓ Under budget
- Post-MVP (3M operations): €3.6-5.4k infrastructure + €22.5k ops + €24k dev = €50-51.9k/quarter
- AWS equivalent: €15-25k/month = €45-75k/quarter (33-47% more expensive)

**Monitoring:** Costs tracked monthly via infrastructure metering, Prometheus metrics

**Status:** Accepted (Coordinated with 05_system_architecture.md)

---

### ADR-011: Application Container Orchestration - Docker Compose vs. Kubernetes

**Decision:** Docker Compose for MVP (sprint 0-1), Kubernetes for Phase 2 (when >5k DAU)

**Context:**
- MVP timeline: 8 weeks, 150 PT
- Kubernetes complexity: 5-10% ops overhead, needs cluster management
- Docker Compose simplicity: 1 server, 1 config file, suitable for MVP scale
- Future scalability: Predetermined Phase 2 target with K8s

**Alternatives Considered:**
1. **Docker Compose (Selected for MVP):** Simple, single-file config, 1 server suitable
2. Kubernetes now: Future-proof, but adds 3-4 weeks dev ops work + complexity
3. Nomad/ECS: Middle ground, but fewer team skills

**Justification:**
- MVP scale: <10k users fits on single t3.xlarge instance
- Team skills: FastAPI devs, no K8s ops expertise yet
- Timeline: 8-week constraint precludes K8s ops setup
- Clear upgrade: Docker Compose → K8s is well-documented pattern

**Docker Compose MVP Services:**
```yaml
services:
  nginx: Reverse proxy, SSL, load balancing
  fastapi: Application (uvicorn)
  postgresql: Database with replication config
  redis: Session cache, rate limiting
  elasticsearch: Full-text search
  prometheus: Metrics collection
  grafana: Visualization
  loki: Log aggregation
  jaeger: Distributed tracing
  minio: Object storage
```

**Kubernetes Phase 2 Rationale:**
- When horizontal scaling needed (horizontal pods replica >1)
- When auto-scaling requirements emerge (CPU-based scaling)
- When 5+ ops team members ready (current: 0)
- When budget permits 20% ops overhead increase

**Tradeoffs:**
- MVP: Docker Compose = operational simplicity, single point of failure
- Phase 2: Kubernetes = operational complexity, multi-zone redundancy, auto-healing

**Monitoring:** Container uptime, restart frequency tracked; threshold for K8s migration = 2+ unplanned restarts/month

**Status:** Accepted (MVP Docker Compose, Phase 2 Kubernetes pre-planned)

---

### ADR-012: Persistent Object Storage - MinIO vs. NFS vs. Managed S3

**Decision:** MinIO for MVP (S3-compatible, self-hosted), NFS alternative for simplified deployments

**Context:**
- Nano ZIP files stored immutably
- Average Nano size: ~50MB (1-2GB library per creator / year)
- Initial upload volume: ~50-100 TB across MVP creators
- DSGVO compliance: EU data residency mandatory
- Backup strategy: Versioning + external backup required

**Alternatives Considered:**
1. **MinIO (Selected):** S3-compatible, self-hosted, versioning built-in, durability 99.999%
2. AWS S3: Managed, reliable, but vendor lock-in + cost (€200-500/month at scale)
3. NFS: Simple, but durability weaker, backup overhead higher
4. Managed SFTP: Outdated, limited scaling

**Justification:**
- MinIO S3-API compatibility enables future AWS migration (no code changes)
- Versioning: Automatic Nano version tracking without extra application logic
- Cost: €30-50/month self-hosted vs €200+ AWS S3 at scale
- Backup: Versioning provides point-in-time recovery

**Configuration (MVP Docker Compose):**
```yaml
minio:
  image: minio/minio
  volumes:
    - /data/minio:/data  # Persistent volume
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: SECURE_RANDOM
  command: server /data --console-address ":9001"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
```

**Backup Strategy:**
- Versioning: MinIO versioning enabled on all buckets
- External backup: Daily snapshots to Backblaze B2 (€0.006/GB cold storage)
- Recovery: object storage clone from backup bucket on disaster

**NFS Alternative (Simplified Deployment):**
```yaml
minio-alt:
  backend: NFS mount (simpler, but requires NAS appliance)
  trade-off: Lower cost hardware, but higher manual ops
```

**Tradeoffs:**
- Object storage abstraction (S3 API) vs file storage (NFS) trade-off
- MinIO operations overhead vs simpler NFS setup
- Durability: MinIO erasure coding vs NFS single-point-of-failure risk

**Monitoring:**
- Bucket usage % of available storage
- Versioning overhead (% unreclaimed deleted objects)
- Backup job success rate (must be 100%)

**Status:** Accepted (MinIO primary, NFS documented alternative)

---

### ADR-013: Log Aggregation & Monitoring - Prometheus/Loki vs. ELK Stack

**Decision:** Prometheus (metrics) + Loki (logs) + Grafana (visualization) - lighter-weight, cloud-native alternative to ELK

**Context:**
- Production logging required for DSGVO audit trails
- Real-time observability critical for incident response
- Cost efficiency: OSS stack must compete with ELK on value
- Team expertise: DevOps learning curve acceptable for Phase 1

**Alternatives Considered:**
1. **Prometheus + Loki + Grafana (Selected):** Cloud-native, modular, 50% less resource overhead than ELK
2. ELK Stack (Elasticsearch + Logstash + Kibana): Monolithic, powerful, but heavier resources
3. Datadog/NewRelic SaaS: Zero-ops, but €50-100k/year cost
4. CloudWatch/AWS native: Vendor lock-in, higher cost

**Justification:**
- Prometheus: Time-series DB optimized for metrics, not logs (separation of concerns)
- Loki: Log aggregation without full indexing overhead of ELK
- Grafana: Dashboard UI, alert management, label-based queries
- Efficiency: 60-70% resource savings vs ELK on same data volume

**Configuration (MVP Docker Compose):**
```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'

loki:
  image: grafana/loki
  ports: ["3100:3100"]
  volumes:
    - ./loki-config.yml:/etc/loki/local-config.yml
    - loki_data:/loki

grafana:
  image: grafana/grafana
  ports: ["3000:3000"]
  environment:
    GF_SECURITY_ADMIN_PASSWORD: SECURE_RANDOM
```

**Alerting & Tracing Integration:**
- Prometheus AlertManager: Rule-based alerting (13+ rules for app/DB/infrastructure)
- Jaeger/Zipkin: Distributed tracing (request flow visualization)
- Loki + Promtail: Log parsing with structured JSON format

**Tradeoffs:**
- Prometheus/Loki architecture is "learn one tool per layer" vs ELK "learn one tool":
  - (+) Flexibility to swap components (e.g., Loki → Elasticsearch later)
  - (-) More operational complexity (3 services vs 1 ELK)
- Resource usage: Prometheus+Loki = ~2GB RAM, ELK = ~4-6GB RAM

**Monitoring:**
- Prometheus scrape frequency health
- Loki ingestion rate (logs/sec)
- Grafana dashboard uptime (target 99.9%)

**Status:** Accepted (production-ready, Phase 1 enhancement: custom dashboards)

---

### ADR-014: Database Strategy - Self-Hosted PostgreSQL vs. Managed PostgreSQL

**Decision:** Managed PostgreSQL (DigitalOcean/Render) for MVP, with self-hosted option for Phase 2

**Context:**
- Financial data storage: ACID guarantees + audit trails mandatory (DSGVO Art. 12-22)
- MVP DevOps capacity: 0 DBAs, learning curve acceptable
- Cost parity: Managed (~€50-80/month) ≈ Self-hosted bare metal (€150-200/month total server cost)
- DSGVO compliance: EU data residency required

**Alternatives Considered:**
1. **Managed PostgreSQL (Selected for MVP):** DigitalOcean, Render, or similar
2. Self-hosted PostgreSQL: Full control, but requires 24/7 backup/monitoring ops
3. Managed PostgreSQL (AWS/DO/Render): Managed, but vendor lock-in, cost escalates at scale
4. MongoDB: NoSQL flexibility, but weaker ACID for financial data

**Justification:**
- Managed reduces operational burden: automated backups, updates, monitoring
- Cost equivalent: €50-80/month managed ≈ €150-200/month total bare metal (when counting server costs)
- ACID guarantees: PostgreSQL's ACID essential for transaction integrity (future payments)
- Flexibility: Can migrate to self-hosted later if cost pressures emerge

**MVP Configuration (Managed):**
```yaml
PostgreSQL 15 (Managed):
  Tier: Shared database tier (€15-25/month) or Dedicated (€50-80/month)
  Backup: Daily snapshots to external bucket (7-day retention)
  Monitoring: Integrated with Prometheus exporter
  Scaling: Vertical only in MVP (horizontal sharding Phase 2)
  SSL: Enforced TLS 1.2+ for all connections
```

**Self-Hosted Option (Documented for Phase 2):**
```yaml
PostgreSQL 15 (Self-Hosted):
  Hardware: VPS t3.xlarge (~€150-200/month)
  Replication: Primary + read-only standby
  Backup: pg_dump → MinIO (daily)
  Monitoring: Prometheus pg_exporter
  Recovery RTO: <1 hour manual
  Complexity: Requires DevOps expertise
```

**Data Residency (DSGVO Art. 44-49):**
- Managed: Choose EU datacenters (DigitalOcean Frankfurt, Render EU)
- Self-hosted: Full control over datacenter location
- Both: No data transfer outside EU unless explicit user consent

**Tradeoffs:**
- Managed: Less control, limited customization, but zero-ops backup/recovery
- Self-hosted: Full control, operational autonomy, but requires DevOps staffing

**Monitoring:**
- Backup success rate (must be 100%)
- Replication lag (if scaled to standby)
- Query performance: p99 latency < 500ms
- Connection pool exhaustion alerts

**Status:** Accepted (Managed PostgreSQL for MVP, self-hosted pre-scoped for Phase 2)

---

### ADR-015: OSS Infrastructure Complexity Risk Mitigation

**Decision:** Dedicated DevOps onboarding sprint (Sprint 0), runbook automation, and operational metrics

**Context:**
- Open-source stack trades convenience (AWS console) for control (infrastructure code)
- Team has no DevOps expertise yet (0 trained ops engineers)
- MVP quality requirements: 99.5% uptime, <2% error rate
- Timeline impact: +0 weeks (Docker Compose automation reduces net ops work)

**Risk Identified:**
- Configuration drift: 8+ services with interdependencies (Prometheus → Grafana, Loki → Jaeger)
- Backup failures: Manual scripts can fail silently without monitoring
- Scaling complexity: Docker Compose --scale requires manual resource planning
- Knowledge loss: Single DevOps engineer becomes single point of failure

**Mitigation Strategy:**

**Sprint 0 (Week 1-2) - DevOps Onboarding:**
- [ ] Deploy complete Docker Compose stack in staging (2d)
- [ ] Build healthcare-critical runbooks (API Down, DB Down, Disk Full) (2d)
- [ ] Automate backup validation (pg_dump → restore cycle) (1d)
- [ ] Setup Prometheus scraping + Grafana dashboards (1d)
- [ ] Configure AlertManager routing (critical→SMS, warning→email) (1d)
- [ ] Document disaster recovery procedure (RTO <1h, RPO <15m) (1d)
- [ ] Setup log shipping to external archive (MinIO + B2) (1d)

**Operational Runbooks (Automated):**
```bash
# Backup validation (daily cron job)
pg_dump -h $DB_HOST | gzip | aws s3 cp - s3://backups/daily-$(date).sql.gz  # S3-compatible CLI
pg_restore -d test-restore < backup.sql && psql -c "SELECT COUNT(*) FROM users" > /metrics/backup_valid

# Health check (every minute)
curl -f http://localhost:3000/health || page_ops_team.sh

# Disk space monitoring (hourly)
df -h /data | grep usage% && cleanup_old_logs.sh || page_ops_team.sh
```

**Staffing & Training:**
- Hire/train 0.5 FTE DevOps engineer (shared with Phase 1 scaling work)
- Cross-training: 1 developer learns backup/recovery (secondary)
- Knowledge transfer: All runbooks in version control + team wiki

**Monitoring Metrics:**
- Service availability (each service, target 99.5%)
- Backup job success rate (target 100%)
- Configuration drift detection (Terraform/Ansible checksums)
- Alert latency (critical alert → page within 5 minutes)

**Success Criteria:**
- Sprint 0 completion: Unplanned outage recovery <30 min via runbook execution
- Ongoing: Zero manual intervention required for >7 consecutive days (August, September)
- Phase 1 readiness: Can scale Docker Compose 2x without code changes

**Tradeoffs:**
- (+) Full infrastructure control, owner mindset, vendor independence
- (-) Higher operational burden initially, requires DevOps expertise investment

**Status:** Accepted (Sprint 0 DevOps onboarding planned, runbooks documented in 10_operations_observability.md)

---

## 4. Open Questions & Decisions Pending

| Question | Owner | Deadline | Impact |
|----------|-------|----------|--------|
| Revenue model (B2B2C vs B2B?) | Product | Pre-launch | Business viability |
| Organization feature (Phase 1 or deferred?) | Product | Sprint 3 | Must decide for API design |
| Localization (multilingual MVP or German only?) | Product | Sprint 1 | UI/DB schema |
| Mobile app (Web-only MVP or React Native?) | Product | Post-launch | Roadmap priority |
| Creator verification (automatic HR lookup or manual?) | Legal + Ops | Sprint 2 | Moderation load |
| Geographic expansion (EU/Global or Ger-only?) | Business | Post-MVP | Infrastructure |

---

## 5. Known Unknowns (Risks to Monitor)

1. **Creator Supply:**
   - Will 20+ creators sign up in MVP?
   - What incentivizes them?
   - Answer via: Q3 pilot, early partnerships

2. **Platform Unit Economics:**
   - Cost per DAU including infrastructure?
   - Revenue per DAU?
   - Break-even point?
   - Answer via: Q4 metrics, financial modeling

3. **Moderation At Scale:**
   - Can 1 moderator handle 100+ new Nanos/week?
   - Needs AI training data?
   - Answer via: Phase 1 staffing experiment

4. **Compliance Interpretation:**
   - Is marketplace liable for creator copyright violations?
   - What insurance needed?
   - Answer via: Early legal consultation

---

## 6. Lessons from Prototype (Prototyp Schwächen → Produktlösungen)

| Prototyp-Schwäche | Root Cause | Produktlösung |
|------------------|-----------|--------------|
| No password hashing | Oversight | bcrypt/Argon2 (mandatory) |
| No DSGVO compliance | Time constraint | Legal audit + tools (Privacy Module) |
| Chat not real-time | Polling design | WebSocket Phase 1 |
| No moderation | Not MVP scope | Full moderation workflow |
| Single-user only | Local development | Multi-user, cloud-hosted |
| No backups | No time | Automated daily snapshots |
| No analytics | Out of scope | Prometheus + Grafana dashboards |

---

## 7. Success Criteria & Metrics (First 12 Months)

### MVP Go-Live (Q3 2025)

```
✓ Security audit passed
✓ DSGVO compliance verified
✓ 50+ published Nanos
✓ 200+ registered users
✓ <2% error rate
✓ 99.5% uptime
✓ <1s mean response time
```

### Phase 1 (Q4 2025 - Q1 2026)

```
✓ 1000 DAU (Daily Active Users)
✓ 200+ creators
✓ 5000+ Nanos in catalog
✓ WeChat/WebSocket live
✓ Organizations feature launched
✓ Payment integration ready
```

### Phase 2+ (2026)

```
✓ 10k+ DAU
✓ Microservices migration complete
✓ Mobile app launched
✓ Payment system operational
✓ International expansion started
```

---

## Referenzen

- [00 — Executive Summary](./00_executive_summary.md) (Strategic Context)
- [06 — Security & Compliance](./06_security_compliance.md) (Risk Details)
- [10 — Operations & Observability](./10_operations_observability.md) (Risk Monitoring)
