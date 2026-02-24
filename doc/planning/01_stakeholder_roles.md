# 01 — Stakeholder & Rollen

---

## 1. Rollen-Matrix

Der Nano-Marktplatz folgt einem **Three-Sided Marketplace**-Modell mit vier primären Rollen und mehreren sekundären Stakeholdern.

### 1.1 Primäre Rollen

#### **A. Plattform-Betreiber / Administrator**

**Definition:**  
Operiert die Infrastruktur, reguliert Nutzerverhalten, sichert Compliance.

**Profil:**
- Einzelperson oder Team (OPS, Legal, Content)
- Neutral zwischen Anbieter und Nachfrager
- Trägt Haftung für Datenenschutz und Inhaltsvalidität

**Rechte & Verantwortungen:**
| Funktion | Berechtigung |
|----------|--------------|
| Login-Verwaltung | Alle Nutzer-Accounts deaktivieren |
| Content-Moderation | Nanos archivieren, editieren, löschen |
| User-Management | Rollen vergeben, Suspensionen verhängen |
| Reporting | Zugriff auf aggregierte Nutzungsstatistiken |
| Compliance | DSGVO-Anfragen bearbeiten, Löschungen durchführen |

**Nutzerfälle (Use Cases):**
1. **Content-Review-Workflow:**
   - Stichproben nachladen hochgeladener Nanos
   - Urheberrechts-, DSGVO-, Spam-Prüfung durchführen
   - Freigabe oder Archivierung vornehmen

2. **Moderation bei Beschwerde:**
   - Flag-System für unangemessene Inhalte prüfen
   - User-Beschwerde über Belästigung bearbeiten
   - Escalation an External (Rechtsbeistand)

3. **Analytics & Monitoring:**
   - Dashboards zu Plattform-Health prüfen (uptime, errors, active users)
   - Performance-Metriken monitoren

**Onboarding & Zugang:**
- Manuelle Aktivierung durch Gründer
- 2FA (Two-Factor Authentication) erforderlich
- Audit Logging aller Admin-Aktionen

---

#### **B. Herausgeber / Content Creator**

**Definition:**  
Erstellen, veröffentlichen und verwalten Nano-Lerneinheiten.

**Profil:**
- Weiterbildungsanbieter (VHS, private Trainer)
- Hochschulen, Unternehmen mit eigenen Schulungsabteilungen
- Freelancer-Trainer
- Technisches NiveaU: Mittel bis Hoch (ZIP-Upload, Metadaten-Erfassung)

**Rechte & Verantwortungen:**
| Funktion | Berechtigung |
|----------|--------------|
| Nano-Verwaltung | Upload, Bearbeitung, Archivierung eigener Nanos |
| Profil | Unternehmensinfo, Beschreibung, Avatar. |
| Chat | Kommunikation mit Nachfragern über Nanos |
| Analytics | Zugriff auf Bewertungen, Download-Zahlen für eigene Nanos |
| Lizenzierung | Angabe von Nutzungsbedingungen pro Nano |

**Profil-Attribute:**
- Unternehmensname
- Beschreibung / Bio
- Kontaktdaten
- Webseite
- Verifizierung (z.B. via Unternehmensregister)

**Nutzerfälle:**
1. **Nano-Upload & Veröffentlichung:**
   - ZIP-Datei hochladen (max. 100 MB, validiert)
   - Metadaten erfassen: Titel, Beschreibung, Dauer, Themengebiete, Kompetenzstufe, Sprache, Format
   - Lizenz wählen (z.B. CC-BY-SA, Proprietary)
   - Veröffentlichung / Private-Mode startet Moderation

2. **Feedback & Optimierung:**
   - Bewertungen & Kommentare abrufen
   - Eigene Nanos aktualisieren (v2 versionieren)
   - Analytics: Downloadrate, Favoriten-Count, Durchschnittsrating

3. **Zusammenarbeit:**
   - Chat mit Interessenten

