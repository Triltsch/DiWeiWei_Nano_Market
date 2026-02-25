# 02 — Fachliche Anforderungen

---

## Übersicht

Basierend auf der Studienarbeit und dem professionellen Produktreife-Standard werden alle funktionalen Anforderungen in drei Kategorien klassifiziert:

- **MUSS (M):** Kritisch für MVP, ohne diese keine Freigabe
- **SOLL (S):** Wichtig für Produktqualität, zielstrebig anstreben
- **KANN (K):** Erweiterungen für zukünftige Phasen oder bei verfügbarem Budget

---

## 1. Authentifizierung & Autorisierung

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| AUTH-001 | Benutzerregistrierung | Self-Service: E-Mail + Passwort. Eindeutige Benutzernamen. Email-Verifizierung erforderlich. | SA2, Prototyp |
| AUTH-002 | Sichere Passwörter | Hashing via bcrypt oder Argon2 (Scrypt minimal). Min. 8 Zeichen, Komplexitätsanforderung. ❌ Prototyp hat NO Hashing | SA2 Sec-Gap |
| AUTH-003 | Login/Logout | Session-basierte oder Token-basierte (JWT + Refresh Token). 2FA optional in MVP. ❌ Prototyp kein 2FA | SA2 |
| AUTH-004 | Rollenbasierte Zugriffskontrolle (RBAC) | Minimum 4 Rollen: Admin, Creator, Consumer, Moderator (optional MVP). Permissions-Matrix pro Rolle. | [01_stakeholder_roles.md](./01_stakeholder_roles.md) |
| AUTH-005 | Account-Verwaltung | Passwortänderung, E-Mail-Änderung mit Verification. Profil-Daten-Verwaltung. | SA2, Prototyp |
| AUTH-006 | Session Management | Automatische Logout nach 30 Min Inaktivität. Parallele Sessions limitieren (1 Maximum pro Browser). | Security Best Practice |
| AUTH-007 | Audit Logging Auth | Alle Logins, Logouts, Failed Attempts werden geloggt (mit Timestamp, IP, User-Agent). | DSGVO, Compliance |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| AUTH-101 | Multi-Factor Authentication (2FA) | TOTP via Authenticator-Apps oder SMS. Backup-Codes. |
| AUTH-102 | Single Sign-On (SSO) | OAuth2/OpenID Connect für Unternehmensnutzer (Azure AD, GoogleWorkspace). |
| AUTH-103 | Passwort-Reset | E-Mail-basiert, sichere Token, Verbrauchbarkeit limitieren. |
| AUTH-104 | Social Login (optional) | Google, LinkedIn als Alternative (Privacy-sensitive). |

### KANN-Anforderungen (Phase 2+)

- WebAuthn / FIDO2 Support
- Biometrics (für Mobile App)
- Federated Identity (eduGAIN für Hochschulen)

---

## 2. Nano-Management & Inhalte

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| NANO-001 | Nano-Upload | ZIP-Datei mit Metadaten. Größenlimit: 100 MB. Validierung: Dateiformat, Struktur. ✅ Prototyp implementiert | SA2 |
| NANO-002 | Metadaten-Erfassung | Pflichtfelder: Titel, Beschreibung, Dauer (min), Kompetenzstufe (1-3), Themengebiet (1-5), Sprache, Format (Video/Text/Quiz). | SA2 |
| NANO-003 | Versionierung | Nanos sind immutable mit Version-Nummer (v1.0, v1.1 etc). Historyverfolgung. Update = neue Version. | SA2, Professionalisierung |
| NANO-004 | Publikationsstatus | Workflow: draft → pending_review → published ∨ archived. Automatische/manuelle Review. ✅ Prototyp: Status-Flag | SA2 |
| NANO-005 | Nano-Bearbeitung | Ersteller kann Metadaten editieren und neue Versionen hochladen. Alte Versionen archivierbar. | SA2, Prototyp |
| NANO-006 | Nano-Detail-Ansicht | Zeigt komplett Metadaten, Creator-Info, Avg Rating, Comments, Download-Link. | SA2, Prototyp |
| NANO-007 | Nano-Löschen | Nur Creator oder Admin kann löschen. Soft-Delete (Archive) bevorzugt statt Hard-Delete DSGVO. | DSGVO, Compliance |
| NANO-008 | Lizenzangabe | Creator muss Nutzungsbedingungen für Nano definieren (z.B. CC-BY-SA, proprietary). Standard-Vorlagen anbieten. | IP-Recht |
| NANO-009 | Media-Upload im Nano | ZIP darf enthalten: PDF, Bilder (JPG/PNG), Video (MP4/WebM). Max-Dateigröße pro Datei: 50 MB. | Best Practice |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| NANO-101 | Modul-Zuordnung | Nanos können Modulen zugeordnet werden (1:n). Module sind Sammlung von Nanos zu Schulung. |
| NANO-102 | Auto-Metadaten-Extraction | AI-Powered Vorschlag von Tags + Themengebiet aus Nano-Inhalten. |
| NANO-103 | Template-System | Vorgefertigte Nano-Templates zum schnelleren Upload. |
| NANO-104 | Bulk-Upload | Multiple ZIPs gleichzeitig hochladen + Metadaten-CSV. |
| NANO-105 | Nano-Export | Download als ZIP mit vollständigen Metadaten (für LMS-Import zukünftig). |

