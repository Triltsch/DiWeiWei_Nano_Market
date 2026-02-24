# 03 — User Journeys

---

## Übersicht

User Journeys beschreiben die vollständigen, realistischen Pfade der Hauptakteure durch das System. Diese Journeys sind Basis für User-Story-Ableitung und UX-Design.

---

## 1. Journey: Content Creator — Nano hochladen & veröffentlichen

**Persona:** Jana, 45, Trainerin bei VHS Hannover. Möchte ihr Excel-Anfängerkurs als Nano teilen.

### Schritte

```
┌─────────────────────────────┬──────────────────────────────┐
│        JOURNEY PHASE        │        AKTIONEN              │
├─────────────────────────────┼──────────────────────────────┤
│ 1. DISCOVERY               │                              │
│ (User findet Plattform)    │ • Am Laptop → Google: "Nano  │
│                            │   Marktplatz"                │
│                            │ • Findet Webseite            │
│                            │ • Clickt: "Creator werden"   │
│                            │                              │
│ 2. ONBOARDING              │ • Registrierung mit E-Mail   │
│ (Account erstellen)        │ • Passwort eingeben          │
│                            │ • Nutzungsbedingungen         │
│                            │   akzeptieren                │
│                            │ • Bestätigungslink in Email  │
│                            │   klicken                    │
│                            │ • Profil ausfüllen:          │
│                            │   - Name, Firma (VHS)        │
│                            │   - Kurzbeschreibung         │
│                            │   - Avatar                   │
│                            │                              │
│ 3. PREPARATION             │ • Dashboard aufrufen         │
│ (Nano vorbereiten)         │ • "Nano hochladen" Button    │
│                            │   klicken                    │
│                            │ • ZIP-Datei vorbereiten      │
│                            │   (Slides PDF + Bilder)      │
│                            │ • ZIP auswählen & uploaden   │
│                            │                              │
│ 4. METADATA ENTRY          │ • Form ausfüllen:            │
│ (Metadaten eingeben)       │   - Title: "Excel für        │
│                            │     Anfänger"                │
│                            │   - Beschreibung (200 chars) │
│                            │   - Dauer: 45 min            │
│                            │   - Kompetenzstufe: 1        │
│                            │   - Themengebiet:            │
│                            │     "Business Skills"        │
│                            │   - Sprache: Deutsch         │
│                            │   - Format: PDF + Video      │
│                            │ • Lizenz wählen: "CC-BY"     │
│                            │ • Vorschau prüfen            │
│                            │                              │
│ 5. SUBMISSION              │ • "Veröffentlichen" klicken  │
│ (Submit zur Moderation)    │ • System: Status = pending   │
│                            │ • Jana: Bestätigung erhalten │
│                            │   ("Ich prüfe dein Nano...") │
│                            │                              │
│ 6. WAIT FOR REVIEW         │ • Jana schließt Browser      │
│ (Moderations-Phase)        │ • Nach 24-48h E-Mail:        │
│                            │   "Nano gebilligt ✓"         │
│                            │   oder Feedback erforderlich │
│                            │                              │
│ 7. PUBLISHED               │ • Nano live! Status =        │
│ (Live-Schaltung)           │   published                  │
│                            │ • Jana erhält E-Mail:        │
│                            │   "Dein Nano ist online"     │
│                            │ • Sie navigiert zur Nano-    │
│                            │   Seite und sieht es         │
│                            │                              │
│ 8. MONITORING              │ • Die erste Woche:          │
│ (Nachverfolgung)           │ • Jana schaut täglich auf    │
│                            │   ihrem Analytics-           │
│                            │   Dashboard:                 │
│                            │   - 50 Views                 │
│                            │   - 3 Downloads              │
│                            │   - 1 Kommentar: "Sehr       │
│                            │     hilfreich!"              │
│                            │   - Avg. Rating: 4.5 ★       │
│                            │ • Sie ist zufrieden!         │
└─────────────────────────────┴──────────────────────────────┘
```

