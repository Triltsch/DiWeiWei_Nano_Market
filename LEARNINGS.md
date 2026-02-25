# Learnings - DiWeiWei Nano-Marktplatz Projekt

## Studienarbeit Analyse & PDF-Extraktion

### Context
Jana Bode's Studienarbeit "Entwicklung eines Prototyps für einen Nano-Marktplatz" (Januar 2025) dokumentiert die prototypische Umsetzung eines Marketplace-Systems für Nano-Learning-Einheiten im Projekt DiWeiWei.

### Key Learnings

#### 1. **Nano-Konzept & Learning-Modell**
- **Nano-Einheiten**: Kurze, in sich geschlossene digitale Lerneinheiten mit klarer thematischer Abgrenzung
- **Kompetenzstufen**: 3 Ebenen (Foundation/Intermediate/Advanced) definieren Lerntiefe
- **Module & Schulungen**: Nanos kombinieren zu Modulen, Module zu Schulungen für ganzheitliche Themenbereiche
- **Learning**: Modularer Aufbau ermöglicht adaptive, selbstbestimmte Lernpfade

#### 2. **Marketplace-Architektur (Studienarbeit vs. Production)**

**Prototype (Study)**:
- Python 3.13.1 mit Solara Framework (Full-Stack)
- MySQL mit XamPP für lokale Entwicklung
- **SICHERHEITSLÜCKEN IDENTIFIZIERT**:
  - ❌ Keine Password-Hashing (KRITISCH)
  - ❌ Kein TLS für Chat-Nachrichten
  - ❌ Keine DSGVO-Implementierung
  - ❌ Keine SQL-Injection-Protection
  - ❌ Chat via HTTP-Polling, nicht WebSocket

**Production Plan**:
- FastAPI Backend (statt Solara)
- PostgreSQL Aurora RDS (statt MySQL) → Gewählt wegen:
  - JSONB für flexible Datenstrukturen
  - German Full-Text-Search (FTS)
  - Superior ACID-Garantien
  - Bessere Indexing-Optionen
- AWS Cloud-Native: ECS, RDS, S3, ElastiCache, Elasticsearch

#### 3. **Business Model: Tausch vs. Kaufmodell**

**Evaluated Concepts**:
1. Fixed-Price (wie Amazon) → ❌ Keine Interaktion
2. Negotiable-Price (wie Klein-Anzeigen) → ⚠️ Indirekte Kommunikation
3. **Barter Model** (GEWÄHLT) ✅:
   - Nanos werden OHNE festen Preis hochgeladen
   - Direkter Chat zwischen Creator und Consumer
   - Nanos werden getauscht (z.B. mein Nano für dein Nano)
   - **Learning**: Kommunikation > Transaktion für regionalen Marketplace

#### 4. **Anforderungen-Extraktion: 99+ Requirements**

**Kategorisiert als**:
- MUSS (27): Must-have features (Login, Upload, Search, Quality Controls)
- SOLL (35): Should-have features (Ratings, Comments, Moderation)
- KANN (37): Nice-to-have features (AI recommendations, Analytics)

**Professionalisierungs-Gaps Identifiziert**:
- 23 Security/Compliance Requirements missing in Prototype
- Moderation Workflow nicht implementiert
- DSGVO Data Export/Anonymization fehlt
- 2FA/Password-Strength nicht vorhanden

#### 5. **Domain Model & Data Normalization**

**11 Core Entities**:
1. USER → 6 attributes + roles (Creator, Consumer, Admin, Moderator)
2. ORGANIZATION → Multi-Org support (Phase 1)
3. NANO → Content unit (18 attributes: title, duration, status, file_path, license, etc.)
4. NANO_VERSION → Immutable versioning
5. NANO_CATEGORY_ASSIGNMENT → N:M relationship (max 5 per nano)
6. RATING → 1-5 star system
7. CHAT_SESSION & CHAT_MESSAGE → Encryption ready
8. FAVORITE & SAVED_LIST → User personalization
9. AUDIT_LOG → DSGVO compliance (7-year retention)
10. MODERATION_FLAG → Content review workflow