### KANN-Anforderungen (Phase 2+)

- Zusammenarbeit mehrerer Creator (Co-Ownership)
- Nano-Samplen (z.B. 1 Minute Vorschau)
- Translationen von Nano-Metadaten (Multilingual)

---

## 3. Suche & Filterung & Discovery

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| SEARCH-001 | Volltextsuche | Titel, Beschreibung, Metadaten (case-insensitive) durchsuchen. Keyword-Matching. ✅ Prototyp | SA2 |
| SEARCH-002 | Filter-Optionen | Filter nach: Themengebiet, Dauer (min-max), Kompetenzstufe, Sprache, Creator. ✅ Prototyp | SA2 |
| SEARCH-003 | Ergebnisranking | Standard: Relevanz (Text-Match Priority), fallback: Rating, Upload-Datum. | UX Best Practice |
| SEARCH-004 | Pagination | Max. 20er pro Seite zur Performance. "Load More" oder Seitenzahlen-Interface. | UX Best Practice |
| SEARCH-005 | Saved Searches | Konsumenten können häufige Such-Filter speichern für schnelle Zugriffe. | Phase 1 oder MVP |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| SEARCH-101 | Faceted Search | Multi-Select Facetten (Thema, Dauer, Level) anzeigen + Anzahl (z.B. "Excel (15)"). |
| SEARCH-102 | Typo-Toleranz | Fuzzy Matching für Tippfehler. ElasticSearch-Ready. |
| SEARCH-103 | Sort-Optionen | Nach Relevanz, Rating, Dauer, Aktualität, Popularität (Downloads) sortierbarnew. |
| SEARCH-104 | Advanced Search | Boolean-Operatoren: +term, -term, "exact phrase". |
| SEARCH-105 | Search Analytics | Admin sieht häufigste Suchanfragen + Zero-Result Queries. |

### KANN-Anforderungen (Phase 2+)

- AI-Recommender ("Nutzer sehen auch...")
- Search Suggestions (Autocomplete)
- Natural Language Query ("Ich brauche Excel für Anfänger")

---

## 4. Bewertung & Feedback

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| REVIEW-001 | Star-Rating | 1-5 Sterne-System pro Nano. Nur registrierte Konsumenten. 1 Rating pro Nutzer pro Nano. | SA2, Prototyp |
| REVIEW-002 | Kommentar-Funktion | Zusätzlich zu Rating optional Kommentar hinterlassen. Max. 500 Zeichen. | SA2, Prototyp |
| REVIEW-003 | Durchschnitt-Anzeige | Beispiel "4.2 ★ (15 votes)". | SA2 |
| REVIEW-004 | Review-Moderation | Admin kann unangemessene Kommentare löschen. Creator kann Antwort hinterlassen. | Compliance |
| REVIEW-005 | Creator-Feedback | Creator bekommt alle Ratings + Kommentare in Dashboard. | Creator UX |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| REVIEW-101 | Review-Moderation Workflow | Flagging unangemessener Kommentare durch Nutzer. Admin-prüfung erforderlich. |
| REVIEW-102 | Review-Analytics | Creator sieht: Rating-Verlauf über Zeit, Sentiment-Trend der Kommentare. |
| REVIEW-103 | Reaction Emojis | Alternative zu Star: Emojis (thumbs up/down) für schnelle Feedback. |