### Ergebnisse & Metriken

| Metrik | Ziel |
|--------|------|
| Time to Upload | <10 Min |
| Frustration Level | Low (intuitive UI) |
| First Feedback | <48h |
| Monthly Views | >100 in Month 1 |

### Pain Points & Lösungen

| Problem | Lösung |
|---------|--------|
| ZIP-Format ist komplex | ZIP-Template bereitstellen, ZIP-Creator im Browser |
| Metadaten langweilig | Drag-Drop UI, Auto-Vorschläge durch AI |
| Warte auf Review | Reviewer SLA definieren (24h) + Status-Updates |
| Weiß nicht, obs hilft | Analytics-Dashboard für Creator mit KPIs |

---

## 2. Journey: Administrator — Moderation eines Nanos

**Persona:** Michael, 38, Teil-Zeit Moderator für die Plattform. Prüft neue Inhalte.

### Schritte

```
┌─────────────────────────────┬──────────────────────────────┐
│        JOURNEY PHASE        │        AKTIONEN              │
├─────────────────────────────┼──────────────────────────────┤
│ 1. NOTIFICATION             │ • Michael erhält Slack       │
│ (Neue Nanos zur Review)     │   Notification: "Neue Nano   │
│                            │   zu prüfen"                │
│                            │ • Klickt Link → Moderations-│
│                            │   Dashboard                 │
│                            │                              │
│ 2. QUEUE INSPECTION         │ • Queue zeigt 5 Nanos        │
│ (Zu prüfende Nanos)         │   pending                   │
│                            │ • Filter: Neueste first      │
│                            │ • Michael wählt Janas Excel-│
│                            │   Nano aus                   │
│                            │                              │
│ 3. DETAILED REVIEW          │ • Moderations-Interface:     │
│ (Inhalt prüfen)            │ • Linke Spalte: Nano-Preview│
│                            │   - Titel, Beschreibung     │
│                            │   - ZIP-Inhalt auflisten    │
│                            │ • Rechte Spalte:             │
│                            │   Checkboxes:                │
│                            │   ✓ Urheberrecht OK         │
│                            │   ✓ DSGVO-konform           │
│                            │   ✓ Keine Belästigung       │
│                            │   ✓ Thema passend           │
│                            │ • Michael prüft ZIP-Inhalte: │
│                            │   PDF öffnen, Bilder prüfen  │
│                            │                              │
│ 4. DECISION MAKING          │ • Falls alles OK: Button     │
│ (Bestätigung/Ablehnung)     │   "Freigeben" klicken       │
│                            │ • Falls Problem: "Ablehnen" + │
│                            │   Grund wählen:              │
│                            │   - "Urheberrecht fraglich"  │
│                            │   - "Metadaten unvollständig"│
│                            │   - "Weitere Infos nötig"    │
│                            │ • Optionale Notiz hinzufügen │
│                            │                              │
│ 5. NOTIFICATION TO CREATOR  │ • System sendet E-Mail       │
│ (Creator bekommt Bescheid)  │   an Jana:                   │
│                            │   "✓ Dein Nano ist freigegeben"│
│                            │   oder                        │
│                            │   "Wir benötigen:             │
│                            │   [Reason]"                   │
│                            │                              │
│ 6. AUTO-PUBLICATION        │ • Falls freigegeben:         │
│ (Go-Live oder Zurück)      │ • Status wechselt zu         │
│                            │   "published"                │
│                            │ • Nano wird searchable,       │
│                            │   rateable                   │
│                            │                              │
│ 7. LOGGING & AUDIT          │ • Michael kann auch:         │
│ (Dokumentation)            │ • Sein Action-Log prüfen      │
│                            │ • Alle Moderationsaktionen   │
│                            │   werden geloggt mit: Zeit,  │
│                            │   Moderator, Aktion,         │
│                            │   Grund                      │
└─────────────────────────────┴──────────────────────────────┘
```

### Ergebnisse & Metriken

