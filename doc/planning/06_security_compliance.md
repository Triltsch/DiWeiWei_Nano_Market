# 06 — Security & Compliance

---

## 1. Sicherheitsübersicht

Die Plattform muss mehreren gesetzlichen und industriellen Standards entsprechen, insbesondere DSGVO, deutschen Datenschutzgesetzen und Best Practices für EdTech.

---

## 2. DSGVO (Datenschutzgrundverordnung)

### 2.1 Rechtsgrundlagen (Art. 6 DSGVO)

| Verarbeitung | Artikel | Implementierung |
|--------------|---------|-----------------|
| Registrierung | Art. 6 (1a) Einwilligung | Opt-in Checkbox + Datenschutzerklärung |
| Kontoverifikation | Art. 6 (1b) Vertrag | Notwendig für Service-Erbringung |
| Audit Logging | Art. 6 (1f) Berechtigtes Interesse | Sicherheit, Betrugsprävention |
| Compliance-Anfragen | Art. 12-22 | Admin-Interface für Betroffenenrechte |

### 2.2 Betroffenenrechte (Arts. 12-22)

| Recht | Implementierung | Deadline |
|-------|-----------------|----------|
| **Art. 15: Auskunft** | "Meine Daten" Export-Button im Profil | 30 Tage |
| **Art. 16: Berichtigung** | Edit-Funktionen im Profil + E-Mail verifiziert | Sofort |
| **Art. 17: Vergessenwerden** | Anonymisierung + Account-Deaktivierung. Nanos bleiben (rechtmäßige Inhalte). | 30 Tage |
| **Art. 18: Einschränkung** | Account kann "suspended" werden (nicht gelöscht, aber inaktiv) | Sofort |
| **Art. 20: Datenportabilität** | JSON/CSV Export aller Nutzer-Daten | 30 Tage |
| **Art. 21: Widerspruch** | Opt-out für Marketing-E-Mails; Recht auf Datenschutz vs. Plattform-Betrieb | Sofort |

### 2.3 Datenschutzerklärung

**Anforderungen (Art. 13 DSGVO):**
- Name des Verantwortlichen (Plattformbetreiber)
- Kontaktdetails des Datenschutzbeauftragten (falls erforderlich)
- Zweck der Verarbeitung
- Rechtsgrundlage
- Empfänger der Daten (z.B. Hosting/Storage Provider, externe Moderatoren)
- Aufbewahrungsdauer
- Betroffenenrechte
- Recht auf Beschwerde bei Aufsichtbehörde

**Speicherort:** Öffentlich zugänglich auf /datenschutz oder /privacy

### 2.4 Datenminimierung

**Daten, die NICHT erforderlich sind, werden nicht erhoben:**
- ❌ Browsinghistorie (außer für Session Management)
- ❌ Standortdaten (Geo-IP nur für CDN-Zwecke)
- ❌ Biometrische Daten
- ❌ Religiöse/Politische Überzeugungen

### 2.5 Retention & Löschung

```
User-Daten:
- Account aktiv: Speichern solange aktiv
- Account gelöscht: 
  - Profile: sofort anonymisieren
  - Chat-Nachrichten: anonymisieren oder 6 Monate speichern
  - Audit-Logs: 7 Jahre speichern (gesetzlich erforderlich)

Content (Nanos):
- Veröffentlichte Nanos: Speichern solange Creator aktiv
- Archivierte: 2 Jahre speichern (vor vollständiger Löschung)

Payment / Transactional (Phase 2):
- Rechnung: 10 Jahre (steuerliche Verpflichtung)
```

### 2.6 Data Processing Agreement (DPA)

**Erforderlich mit:**
- Hosting/Storage Provider (EU)
- External Moderators (falls Daten gezeigt)
- Email Provider (if used)

**Inhalte:**
- Art der Verarbeitung
- Kategorien von Daten
- Umfang und Dauer
- Sicherheitsmaßnahmen
- Subprozessoren

---

## 3. Authentifizierung & Autorisierung

### 3.1 Password Security