### KANN-Anforderungen (Phase 2+)

- Weighted Ratings (Experten höher gewichtet)
- Review Authenticity (z.B. "Verified Purchaser")

---

## 5. Kommunikation & Chat

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| CHAT-001 | Chat-Initiation | Beliebig Konsument kann Chat mit Creator zu spezifischem Nano starten (1:1). | SA2, Prototyp |
| CHAT-002 | Nachrichtenhistorie | Chat-Nachrichten persistieren in DB. Beide Parteien sehen vollständige Historie. | SA2 |
| CHAT-003 | Authentifizierung | Nur eingeloggte Nutzer können Chat. Creator/Consumer prüfbar. | DSGVO, Compliance |
| CHAT-004 | Enkryptierung Transport | TLS/SSL verschlüsselt in Transit. ❌ Prototyp hat keine Verschlüsselung | Security Baseline |
| CHAT-005 | Nachrichtenformat | Text max. 1000 Zeichen. Emoji-Support. Links erlaubt (auto-linkified). | UX |
| CHAT-006 | Chat-UI | Polling-Modell (aktualisierbar via Refresh-Button), später WebSocket. | SA2, Prototyp (polling) |
| CHAT-007 | Inaktivitäts-Timeout | ChatSession nach 30 Tagen ohne Aktivität archivieren (aber nicht löschen). | Compliance, Storage |
| CHAT-008 | Abuse Prevention | Spam-Filter: Max. 10 Nachrichten pro Minute pro User. Admin kann Chat-Threads manuell deaktivieren. | Trust & Safety |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| CHAT-101 | End-to-End Encryption (E2E) | Optional: Private Key generiert clientseitig. Server speichert nur encrypted Messages. |
| CHAT-102 | WebSocket-Migration | Echtzeit-Chat statt Polling. User-Presence-Indicators (online/offline). |
| CHAT-103 | Chat-Benachrichtigungen | E-Mail oder In-App Notification bei neuer Nachricht. Muting möglich. |
| CHAT-104 | File-Sharing im Chat | Kleine Dateien (<5 MB) attachable. Links zu externen Repos. |
| CHAT-105 | Chat-Export | Beide Parteien können Chat-Transcript als PDF exportieren. |

### KANN-Anforderungen (Phase 2+)

- Group Chats (zwischen Teams)
- Voice/Video Chat
- AI-Assistant im Chat (Chatbot für FAQ)

---

## 6. Profil & Personalisierung

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| PROF-001 | Öffentliches Profil | Creator-Profil mit: Name, Unternehmen, Beschreibung, Avatar (optional), Kontaktinfo (email öffentlich?). | SA2 |
| PROF-002 | Privates Profil | Consumer-Profil mit: Name, Funktion, Unternehmen. Nur für eingeloggte sichtbar. | SA2 |
| PROF-003 | Profilediting | Nutzer kann eigne Profile-Daten editieren inklusiv Passwort-Änderung. | SA2, Prototyp |
| PROF-004 | Avatar | Optional 200x200 profilbild. Fallback: Initials. | UX |
| PROF-005 | Interessen/Präferenzen | Consumer kann bis zu 5 Themeninteressen speichern. | SA2 |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| PROF-101 | Profil-Verifikation Badge | Grüner Haken für verifiziete Creator (HR-Nummer geprüft). |
| PROF-102 | Creator-Stats Dashboard | Anzahl hochgeladene Nanos, Avg Rating, Downloads-Total, Feedback-Summary. |
| PROF-103 | Verifikations-Link | Creator-Profil mit verlinkter Website + Verifizierungs-Button |

### KANN-Anforderungen (Phase 2+)

