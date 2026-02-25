# 04 — Domänenmodell & Datenmodell

---

## 1. Überblick Domäne

Der Nano-Marktplatz ist ein **Two-Sided-Marketplace** mit Fokus auf Content-Curation und direkte Kommunikation. Die Kerndomäne besteht aus:

- **Users/Identities:** Authentifizierung, Profile, Rollen
- **Nanos:** Lerneinheiten mit Metadaten und Versionierung
- **Discovery:** Suche, Filter, Kategorisierung
- **Feedback:** Ratings, Kommentare, Moderation
- **Messaging:** Chat zwischen Creator und Consumer
- **Transactions (zukünftig):** Lizenzvereinbarungen, Payments

---

## 2. Entity-Relationship-Modell (ERM)

### 2.1 Entität: USER

```
USER
├─ ID (PK, UUID)
├─ Email (Unique)
├─ Username (Unique)
├─ PasswordHash (Bcrypt/Argon2)
├─ FirstName
├─ LastName
├─ ProfileAvatar (BlobRef zu object storage)
├─ Bio (nullable, 500 chars)
├─ Company (nullable)
├─ JobTitle (nullable)
├─ Phone (nullable, encrypted)
├─ CreatedAt (Timestamp)
├─ UpdatedAt (Timestamp)
├─ LastLogin (Timestamp, nullable)
├─ Status (enum: active, inactive, suspended, deleted)
├─ EmailVerified (Boolean)
├─ VerifiedAt (Timestamp, nullable)
├─ PreferredLanguage (defaults: de)
└─ Role (enum: admin, creator, consumer, moderator)
```

**Normalisierung:** 1NF ✓ (atomic Attributes)

**Indizes:**
- Email (UNIQUE)
- Username (UNIQUE)
- Status (for query filtering)
- CreatedAt (for time-series queries)

---

### 2.2 Entität: ORGANIZATION (Future: Phase 1)

```
ORGANIZATION
├─ ID (PK, UUID)
├─ Name (Unique)
├─ Email (contact)
├─ Website (nullable)
├─ RegistrationNumber (HR, UID - nullable)
├─ VerificationStatus (enum: unverified, pending, verified)
├─ VerifiedAt (Timestamp, nullable)
├─ Logo (BlobRef)
├─ Description
├─ CreatedAt
├─ UpdatedAt
└─ Status (active, inactive, suspended)
```

**Relation:** User:Organization = n:m via `USER_ORGANIZATION_ROLE`
```
USER_ORGANIZATION_ROLE
├─ ID (PK)
├─ User_ID (FK → USER)
├─ Organization_ID (FK → ORGANIZATION)
├─ Role (enum: admin, editor, viewer)
└─ JoinedAt
```

---

### 2.3 Entität: NANO

```
NANO
├─ ID (PK, UUID)
├─ Creator_ID (FK → USER, not null)
├─ Organization_ID (FK → ORGANIZATION, nullable, Phase 1)
├─ Title (not null)
├─ Description (max 1000 chars)
├─ Duration_Minutes (int, >0)
├─ CompetencyLevel (enum: 1, 2, 3)  // didaktische Stufen
├─ Language (enum: de, en, ...)
├─ Format (enum: video, text, quiz, interactive, mixed)
├─ Status (enum: draft, pending_review, published, archived, deleted)
├─ PrivacyLevel (enum: public, organization_only, private) // Phase 1
├─ Version (semver: "1.0.0")
├─ ThumbnailUrl (BlobRef zu object storage)
├─ FileStoragePath (Object storage URI zur ZIP)
├─ License (enum: CC-BY, CC-BY-SA, CC0, Proprietary)
├─ UploadedAt (Timestamp)
├─ PublishedAt (Timestamp, nullable)
├─ ArchivedAt (Timestamp, nullable)
├─ UpdatedAt (Timestamp)
├─ DownloadCount (int, cache field)
├─ AverageRating (decimal 0-5, denormalisiert Cache) // note: typo fixed from 'averange'
├─ RatingCount (int, cache)
└─ Meta_SeoKeywords (text, nullable) // Phase 1
```

**Normalisierung:** Denormalisierung (DownloadCount, AverageRating) für Performance, aber mit periodischem Sync.