**Onboarding & Verifikation:**
- Self-Service-Registrierung
- E-Mail-Verifikation erforderlich
- Optional: Unternehmensregistrierung prüfen (skalierbar)
- First-Time Upload mit Hinweis auf Datenschutz & Urheberrecht

---

#### **C. Nachfrager / Konsument**

**Definition:**  
Suchen, bewerten und nutzen Nano-Inhalte.

**Profil:**
- HR-Leiter, Learning Manager in Unternehmen
- Einzelne Lernende, Fachkräfte
- Hochschulen bei Fortbildungssuche
- Technisches Niveau: Gering bis Mittel

**Rechte & Verantwortungen:**
| Funktion | Berechtigung |
|----------|--------------|
| Suche & Filterung | Durchsuchen aller öffentlichen Nanos |
| Detailansicht | Vorschau & Metainformation lesen |
| Bewertung | Ratings (1-5 Sterne) + Kommentare hinterlassen |
| Favorisierung | Persönliche Favor-Listen |
| Chat | Kontakt mit Herausgebern aufnehmen |
| Export | Downloadlink erhalten (falls autorisiert) |

**Profil-Attribute:**
- Name
- Funktion (z.B. "Learning Manager")
- Unternehmen
- Persönliche Lern-Interessen (max. 5 Themengebiete)

**Nutzerfälle:**
1. **Suche & Discovery:**
   - Suchfeld oder Filter nach: Titel, Themengebiet, Dauer, Kompetenzstufe, Sprache
   - Ergebnissseite mit Ranking (nach Relevanz, Bewertung, Upload-Datum)

2. **Bewertung & Feedback:**
   - Nano ansehen (ggf. mit Vorauthenticaton)
   - Eigener Rating + Kommentar hinterlassen
   - Andere Kommentare lesen

3. **Favorisierung & Listen:**
   - Herzchen-Button Nanos zu "Meine Favoriten" hinzufügen
   - Listen verwalten (z.B. "Compliance Training", "Data Science")
   - Listen mit Kollegen/Team teilen (zukünftig)

4. **Direkte Kommunikation:**
   - Chat mit Creator initiieren (z.B. "Kann das Nano auch offline durchgeführt werden?")
   - Verhandlung über Lizenzierung, Customization etc.

**Onboarding & Identität:**
- Self-Service-Registrierung
- E-Mail-Verifikation
- Optional: Unternehmensdomäne + SSO (zukünftig)

---

#### **D. Moderator / Content Reviewer**

**Definition:**  
Spezialisierte Rolle für Qualitätssicherung und Streitbeilegung (Skalierung Phase 2).

**Profil:**
- Externe oder interne Experten
- Didaktische Kompetenz in Zielthemengebieten
- Expertise in Datenschutz / Urheberrecht (externe Berater)

**Rechte & Verantwortungen:**
| Funktion | Berechtigung |
|----------|--------------|
| Review-Zugriff | Stichproben-Nanos prüfen vor Veröffentlichung |
| Feedback | Structured-Review an Creator zurück |
| Escalation | Verdächtige/kritische Inhalte an Admin |
| Analytics | Monitoring von Moderation-Queue |

**Nutzerfälle:**
1. **Content-Review-Workflow:**
   - Moderations-Dashboard mit Nanos in "pending" Status
   - Gründliche Inhaltsprüfung durchführen (Didaktik, Genauigkeit, IP)
   - Feedback-Vorlagen verwenden (z.B. "Quellenangabe fehlt")
   - Freigabe oder Ablehnung mit Begründung

2. **Beschwerde-Bearbeitung:**
   - Flags bearbeiten (unangemessenes Material, Belästigung)
   - Entscheidung treffen: Archivieren, User warnen, oder ignorieren

**Onboarding & Verifikation:**
- Manuelle Aktivierung durch Admin
- Vertrag / NDA erforderlich  (bei externen Experten)
- Training auf Moderation-Rules


---

### 1.2 Sekundäre Rollen