- Trust Score / Reputation Badges (z.B."Top Creator")
- Nutzer-Zertifikationen (z.B. "Zertifiziert durch XYZ")
- Public Portfolio / Showcase

---

## 7. Moderation & Sicherung

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| MOD-001 | Content-Review-Workflow | Admin oder Moderator: Stichproben-Check von Nanos vor Veröffentlichung auf Urheberrecht, DSGVO, Spam. | Compliance |
| MOD-002 | Archivierungsprozess | Ein unangemessenes Nano kann vom Admin archiviert werden (Status=1). Creator wird benachrichtig. | SA2 |
| MOD-003 | Flag-System | Nutzer können inappropriate Content / Belästigung flaggen. Admin sieht Flag-Queue. | Trust & Safety |
| MOD-004 | Audit Trail | Alle Admin + Moderator-Aktionen werden geloggt (wer, wann, was). | Compliance, DSGVO |
| MOD-005 | Takedown-Prozess | Bei Urheberrechts-Beschwerde (DMCA-ähnlich): Creator gets 48h zur Antwort, dann archivieren. | IP-Recht |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| MOD-101 | Automated Moderation | KI-Basics: Spam-Detection, Profanity-Filter, Plagiarismus-Check. |
| MOD-102 | Moderation-Dashboard | Queue-View mit Pending-Content, Flags, Tickets. |
| MOD-103 | Moderation-SLA | Comment muss innerhalb 7 Tagen reviewt werden. |
| MOD-104 | Appeal-Process | Creator kann gegen Archivierung widersprechen. 2. Review durch anderer Moderator. |

### KANN-Anforderungen (Phase 2+)

- Advanced Plagiarism Detection (Turnitin-Integration)
- Computer Vision für unangemessene Bilder

---

## 8. Favoriten & Listen

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| FAV-001 | Favorisierung | Consumer kann Nano zum Favorit mit Herz-Button markieren. Persistent speichern. | SA2, Prototyp |
| FAV-002 | Favoriten-Liste | "Meine Favoriten" zeigt alle favorisierten Nanos mit Filter/Sort-Optionen. | SA2 |
| FAV-003 | Anzahl-Badge | Herz-Button zeigt Nutzerzahl ("♥ 42 favorited"). | UX |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| FAV-101 | Listen-Management | Custom-Listen erstellen (z.B. "Meine Excel-Schulung", "Sommer-Kurse"). |
| FAV-102 | Liste-Teilen | Personen-Link oder Invitations für anderen zum Zugriff auf Liste (lesend). |
| FAV-103 | Liste-Export | Favoriten als CSV/JSON exportieren. |

---

## 9. Daten & Analytics

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| ANALYTICS-001 | Usage Logs | System loggt: Wer, wann, was (Login, Download, Rating, etc). Speichern >30 Tage. | DSGVO |
| ANALYTICS-002 | Admin-Dashboard | Admin sieht: Active Users (weekly/monthly), Nano-Count, Rating-Dist, Error-Rates. | Operations |
| ANALYTICS-003 | Creator-Analytics | Creator Dashboard zeigt: Views, Downloads, Avg Rating pro Nano, Kommentar-Summary. | Creator UX |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| ANALYTICS-101 | Cohort-Analysis | Nutzer nach Acquisition-Quelle clustern. |
| ANALYTICS-102 | KPI-Reporting | Monatliche Reports zu: MAU, Engagement-Rate, Creator-Growth, Retention. |
| ANALYTICS-103 | Heat-Maps | Clickstream-Analytics auf Frontend (anonymisiert). |

### KANN-Anforderungen (Phase 2+)

- Predictive Analytics (Churn-Risk scoring)
- Machine Learning Insights

---

## 10. Export & Integration

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| EXPORT-001 | Nano-Download | Consumer kann Nano-ZIP herunterladen (wenn Creator erlaubt). | SA2 |
| EXPORT-002 | Metadaten-Export | Admin kann Nano-Katalog als CSV exportieren (Batch). | Admin UX |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| EXPORT-101 | SCORM-Export | Nanos zu SCORM 1.2 / 2004 konvertieren für LMS-Import. |
| EXPORT-102 | xAPI/TinCan | Interoperabilität via Learning Record Store (LRS). |
| EXPORT-103 | API-Access | REST API für Dritt-Systeme zum Abruf von Nano-Metadaten. |