**Indizes:**
- Creator_ID
- Status (für Publishing-Workflow)
- Language
- CompetencyLevel
- PublishedAt (für Trending)
- AverageRating (für Ranking)

---

### 2.4 Entität: NANO_VERSION (Audit Trail)

```
NANO_VERSION  // Immutable ledger
├─ ID (PK, UUID)
├─ Nano_ID (FK → NANO)
├─ Version (semver: "1.0.0")
├─ ChangeLog (text, was sich geändert hat)
├─ CreatedBy_User_ID (FK → USER)
├─ CreatedAt (Timestamp)
├─ FileStoragePath (Object storage)
└─ Status (published, archived)
```

**Nutzungsfall:** Creator kann frühere Versionen abrufen/vergleichen.

---

### 2.5 Entität: NANO_TAGS / CATEGORY

```
NANO_CATEGORY_ASSIGNMENT
├─ ID (PK)
├─ Nano_ID (FK → NANO)
├─ Category_ID (FK → CATEGORY)
└─ Rank (int, für Ordering)

CATEGORY  // Dictionary/Dimension-Table
├─ ID (PK, UUID)
├─ Name (unique)
├─ Description
├─ ParentCategory_ID (nullable, für Hierarchie)
├─ IconUrl (nullable)
└─ Status (active, inactive)
```

**Beispiele:**
```
Business Skills
├─ Excel
├─ PowerPoint
├─ Kommunikation
└─ Projektmanagement

IT/Tech
├─ Python
├─ Cloud Architecture
└─ Data Science
```

**Constraint:** Max 5 Kategorien pro Nano.

---

### 2.6 Entität: RATING / REVIEW

```
RATING
├─ ID (PK, UUID)
├─ Nano_ID (FK → NANO)
├─ Rater_ID (FK → USER)
├─ Score (int: 1-5)
├─ Comment (text, nullable, max 500 chars)
├─ CreatedAt (Timestamp)
├─ UpdatedAt (Timestamp)
├─ Moderator_ApprovedAt (Timestamp, nullable)
├─ Moderator_ApprovedBy_ID (FK → USER, nullable)
├─ Status (enum: pending_moderation, approved, rejected) // Phase 1
└─ Helpful Count (int, others found useful)
```

**Constraint:** UNIQUE(Nano_ID, Rater_ID) - ein User pro Nano nur eine Bewertung

**Indizes:**
- (Nano_ID, CreatedAt DESC) für schnelle Sortierung

---

### 2.7 Entität: CHAT_SESSION / MESSAGE

```
CHAT_SESSION
├─ ID (PK, UUID)
├─ Nano_ID (FK → NANO)
├─ Initiator_ID (FK → USER) // Consumer
├─ Creator_ID (FK → USER)  // Anbieter
├─ CreatedAt (Timestamp)
├─ LastMessageAt (Timestamp)
├─ Status (enum: active, archived, reported)
└─ ArchivedAt (nullable)

CHAT_MESSAGE
├─ ID (PK, UUID)
├─ ChatSession_ID (FK → CHAT_SESSION)
├─ From_User_ID (FK → USER)
├─ To_User_ID (FK → USER)
├─ MessageText (text, max 1000 chars)
├─ EncryptionType (enum: none, TLS, E2E) // E2E future
├─ CreatedAt (Timestamp)
├─ ReadAt (Timestamp, nullable)
├─ Status (enum: sent, delivered, failed)
└─ FlaggedAt (nullable, Spam-Flag)
```

**Normalisierung:** CHAT_SESSION redundiert (Creator_ID abrufbar via NANO), aber für Query-Effizienz nötig.

**Indizes:**
- (ChatSession_ID, CreatedAt)
- (To_User_ID, ReadAt) für Unread-Count

---

### 2.8 Entität: FAVORITE

```
FAVORITE
├─ ID (PK)
├─ User_ID (FK → USER)
├─ Nano_ID (FK → NANO)
├─ SavedList_ID (FK → SAVED_LIST, nullable) // Phase 1
├─ CreatedAt (Timestamp)
└─ Status (enum: active, removed)
```

**Constraint:** UNIQUE(User_ID, Nano_ID)

---