| Rolle | Verantwortung | Phase |
|-------|--------------|-------|
| **Gast / Anonymer Nutzer** | Lese-Zugriff auf Nanos (optional) | Phase 1 |
| **Super-Admin** | IT-Infrastruktur, Backups, Security | MVP |
| **Content Analyst** | KPI-Monitoring, Trendanalyse | Phase 1 |
| **API-Consumer** | Drittanwendungen (LMS, HRSystems) | Phase 2 |

---

## 2. Rechteverwaltung (RBAC / Attribute-Based Access Control)

### 2.1 Rolle-Permission-Matrix

```
┌─────────────────────────┬────────┬──────────┬──────────┬──────────────┐
│ Ressource / Aktion      │ Gast   │ Creator  │ Consumer │ Admin        │
├─────────────────────────┼────────┼──────────┼──────────┼──────────────┤
│ Browse Public Nanos     │  ✅    │   ✅     │    ✅    │     ✅       │
│ Upload Nano             │  ❌    │   ✅     │    ❌    │     ✅       │
│ Edit Own Nano           │  ❌    │   ✅     │    ❌    │     ✅       │
│ Edit Any Nano           │  ❌    │   ❌     │    ❌    │     ✅       │
│ Rate & Comment          │  ❌    │   ✅     │    ✅    │     ✅       │
│ View Own Analytics      │  ❌    │   ✅     │    ❌    │     ✅       │
│ Moderation UI           │  ❌    │   ❌     │    ❌    │   ✅ / 🔵   │
│ User Management         │  ❌    │   ❌     │    ❌    │     ✅       │
│ Access Logs & Audit     │  ❌    │   ❌     │    ❌    │   ✅ / 🔵   │
│ Chat                    │  ❌    │   ✅     │    ✅    │     ✅       │
│ Delete Any Account      │  ❌    │   ❌     │    ❌    │     ✅       │
└─────────────────────────┴────────┴──────────┴──────────┴──────────────┘
✅ = Allowed  |  ❌ = Denied  |  🔵 = Conditional / Future
```

### 2.2 Attribut-basierte Zugriffskontrolle (ABAC) - Zukünftig

**Zusätzliche Dimensionen (Phase 2):**
- `Nano.Privacy`: public, private, organiztion-only
- `User.Verification`: unverified, verified, trusted
- `User.Organization`: Org_ID für org-interne Nanos
- `Nano.Status`: draft, pending_review, published, archived, deleted

**Erweiterte Regel:**
```
IF (Rolle == "Consumer" 
    AND Nano.Privacy == "organization-only" 
    AND User.Organization != Nano.Creator.Organization)
THEN Deny()
```

---

## 3. Organisationsmodelle

### 3.1 Single-Org Model (MVP)

**Struktur:**
```
Plattform
├── Creator: VHS Hannover
│   ├── Nano: Excel-Grundlagen
│   ├── Nano: PowerPoint-Design
│   └── Nano: Word Advanced
└── Creator: TechCorp GmbH
    ├── Nano: Python Basics
    └── Nano: Cloud Architecture
```

**Merkmale:**
- Creator agiert als Einzelnutzer oder Kontakt aus der Firma
- Keine Verwaltung mehrerer Nutzer pro Unternehmens-Konto
- Einfache Implementierung, begrenzte Skalierbarkeit

### 3.2 Multi-Org Model (Phase 1)

**Struktur:**
```
Plattform
├── Organization: VHS Hannover
│   ├── User: Max Müller (Admin)
│   │   └── Upload: Excel Basics
│   ├── User: Sarah Schmidt (Moderator)
│   └── Nano: [org-owned Nano mit collective Ownership]
└── Organization: TechCorp GmbH
    ├── User: IT-Manager (Admin)
    ├── User: HR-Manager (Viewer)
    └── Nano: Python Kurs
```

**Merkmale:**
- Pro Organisation: Admin, Editors, Viewers
- Rollenbasierte Zugriffskontrolle auf Org-Level
- Org. Billing: Rechnungsadministration
- Org. Analytics: Gesamt-KPIs

**Implementierung:**
- Neue Tabelle: `organizations`
- N:M Relation: `user_organization_roles`
- Scope alle Nano-Operationen auf `user.active_organization`

