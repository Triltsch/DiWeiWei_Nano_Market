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
| **AWS ist kosteneffizient** | MITTEL | Migrate to on-premise if costs explode |
| **PostgreSQL skaliert zu 10k+ DAU** | MITTEL | Sharding or read-replicas |
| **FastAPI kann 1000 RPS handhaben** | MITTEL | Upgrade zu Node.js / Go if needed |
| **Elasticsearch ist "good enough"** | GERING | Use Solr or Algolia as SaaS |

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

**Decision:** PostgreSQL + AWS RDS Aurora

**Evaluated Options:**
1. **PostgreSQL Aurora (Selected):** Better JSON support, strong ACID, superior indexing
2. MySQL: Simpler, wider adoption, but weaker JSON/Full-text search
3. DynamoDB: NoSQL, good for scale, but complex queries hard
4. MongoDB: Flexible schema, but consistency/ACID guarantees weaker

**Decision Factors:**
- JSONB support for flexible metadata (future)
- Full-text search with German tokenizer
- ACID guarantees critical for financial data (future)
- AWS managed simplifies operations

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
- Access Token: 15 min expiry, HttpOnly cookie or localStorage
- Refresh Token: 7 day expiry, HttpOnly secure cookie only
- Claim: {user_id, email, role, exp, iat}

---

### ADR-005: Nano Storage Format

**Decision:** ZIP files in S3 + Metadata in RDS

**Alternatives:**
1. **ZIP in S3 (Selected):** Immutable, versioned, cost-efficient, follows prototype
2. Unzipped in S3: More granular, but complex deduplication
3. Database BLOB: Simple, but scales poorly
4. Git-like versioning (gitsync): Complex, overkill

**Rationale:** ZIP matches creator's mental model, easy to export/import

**Versioning:** Via nano_versions table + S3 versioning

---

### ADR-006: Search Backend

**Decision:** Elasticsearch (or AWS OpenSearch)

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
| No analytics | Out of scope | CloudWatch + custom dashboards |

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