| Metrik | Ziel |
|--------|------|
| Time per Review | 5-10 Min |
| False Rejection Rate | <5% |
| Appeal Handling | <3 Tage |
| Moderator SLA Hit | >95% (24h) |

---

## 3. Journey: Unternehmens-Nutzer — Excel-Schulung recherchieren & organisieren

**Persona:** Sandra, 52, Learning Manager bei einem Finanzunternehmen. Sucht Trainings für ihr Team.

### Schritte

```
┌─────────────────────────────┬──────────────────────────────┐
│        JOURNEY PHASE        │        AKTIONEN              │
├─────────────────────────────┼──────────────────────────────┤
│ 1. LOGIN                    │ • Sandra öffnet Browser      │
│ (Authentifizierung)         │ • Nano-Marktplatz.de         │
│                            │ • Username & Passwort        │
│                            │ • 2FA (zukünftig)            │
│                            │                              │
│ 2. HOME PAGE                │ • Dashboard sieht:           │
│ (Startseite)                │ • "Empfehlungen für dich"    │
│                            │   (basiert auf Interessen:   │
│                            │    "Finance", "Excel")       │
│                            │ • Featured Nanos             │
│                            │ • Recent activity            │
│                            │                              │
│ 3. SEARCH & FILTER          │ • Sandra gibt ein:           │
│ (Recherche)                 │ • Suchfeld: "Excel pivot"   │
│                            │ • Filter: Dauer <1h,        │
│                            │   Level: 1-2                │
│                            │   Sprache: Deutsch          │
│                            │ • Ergebnisse: 7 Nanos        │
│                            │                              │
│ 4. EVALUATION               │ • Sorted by: Rating (Top)   │
│ (Bewertungen prüfen)        │ • Erstes Nano:              │
│                            │   - "Pivot-Tabellen         │
│                            │     verstehen"               │
│                            │   - 4.7 ★ (230 Bewertungen) │
│                            │   - Creator: VHS Hannover    │
│                            │   - Dauer: 45 min            │
│                            │ • Sandra klickt zur Detail   │
│                            │                              │
│ 5. DETAIL INSPECTION        │ • Nano-Seite:               │
│ (Detailansicht)            │ • Vollständige Beschreibung  │
│                            │ • Kommentare lesen:          │
│                            │   "Sehr praxisorientiert!"   │
│                            │   "Auch für Anfänger klar"   │
│                            │ • Creator-Profil prüfen:     │
│                            │   "VHS Hannover - 50+ Nanos" │
│                            │   "Verifiziert ✓"            │
│                            │ • Lizenz: CC-BY (kann ich    │
│                            │   team-intern nutzen)        │
│                            │                              │
│ 6. FAVORITES & LIST         │ • Herz-Button klicken        │
│ (Sammlung erstellen)        │ • In Liste "Excel Training"  │
│                            │   speichern (neue Liste)     │
│                            │ • Weitere Nanos hinzufügen   │
│                            │ • Favoriten-List: 5 Nanos    │
│                            │   gesammelt                  │
│                            │                              │
│ 7. COMMUNICATION            │ • Frage: "Kann das auch      │
│ (Chat mit Creator)          │   offline durchgeführt       │
│                            │   werden?"                   │
│                            │ • Chat-Button klicken        │
│                            │ • Chat startet...            │
│                            │ • Jana (Creator) antwortet   │
│                            │   in 2h: "Ja, gerne, können  │
│                            │   auch Mixed-Mode            │
│                            │   kombinieren"               │
│                            │ • Sandra: "Prima! Können      │
│                            │   wir eine Custom-Version    │
│                            │   mit Firmendaten machen?"   │
│                            │ • Jana: "Ja, 1.500€          │
│                            │   Customization-Gebühr"      │
│                            │ • Sandra: "Okay, Kontakt     │
│                            │   über die Website"          │
│                            │                              │
│ 8. EXPORT & SHARING        │ • Sandra exportiert ihre      │
│ (Datennutzung)              │   Liste als PDF für Boss      │
│                            │ • Schickt Email mit          │
│                            │   Empfehlungen              │
│                            │ • Boss approves → Vertrag    │
│                            │   mit VHS wird gemacht       │
│                            │                              │
│ 9. DELIVERY & FOLLOW UP     │ • Nanos werden ins          │
│ (Durchführung)              │   Learning-System geladen    │
│                            │ • Team durcharbeitet        │
│                            │ • Sandra sammelt Feedback   │
│                            │ • Sandra gibt auf Plattform │
│                            │   5-Stern Rating ab         │
│                            │ • Kommentar: "Klasse,       │
│                            │   ganzes Team zufrieden"    │
└─────────────────────────────┴──────────────────────────────┘
```