---

## 4. Onboarding & Verifikation

### 4.1 Creator Onboarding (Anbieter)

```
Step 1: Self-Service Registration
├─ E-Mail + Passwort
├─ Profil-Grunddaten
└─ Nutzungsbedingungen + DSGVO acknowledged

Step 2: E-Mail Verification
├─ Bestätigungslink senden
├─ Token 24h gültig
└─ Resend erlaubt

Step 3: Company Verification (Optional, Phase 1)
├─ Unternehmensname eingeben
├─ Handelsregister-Nummer (HR, UID)
├─ System prüft externe DB
└─ Badge: "Verifizierter Creator"

Step 4: Sandbox-Mode (Zukünftig)
├─ Erste 3 Nanos im "draft" + "pending_review"
├─ Moderator-Review erforderlich
└─ Nach Bestätigung: Volle Publisherechte
```

### 4.2 Consumer Onboarding (Nachfrager)

```
Step 1: Self-Service Registration
├─ E-Mail + Passwort
├─ Name, Funktion, Unternehmen (optional)
└─ Datenschutzerklärung accepted

Step 2: E-Mail Verification
├─ Bestätigungslink
└─ Sofort nutzbar nach Verification

Step 3: Interessensangabe (Optional)
├─ Bis zu 5 Themengebiete wählen (für Recommend)
└─ Später editierbar
```

### 4.3 Admin Onboarding

```
Step 1: Manual Creation
├─ Admin-Account durch Gründer erzeugt
├─ Temporäres Passwort
└─ Erste Anmeldung erzwingt Passwortänderung

Step 2: 2FA Setup
├─ TOTP (Time-based One-Time Password) mit Authy/Google Authenticator
├─ Backup-Codes generieren
└─ Bestätigung erforderlich

Step 3: Audit Logging Activation
├─ Alle Admin-Aktionen werden geloggt
├─ Log-Zugriff selbst geloggt (meta)
└─ Immutable Audit Trail (z.B. in S3)
```

---

## 5. Vertragsbeziehungen & Nutzungbedingungen

### 5.1 Nutzer-Plattform Verhältnis

**ToS (Terms of Service) - Pflichtbestätigung bei Registrierung:**
- Plattformnutzung unter Einhaltung Gesetzen
- IP-Recht Klarstellung: Creator bleibt Rechtshaber, erteilt beschränkte Lizenz
- Moderation & Content-Removal bei Rechtsverletzung
- Haftungsbegrenzung der Plattform
- Datenschutzerklärung DSGVO

### 5.2 Creator-Nachfrager Beziehung

**Tausch-Modell (MVP):**  
Keine formale Vertragsbindung auf Plattform-Ebene. Direkter Chat zwischen Parteien für Einzelverhandlungen.

**Optional (Phase 1+):**
- Standard-Lizenzvorlagen (z.B. CC-BY-SA)
- Digital Signature für Lizenz-Vereinbarungen
- Payment-Integration für kommerzielle Transaktionen

---

## 6. Responsible Disclosure & Trust

### 6.1 Nutzer-Vertrauen-System

| Signal | Wert |
|--------|------|
| Verifiziertes Profil (Org-Check) | ⭐⭐⭐ |
| 50+ Nanos eingereicht | ⭐⭐ |
| Durchschnitt Rating ≥ 4.5 | ⭐ |
| Community-Flag / Beschwerde History | 🚩 (Warnung) |

### 6.2 Sandbox & Reputation System

**Für neue Creator:**
- Maximal 5 Nanos im Monat (Anti-Spam)
- Moderations-Review für erste 3 Nanos
- Nach 10 erfolgreichen Reviews: Automatische Freigabe

---

## Referenzen

- [02 — Fachliche Anforderungen](./02_requirements.md) (Datenschutz-Anforderungen)
- [06 — Security & Compliance](./06_security_compliance.md) (Authenticierung, DSGVO)
- [07 — Moduldesign](./07_modules.md) (Identity & Organization Module)