**Normalization Decision**: 3NF with strategic denormalization:
- `average_rating` cached (trigger-based updates)
- `download_count` aggregated nightly
- **Why**: Performance optimization vs. query complexity trade-off

#### 6. **Architecture Pattern: Monolith → Microservices**

**MVP Decision**: Modular Monolith (not premature microservices)
- **8-week sprint** demands tight coupling
- **150 PT sustainability** limit
- **10 well-defined modules** enable clean service extraction later

**Modules**:
1. Identity & Auth (JWT, 2FA)
2. Nano Catalog (Upload, CRUD, Versioning)
3. Search & Discovery (FTS, Faceting)
4. Feedback (Ratings, Comments, Moderation)
5. Messaging (Chat, Encryption)
6. Profiles & Organizations
7. Favorites & Lists
8. Moderation & Abuse
9. Audit & DSGVO
10. Analytics

**Phase 2 Migration Path**:
- Auth → Keycloak microservice
- Chat → Node.js (WebSocket native)
- Search → Elasticsearch cluster
- Keep Content & Profiles in monolith initially

#### 7. **Technology Stack Decisions**

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend Framework** | FastAPI | Async, type-safe, auto-docs, AWS-ready |
| **Frontend** | React 18+ | Industry standard, component reusability |
| **Database Primary** | PostgreSQL Aurora | JSONB, FTS, ACID, AWS RDS managed |
| **Search Engine** | AWS OpenSearch | German tokenizer, faceting, managed |
| **Object Storage** | S3 | Nano ZIPs, avatars, immutable audit logs |
| **Session Cache** | ElastiCache (Redis) | HttpOnly cookies, 30-60min TTL |
| **Infrastructure** | AWS ECS + ALB | Load balancing, auto-scaling, managed |
| **Real-time Chat** | Polling (MVP) → WebSocket Phase 1 | Simplified MVP, upgrade path clear |

#### 8. **DSGVO Implementation Strategy**

**Articles Mapped**:
- Art. 6 (Lawfulness) → Consent banner + purpose limitation
- Art. 12-22 (Data Subject Rights):
  - **Art. 15**: Data export via "Meine Daten" button → JSON/CSV
  - **Art. 17**: Right to erasure → Soft-delete with pseudonymization
  - **Art. 20**: Data portability → CSV export format standardized
  - **Art. 21**: Opt-out → Newsletter unsubscribe + communication preferences
- **Retention**: Audit logs 7-year (DSGVO + tax law)
- **Pre-Launch Gates**: 
  - ✓ Security audit passed
  - ✓ DSGVO audit passed
  - ✓ Penetration test passed

#### 9. **Risk Profile & Mitigations**

**Critical Risks**:
1. DSGVO Violation (40% prob) → Pre-launch legal audit
2. Chat Privacy Leak (35% prob) → TLS MVP, E2E Phase 2
3. Data Breach (20% prob) → AWS KMS, audit logging, incident runbook
4. SQL Injection (15% prob) → ORM (SQLAlchemy), prepared statements

**Business Risks**:
- Marketplace Coldstart (70% prob) → Seed content + early access program
- Creator/Consumer Imbalance (60% prob) → Asymmetric launch strategy
- Moderation Overhead (50% prob) → AI content filter Phase 1

#### 10. **MVP Scope & Budget**

**8-Week Sprint, 150 PT, 180k€**:
- 7 Epics: Auth (2w), Nanos (3w), Search (2w), Feedback (1w), Chat (1w), Moderation (1w), DevOps (2w, parallel)
- Team: 1 Senior Dev + 1 Full-Stack + 0.5 DevOps + 0.5 QA + 1 PM (5 FTE)
- Go-Live Target: Q3 2025
- Post-MVP: 180k€/year for scaling