**Anforderungen:**
- ✅ Hashing: bcrypt oder Argon2 (nicht MD5/SHA1)
- ✅ Minimum 8 Zeichen
- ✅ Komplexitätsanforderung (mind. 1 Upper + 1 Digit + 1 Special)
- ✅ No Common Passwords (check against breached list: https://haveibeenpwned.com/)
- ✅ Password Reset via secure E-Mail-Link (Token 1h gültig)

**Implementierung (bcrypt mit Python):**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Currently recommended
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 3.2 Session Management

**Token-basiert (JWT):**
```
Access Token:
- Typ: JWT (HS256)
- Gültigkeitsdauer: 15 Minuten
- Claims: user_id, role, exp

Refresh Token:
- Typ: Opaque Token (random string)
- Gültigkeitsdauer: 7 Tage
- Gespeichert in HTTP-Only Cookie oder Secure Storage

  Flow:
  1. User: login → get Access + Refresh Token
  2. Request with Access Token
  3. Token expires → User: refresh-endpoint with Refresh Token
  4. Server: Validates, issues new Access Token
  5. Logout: Delete Refresh Token
```

### 3.3 Multi-Factor Authentication (2FA, Phase 1)

**MVP:** Optional 2FA für Admins  
**Phase 1:** Verfügbar für alle Nutzer

```
Method: TOTP (Time-based One-Time Password)
Provider: Google Authenticator, Authy, Microsoft Authenticator

Setup:
1. User: Enable 2FA in Settings
2. Server: Generate TOTP Secret (Base32)
3. User: Scan QR-Code with Authenticator App
4. User: Enter 6-digit Code to Verify
5. Server: Store Secret + Backup Codes

Login with 2FA:
1. User: email + password
2. Server: Prompt for 2FA code
3. User: Enter code from Authenticator
4. Server: Verify TOTP (time window ±30s)
5. Issue Auth Tokens
```

---

## 4. Transport Security

### 4.1 TLS/SSL

**Anforderungen:**
- ✅ HTTPS Only (HTTP redirection zu HTTPS)
- ✅ TLS 1.2+ (no SSLv3, TLSv1.0, TLSv1.1)
- ✅ Zertifikat von anerkannter CA (z.B. Let's Encrypt)
- ✅ Zertifikat: Minimum 2048-bit RSA oder 256-bit ECDSA
- ✅ HSTS Header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

**Open-Source Setup:**
```
Nginx/Caddy → Let's Encrypt (ACME)
  Auto-renewal via certbot or built-in Caddy
  Automatic deployment to reverse proxy
  SSLPolicy: TLS 1.2+ (modern ciphers)
```

### 4.2 CORS (Cross-Origin Resource Sharing)

**Allowed Origins:**
```
Development: http://localhost:3000
Production: https://nano-marketplace.de, https://app.nano-marketplace.de

Not Allowed Wildcards (*)
```

---

## 5. Datenverschlüsselung

### 5.1 At-Rest Encryption

**Datenbank (PostgreSQL, Managed oder Self-hosted):**
```
At-Rest Encryption:
- Managed: Provider-managed disk encryption (EU region)
- Self-hosted: LUKS/dm-crypt on database volume

Backup Encryption:
- Encrypted snapshots or pg_dump with GPG
```

**Object Storage (MinIO, S3-compatible):**
```
Encryption: Server-Side Encryption (SSE-S3 or SSE-C)
Versioning: Enabled (can restore old Nanos)
```

**Cached Data (Redis):**
```
Encryption in Transit: TLS
Data: Session tokens, not user PII
  (if needed: Redis TLS + disk encryption on host)
```

**Sensitive Fields (Passwords, Phone):**
```python
# Application-level encryption
from cryptography.fernet import Fernet

def encrypt_field(plain_text: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(plain_text.encode()).decode()

# Store encrypted in DB, decrypt on retrieval
```

### 5.2 End-to-End Encryption (E2E) - Phase 2

**Für Chat-Nachrichten:**
```
Concept (Signal Protocol):
1. Users share public keys (stored on server)
2. Client encrypts message with recipient's public key
3. Server stores encrypted blob (cannot read)
4. Recipient decrypts with private key

Limitation: No Server-side search on encrypted messages
```

---

## 6. Input Validation & Injection Prevention

### 6.1 SQL Injection Prevention

**Mittel:**
- ✅ Parameterized Queries (Prepared Statements)
- ✅ ORM (SQLAlchemy) - not raw SQL

**Anti-Pattern (❌ NEVER):**
```python
# VULNERABLE
query = f"SELECT * FROM users WHERE email = '{email}'"
```

**Correct Pattern (✅ ALWAYS):**
```python
# Using SQLAlchemy ORM
from sqlalchemy import select

user = session.execute(
    select(User).where(User.email == email)
).scalar_one_or_none()

# Or parameterized query (if using raw SQL)
query = "SELECT * FROM users WHERE email = %s"
cursor.execute(query, (email,))
```

### 6.2 XSS (Cross-Site Scripting) Prevention

**Mittel:**
- ✅ Content Security Policy (CSP) Header
- ✅ HTML Escaping in Frontend
- ✅ No unsafe `innerHTML` (use `textContent` or sanitizers)

**CSP Header:**
```
Content-Security-Policy: 
  default-src 'self'; 
  script-src 'self' https://cdn.jsdelivr.net; 
  style-src 'self' 'unsafe-inline'; 
  img-src 'self' https://cdn.nano-marketplace.de;
```

### 6.3 CSRF (Cross-Site Request Forgery) Prevention

**Mittel:**
- ✅ SameSite Cookie Attribute: `SameSite=Strict`
- ✅ CSRF Tokens für State-changing Methods (POST, PATCH, DELETE)

**Token-Flow:**
```
1. GET /form → Server generates CSRF token
2. Form includes: <input name="_csrf" value="token123">
3. POST submission → Server validates token
4. If invalid → 403 Forbidden

In FastAPI:
from starlette.middleware.csrf import CSRFMiddleware
app.add_middleware(CSRFMiddleware, secret_key="...")
```

---

## 7. Threat Model

### 7.1 Angriffsszenarios & Mitigationsstrategien

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **Brute Force Login** | Hoch | Mittel | Rate limiting: 5 Attempts/15min per IP |
| **Message Interception** | Mittel | Hoch | TLS für alle Übertragungen |
| **SQL Injection** | Gering | Kritisch | Parameterized Queries |
| **Privilege Escalation** | Gering | Kritisch | RBAC enforcement, Token validation |
| **Data Breach (Object Storage)** | Gering | Kritisch | Network isolation, access policies, encryption |
| **DDoS Attack** | Mittel | Hoch | Cloudflare Free Tier, Nginx rate limiting, WAF rules |
| **Account Takeover** | Gering | Hoch | 2FA, Session monitoring |

---

## 8. Audit Logging

### 8.1 Audit Trail

**Was wird geloggt:**
```
{
  "timestamp": "2025-02-24T10:15:00Z",
  "action": "NANO_PUBLISHED",
  "actor_user_id": "uuid-creator",
  "target_nano_id": "uuid-nano",
  "details": {
    "title": "Excel für Anfänger",
    "status_before": "pending_review",
    "status_after": "published"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "result": "success"
}
```

**Storage:** Immutable (append-only) in MinIO + Loki

**Retention:** 7 Jahre (per DSGVO + German tax law)

**Access:** Admin nur über encrypted connection, alle Access-Events selbst geloggt

---

## 9. Compliance & Audits

### 9.1 Externe Audits

**MVP Go-Live Anforderungen:**
- [ ] Security Audit (Penetration Test)
- [ ] DSGVO Compliance Audit (externer Datenschutz-Consultant)
- [ ] Code Review (Static Analysis: SonarQube, SAST)

### 9.2 Interne Tests

**Regelmäßig (monatlich):**
- [ ] OWASP Top 10 Check
- [ ] Dependency Vulnerability Scanning (Snyk, Dependabot)
- [ ] SSL/TLS Configuration Test (Qualys SSL Labs, testssl.sh)
- [ ] Database Backup Restore Test
- [ ] Disaster Recovery Drill

---

## 10. Gesetzliche Anforderungen (Deutsch-spezifisch)

### 10.1 TMG (Telemediengesetz)

**Anforderungen:**
- ✅ Impressum auf Website (Name, Adresse, Kontakt)
- ✅ Haftungsausschluss
- ✅ Datenschutzerkläring

### 10.2 UrhG (Urheberrecht)

**Plattform haftet nicht direkt für Inhalte**, aber muss:
- ✅ Takedown-Partner (DMCA-ähnlich) unterstützen
- ✅ Content-Policy publizieren
- ✅ Moderations-Prozess haben
- ✅ Creator bestätigt Urheberrechte bei Upload

---

## 11. Payment Security (Phase 2, nur wenn Monetisierung)

### 11.1 PCI DSS (Payment Card Industry)

Falls Kreditkarten akzeptiert:
- ✅ Never store full card numbers
- ✅ Use PCI-DSS compliant provider (Stripe, PayPal)
- ✅ No direct card processing by platform

---

## 12. Checklist für Production Launch

- [ ] HTTPS enabled, HSTS header set
- [ ] Password hashing implemented (bcrypt, 12 rounds minimum)
- [ ] SQL injection prevention confirmed (parameterized queries)
- [ ] CSRF tokens in place for state-changing ops
- [ ] Rate limiting configured (Login, API)
- [ ] 2FA available (admins mandatory, optional for users)
- [ ] Audit logging for critical actions
- [ ] DSGVO compliance audit passed
- [ ] Security penetration test completed
- [ ] Backup/restore tested
- [ ] Incident response plan documented
- [ ] Privacy policy + Terms published
- [ ] Data processing agreements signed
- [ ] Alerts configured in Prometheus/AlertManager
- [ ] Encryption enabled (at-rest + in-transit)

---

## Referenzen

- [01 — Stakeholder & Rollen](./01_stakeholder_roles.md) (Datenzugriff)
- [05 — Systemarchitektur](./05_system_architecture.md) (Infrastructure Security)
- [10 — Operations & Observability](./10_operations_observability.md) (Audit Logs)