### 2.9 Entität: SAVED_LIST (Phase 1)

```
SAVED_LIST
├─ ID (PK, UUID)
├─ User_ID (FK → USER)
├─ Name (string)
├─ Description (nullable)
├─ IsPublic (boolean)
├─ CreatedAt
└─ UpdatedAt

SAVED_LIST_ITEM
├─ ID (PK)
├─ SavedList_ID (FK → SAVED_LIST)
├─ Nano_ID (FK → NANO)
└─ Rank (int, Ordering)
```

---

### 2.10 Entität: AUDIT_LOG (Compliance)

```
AUDIT_LOG
├─ ID (PK, UUID)
├─ ActionType (enum: login, upload, download, delete, moderation, dsgvo_request)
├─ Actor_ID (FK → USER)
├─ TargetType (enum: user, nano, chat, comment)
├─ TargetID (UUID)
├─ Details (JSON, kontextabhängig)
├─ IPAddress (anonymized)
├─ UserAgent (device info)
├─ CreatedAt (Timestamp, immutable)
└─ Status (enum: success, failure)
```

**Constraint:** Immutable (no updates). Retention Policy: 7 Jahre (DSGVO).

---

### 2.11 Entität: MODERATION_FLAG (Phase 1)

```
MODERATION_FLAG
├─ ID (PK, UUID)
├─ FlaggedContentType (enum: nano, comment, chat_message)
├─ FlaggedContentID (UUID)
├─ FlaggedBy_ID (FK → USER)
├─ CreatorNano_ID (FK → NANO, nullable, join-path)
├─ Reason (enum: copyright, spam, inappropriate, other)
├─ Description (text, optional)
├─ Status (enum: pending, investigating, resolved, dismissed)
├─ ReviewedBy_ID (FK → USER, nullable)
├─ Resolution (text, nullable)
├─ CreatedAt
├─ ResolvedAt (nullable)
└─ Action (enum: no_action, warning, archive, delete)
```

---

## 3. Dataflow-Diagramm (Übersicht)

```
┌──────────────┐
│   CLIENT     │
│  Browser UI  │
└───────┬──────┘
        │ HTTPS/TLS
        ↓
┌──────────────────────────┐
│  REST API Layer          │
│  ├─ Auth Endpoints       │
│  ├─ Nano Endpoints       │
│  ├─ Search Endpoints     │
│  ├─ Chat Endpoints       │
│  ├─ Rating Endpoints     │
│  └─ Admin Endpoints      │
└───────┬──────────────────┘
        │
        ├─────────────────→ ┌─────────────────┐
        │                  │  SESSION CACHE  │
        │                  │  (Redis)        │
        │                  └─────────────────┘
        │
        ├─────────────────→ ┌──────────────────────┐
        │                  │   SEARCH INDEX       │
        │                  │   (Elasticsearch)    │
        │                  └──────────────────────┘
        │
        ↓
┌──────────────────────────┐
│   PostgreSQL / MySQL     │
│   (Relational Database)  │
│   ├─ Users              │
│   ├─ Nanos              │
│   ├─ Ratings            │
│   ├─ Chat               │
│   ├─ Audit              │
│   └─ Settings           │
└──────┬────────┬──────────┘
       │        │
      │        └──────→ ┌──────────────────┐
      │                │  Automated       │
      │                │  Backups (MinIO) │
      │                └──────────────────┘
       │
       └──────────────→ ┌──────────────────┐
                       │  Object Storage  │
                       │  (MinIO)         │
                       │  ├─ Nanos ZIPs  │
                       │  ├─ Avatars     │
                       │  ├─ Thumbnails  │
                       │  └─ Audit Logs  │
                       └──────────────────┘
```

---

## 4. Domain-Events (Event Sourcing Ready)

Die Plattform kann zukünftig Event-basiert (Event Sourcing) erweitert werden:

```
Events:
- UserRegistered(email, username)
- UserEmailVerified(user_id)
- NanoUploaded(nano_id, creator_id, title)
- NanoPublished(nano_id, published_by)
- NanoArchived(nano_id, reason)
- RatingSubmitted(nano_id, score)
- ChatInitiated(chat_session_id, initiator_id, creator_id)
- ChatMessageSent(chat_message_id, from_user_id)
- ContentFlagged(flag_id, reason)
- ModerationDecision(flag_id, action)
- UserDataRequested(user_id, request_type: export/delete)
- UserAnonymized(user_id)
```