---

## 11. Datenschutz & DSGVO

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| DSGVO-001 | Datenschutzerklärung | Öffentlich verfügbar, detailliert nach Art. 13/14 DSGVO. | DSGVO |
| DSGVO-002 | Verarbeitungsbasis | Rechtmäßigkeit dokumentieren: Einwilligung (Art. 6 Abs. 1 a), Vertrag (b), oder Rechtsobliegenheit (c). | DSGVO |
| DSGVO-003 | Betroffenenrechte | Umsetzen: Zugriff (Art. 15), Berichtigung (16), Löschung (17), Sperrung (18). | DSGVO |
| DSGVO-004 | Consent Management | Opt-in Checkboxes bei Registrierung & Newsletter (falls zutreffend). Revocation/Opt-out möglich. | DSGVO |
| DSGVO-005 | Privacy-by-Design | Default: Minimal Data Collection, Dual-Use Minimizing. | DSGVO |
| DSGVO-006 | DPA mit Cloud-Providers | Data Processing Agreement mit AWS, notfalls Zusatzbedingungen. | DSGVO |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| DSGVO-101 | Data Retention Policy | Automatische Löschung nach definierten Fristen (z.B. User-Account nach 12M nach Inaktivität). |
| DSGVO-102 | DSFA (Datenschutzfolgenabschätzung) | Durchführung + Dokumentation (besonders bei Profiling/Tracking). |
| DSGVO-103 | Datenabzug-Feature | Export aller persönlicher Daten als JSON/CSV (Art. 20 DSGVO). |
| DSGVO-104 | Breach Notification | Automatische Interna-Mitteilung bei Datenabfluss <72h. Log-System aktivieren. |

---

## 12. Performance & Skalierbarkeit

### MUSS-Anforderungen (MVP)

| ID | Anforderung | Beschreibung | Quelle |
|----|-------------|-------------|--------|
| PERF-001 | Seitenladezeit | Zielzeit <2s (3G) für Homepage. Lazy Loading für Bilder. | UX, SEO |
| PERF-002 | Database Performance | Query avg <100ms. Indexierung auf häufigen Filtern (Thema, Creator, Status). | Operations |
| PERF-003 | Uptime SLA | Keine geplanten Ausfallzeiträume während Schichttage. 99.5% uptime target. | Operations |
| PERF-004 | Dateiübertragung | Max Upload-Zeit 10 Minuten für 100 MB ZIP. Progress-Indikator. | UX |

### SOLL-Anforderungen (Phase 1)

| ID | Anforderung | Beschreibung |
|----|-------------|-------------|
| PERF-101 | Caching-Strategie | Page Caching (30 Min), Query Caching (Redis), Browser-Caching (ETag). |
| PERF-102 | CDN-Integration | CloudFront für statische Assets + Nano-ZIP-Downloads. |
| PERF-103 | Database Replication | Read-Replicas für bessere Skalierbarkeit. |
| PERF-104 | Load-Testing | Benchmark: Mindestens 1.000 parallele Nutzer unterstützen. |

---

## 13. Priorisierung nach WSJF (Weighted Shortest Job First)

```
Priorität = (Value + Time Sensitivity + RiskReduction + Effort) / Effort

KRITISCH:
- AUTH-002, AUTH-007 (Security)
- DSGVO-001, DSGVO-003 (Compliance)
- MOD-001 (Trust)

HOCH:
- NANO-001..009 (Core Funcs)
- SEARCH-001..005 (Discovery)
- CHAT-001..008 (Communication)

MITTEL:
- REVIEW-001..005 (UX)
- PROF-001..005 (Personalisierung)

SPÄTER:
- ANALYTICS-101+ (Insights)
- EXPORT-101+ (Integrations)
```

---

## Referenzen

- [03 — User Journeys](./03_user_journeys.md)
- [04 — Domänenmodell](./04_domain_model.md)
- [06 — Security & Compliance](./06_security_compliance.md)