### Ergebnisse & Metriken

| Metrik | Ziel |
|--------|------|
| Time to Decision | <30 Min (nicht >2h) |
| Conversion (View→Download) | >30% |
| Satisfaction (Feedback) | 4.5+ ★ avg |
| Repeat Purchase Rate | >50% follow-up |

### Pain Points & Lösungen

| Problem | Lösung |
|---------|--------|
| Zu viele Ergebnisse | Bessere Filter + Faceted Search |
| Zu wenig Info über Creator | Trust-Badges, Verifikations-Status |
| Chat-Verzögerung | SLA für Creator (response <24h) |
| Integr. mit LMS fehlt | Phase 1: SCORM-Export |

---

## 4. Journey: Admin — DSGVO-Anfrage bearbeiten (Datenlöschung)

**Persona:** Frank, 35, Datenschutzbeauftragter. Erhält DSGVO-Anfrage von Nutzer Klaus.

### Schritte

```
┌──────────────────────────┬──────────────────────────────┐
│    JOURNEY PHASE         │        AKTIONEN              │
├──────────────────────────┼──────────────────────────────┤
│ 1. REQUEST RECEPTION     │ • Klaus sendet Email:        │
│ (Anfrage ankommen)       │   "Ich möchte meine Daten    │
│                          │   gelöscht sehen DSGVO Art.17"│
│                          │ • System: Ticket auto-create │
│                          │                              │
│ 2. IDENTIFICATION        │ • Frank verifiziert:         │
│ (Identitätsprüfung)      │ • E-Mail gehört zu User Klaus│
│                          │ • User_ID: #12345            │
│                          │                              │
│ 3. DATA INVENTORY        │ • Frank navigiert zu Admin   │
│ (Was haben wir?)         │   → "DSGVO Tools"           │
│                          │ • Daten von Klaus:           │
│                          │   - Profile: Name, Email    │
│                          │   - 5 hochgeladene Nanos    │
│                          │   - 20 Chat-Konversationen  │
│                          │   - 50 Ratings & Comments   │
│                          │   - Login-Logs (6 Monate)   │
│                          │                              │
│ 4. LEGAL CHECK           │ • Frank prüft:              │
│ (Rechtsabwägung)         │ • Recht auf Löschung Art.17 │
│                          │ • Aber: Nanos von anderen   │
│                          │   genutzt/bewertet          │
│                          │   → Pseudonymisierung       │
│                          │   statt Hard-Delete          │
│                          │ • Decision: Anonymize + Log │
│                          │                              │
│ 5. DATA EXPORT           │ • Frank klickt: "Daten      │
│ (Datensicherung vor Del) │   exportieren"              │
│                          │ • ZIP generiert mit:        │
│                          │   - Klaus's Profil (JSON)   │
│                          │   - Alle seine Nanos (ZIP)  │
│                          │   - Chat-Transcripts (txt)  │
│                          │ • Frank speichert ZIP lokal  │
│                          │ • Klaus zugeschickt (Email) │
│                          │                              │
│ 6. ANONYMIZATION         │ • Frank klickt: "Nutzer     │
│ (Daten anonymisieren)    │   anonymisieren"            │
│                          │ • System führt:             │
│                          │   - User.name = "User_12345"│
│                          │   - User.email = deleted    │
│                          │   - User.username = deleted │
│                          │   - User.account_active=0   │
│                          │ • Nanos bleiben, aber jetzt │
│                          │   ohne verfolgbarer         │
│                          │   Beziehung zu Klaus        │
│                          │ • Chat-Nachrichten:        │
│                          │   Benutzer → "Gelöschter In" │
│                          │                              │
│ 7. CONFIRMATION & LOG    │ • System loggt:             │
│ (Bestätigung)            │   WHO: Frank (Admin_ID#1)   │
│                          │   WHEN: 2025-02-24 10:15    │
│                          │   WHAT: User #12345         │
│                          │   anonymized (Request)      │
│                          │   Reason: GDPR Art. 17      │
│                          │                              │
│ 8. NOTIFICATION          │ • E-Mail an Klaus:          │
│ (User informieren)       │   "Anfrage bearbeitet.      │
│                          │   Ihr Account wurde         │
│                          │   anonymisiert. Neben-      │
│                          │   stellen bereits gelöscht." │
└──────────────────────────┴──────────────────────────────┘
```