**Use Case:** Für Analytics, Audit-Trail, oder Microservice-Integration (Phase 2).

---

## 5. Datenklassifizierung & Sensitivity

| Datenklasse | Attribut | Sensitivität | Handling |
|-------------|----------|--------------|----------|
| **Public** | Nano Title, Description, Rating avg | Öffentlich | CDN-cachebar |
| **Internal** | Nano Download Count, Creator Name | Internal | nur für authentifizierte |
| **Sensitive** | Email, Phone (encrypted) | PII | Verschlüsselt at-rest |
| **Highly Sensitive** | PasswordHash, Payment Data | PII/PCI | Encrypted + HSM (future) |
| **Compliance** | Audit Logs, DSGVO Requests | Regulatory | Immutable, 7 Jahre retention |

---

## 6. Datenbankwahl: PostgreSQL vs MySQL vs Hybrid

### Trade-Off-Analyse

| Aspekt | PostgreSQL | MySQL | Bewertung |
|--------|-----------|-------|-----------|
| **ACID Compliance** | ✅ Erstklassig | ✅ Gut | PostgreSQL +5 |
| **JSON/Document Support** | ✅ JSONB native | 🔵 JSON (limited) | PostgreSQL +3 |
| **Full-Text Search** | ✅ Gut | 🟡 Mittel | PostgreSQL +2 |
| **Skalierung (Sharding)** | 🔵 Manual | ✅ Einfacher | MySQL +3 |
| **Replication** | ✅ Cascading | ✅ Linear | Tie |
| **Managed Offering** | ✅ Many | ✅ Many | Tie |
| **Community** | ✅ Enterprise | ✅ Weit verbreitet | MySQL +2 |

**Empfehlung für MVP:** **PostgreSQL (managed oder self-hosted)** (Enterprise-ready, JSONB für flexible Fields, erstklassige Indizierung).

### Schema für PostgreSQL

```sql
-- Primary Tables
CREATE TABLE "users" (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  INDEX (email),
  INDEX (status)
);

CREATE TABLE "nanos" (
  id UUID PRIMARY KEY,
  creator_id UUID REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  duration_minutes INT CHECK (duration_minutes > 0),
  competency_level INT CHECK (competency_level IN (1,2,3)),
  status VARCHAR(50) DEFAULT 'draft',
  published_at TIMESTAMP,
  averange_rating NUMERIC(3,2) GENERATED ALWAYS AS (...)
);

-- Indexes
CREATE INDEX idx_nanos_creator ON nanos(creator_id);
CREATE INDEX idx_nanos_status ON nanos(status);
CREATE INDEX idx_nanos_published_rating ON nanos(published_at DESC, average_rating DESC);

-- Full-Text Search
CREATE INDEX idx_nanos_ftx ON nanos USING GIN(to_tsvector('german', title || ' ' || description));
```

---

## 7. Normalisierungsgrad

### Normalisierungsstatus

- **1NF:** ✅ Alle Werte atomar
- **2NF:** ✅ Alle nicht-Schlüssel-Attribute sind vollständig abhängig vom PK
- **3NF:** ✅ Keine transitiven Abhängigkeiten
- **BCNF:** 🔵 Nicht notwendig für MVP

### Denormalisierungen (Performance-bewusst)

```
NANO.average_rating  // Denom. aus Rating-Aggregation
                      // Sync via Trigger oder Batch-Job
                      
NANO.download_count  // Cache aus Log-Analyse
                      // Periodische Update (z.B. nachts)
                      
CHAT_SESSION.lastMessageAt // Denom. zur schnellen Sortierung
```

**Strategie:** Schreib-pessimistisch (Update beim Upload), Lese-optimistisch (aggregate Queries cached).

---

## Referenzen

- [02 — Fachliche Anforderungen](./02_requirements.md) (Datenscope)
- [05 — Systemarchitektur](./05_system_architecture.md) (DB-Deployment)
- [06 — Security & Compliance](./06_security_compliance.md) (Verschlüsselung)