#### 11. **Testing Strategy: Pyramid Approach**

**Coverage Targets**:
- **Unit** (70%): Password hashing, JWT validation, search ranking
- **Integration** (15%): API→Service→Repo, mocked DB fixtures
- **E2E** (5%): Playwright/Selenium, staging environment
- **Security** (10%): OWASP Top 10, DSGVO compliance, penetration testing
- **Performance** (Locust): 1000 concurrent users, p95 <1s latency

**CI/CD**: GitHub Actions with lint (flake8), test (pytest), security (SonarQube) gates

#### 12. **Deployment & Operations**

**Monitoring Stack**:
- CloudWatch (metrics), CloudWatch Logs (structured JSON), X-Ray (traces), SNS (alerts)
- **SLOs**: 99.95% uptime, p95 <1s latency, 5xx <0.5%
- **Capacity**: 1k DAU = 2 ECS tasks, 5k DAU = 3-4 tasks, 10k DAU = 5-8 tasks

**Incident Response**: SEV-1 (page on-call), SEV-2 (normal response), post-mortem 24h

**Backup/DR**: RTO <1h, RPO <15min, monthly DR drills

#### 13. **Architectural Decisions (9 ADRs)**

**Key Decisions**:
- ADR-001: Monolith (MVP speed) vs Microservices (later)
- ADR-002: PostgreSQL (FTS, JSONB) vs MySQL (simplicity)
- ADR-003: React (market fit) vs Vue (lighter)
- ADR-004: JWT+Refresh (stateless) vs Database sessions
- ADR-005: S3 (scalable) vs BLOB (simpler)
- ADR-006: Elasticsearch (rich queries) vs DB full-text
- ADR-007: Polling (MVP) vs WebSocket (Phase 1)
- ADR-008: Payment (defer Phase 2) vs Tausch-model MVP
- ADR-009: Chat TLS (MVP) vs E2E (Phase 2)

#### 14. **PDF Extraction & Study Integration**

**Process**:
1. PDF Study (114 pages) → pdfplumber extraction
2. Structured analysis → 570-line detailed document
3. Requirements professionalization → 99 mapped requirements
4. Planning documents → 13-file suite covering all aspects

**Learning**: Programmatic PDF extraction enables systematic requirements capture from academic research.

#### 15. **Professionalization Vectors**

**Gap Analysis - Prototype → Production**:

| Area | Prototype | Production |
|------|-----------|-----------|
| Password Storage | ❌ Plain text | ✓ Argon2 (12 rounds) |
| Chat Encryption | ❌ HTTP polling | ✓ TLS MVP, E2E Phase 1 |
| DSGVO | ❌ None | ✓ Art. 6, 12-22, 21 |
| SQL Injection | ❌ No protection | ✓ ORM + Prepared statements |
| Moderation | ❌ Comments only | ✓ Review workflow + flags |
| Monitoring | ❌ Console logs | ✓ CloudWatch + SLOs |
| Testing | ❌ Manual | ✓ 80%+ coverage + CI/CD |
| Deployment | ❌ Local XamPP | ✓ AWS ECS multi-AZ |
| Scalability | ❌ Single machine | ✓ Auto-scaling 1-10k DAU |
| Audit Trail | ❌ None | ✓ Immutable 7-year retention |

---

## Meta-Learnings for Future Projects

1. **Prototype-to-Production Gap**: Academic prototypes require 15-20x effort for production hardening
2. **Modularity Early**: Defining 10 modules in MVP enables cleaner Phase 2 microservice migration
3. **PDF as Requirements Source**: Systematic PDF analysis beats manual reading; enables requirements traceability
4. **Regional Marketplace Dynamics**: Barter models suit B2B regional ecosystems; eCommerce patterns don't translate directly
5. **Security is Foundational**: Plan DSGVO/encryption architecturally; retrofitting is exponentially harder

---

**Document Updated**: 2026-02-24
**Status**: Initial Planning Complete → Ready for Engineering Kickoff