---

## 5. Journey: Konsument — Negative Bewertung schreiben & Appeal

**Persona:** Robert, 28, nutzt Nano zum Lernen. Findet das Nano nicht hilfreich.

### Schritte

```
1. DISCOVERY: Robert sicht Nano "Power BI Basics" (4.2 ★)
2. DECISION: Trotzdem probiert (günstig via Tausch)
3. CONSUMPTION: 45 Min durchgearbeitet → "Zu schnell, skip Praxis"
4. FEEDBACK: 2 ★ Rating + Kommentar hinterlegen:
            "Zu oberflächlich für tatsächliche Umsetzung"
5. CREATOR RESPONSE: Creator Jana antwortet:
            "Danke für Feedback! Level 1 ist bewusst Intro.
             Hast du Level 2 probiert?"
6. RESOLUTION: Robert probiert Level 2 → "Besser!" → Update Rating zu 4 ★

METRIC: Creator Response Time <24h → Retention ↑
```

---

## 6. Journey: Moderator — Content-Flag mit Plagiarismus (Zukünftig)

**Persona:** Lisa, 33, Content-Moderator. Prüft flagged Nano.

### Schritte

```
1. FLAG-NOTIFICATION: Nutzer meldet "Plagiarismus verdacht" an Nano "Data Science 101"
2. QUEUE: Lisa sieht Flag in "Content Moderation Queue"
3. INVESTIGATION: 
   - Lädt Nano-ZIP
   - Vergleicht mit Original-Quelle (Google/Source)
   - Findet: 70% Textübereinstimmung mit Udemy-Kurs
4. ESCALATION: Lisa findet Urheberrechts-Verletzung
5. CREATOR-CONTACT: Lisa sendet Message an Creator:
            "Plagiarismus-Verdacht. Bitte antworte bis 48h"
6. DECISION:
   - Falls Creator nicht antwortet: Nano archivieren
   - Falls Creator erklärt (z.B. "hat Lizenz"): Verifizieren
   - Falls Fehler zugestanden: Archivieren + Warn-Notice
```

---

## Zusammenfassung: Kernerkenntnisse aus Journeys

| Erkenntes | Impact | Implementierung |
|-----------|--------|-----------------|
| Creator braucht schnelles Feedback | Timeline <48h | Moderator SLA definieren |
| Nachfrager fürchten Qualität | Trust-Signals needed | Verifikations-Badges |
| Chat ist kritisch für Deals | Real-time wichtig | WebSocket-Priority Phase 1 |
| DSGVO nicht einfach | Admin-Tools nötig | Dedicated DSGVO-Modul |
| Moderation ist manual-heavy | Bot-Support erforderlich | KI-Classifier Phase 1 |

---

## Referenzen

- [01 — Stakeholder & Rollen](./01_stakeholder_roles.md)
- [02 — Fachliche Anforderungen](./02_requirements.md)
- [08 — Backlog & Roadmap](./08_backlog_roadmap.md) (User Stories)
