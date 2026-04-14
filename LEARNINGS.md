# LEARNINGS

Kompaktes Regelwerk für Implementierung, Review und Qualitätssicherung.

## Frontend

### Async & Effects
- `useEffect` async-Flows: `try/catch` + sichtbarer Fehlerzustand + Abbruchschutz (`isActive` Flag + Cleanup bei Unmount).
- Präferenzfelder (Sprache): UI-State sofort updaten, NICHT auf Backend-Response warten; sonst wird Nutzer-Änderung von Response überschrieben.
- URL↔State-Sync mit Write-Guard (`useRef`) um Feedback-Loops zu verhindern.
- Magic-Numbers (Debounce, Page Size, Timeouts) als Modulkonstanten definieren.

### Lokalisierung & Typisierung
- Alle sichtbaren Strings über `t()` lokalisieren (mit Fallbacks und Fehlermeldungen).
- Keine statischen `id`-Werte in wiederverwendbaren Komponenten; `useId()` nutzen.
- API-Boundary ehrlich typisieren: `string | null`, optionale Felder; Fallbacks erst im Rendering.
- Detail-/Action-UX auth- und statusbewusst: `!isAuthenticated` → früh redirecten, nur mögliche Aktionen anbieten.

### Routing & RBAC
- Route-Guards mit `requiredRoles` implementieren; Navigation rollenbasiert rendern (Links + API-Berechtigung konsistent).
- JWT `role` zentral in User-State; nach Refresh neu ableiten.
- API-Clients pro Domäne kapseln, HTTP-Status auf typisierte Fehlercodes mappen.
- 401 vs. 403 explizit trennen: 401 = Re-Login, 403 = Forbidden-State.
- 409-Konflikte: Backend-`detail` gezielt auswerten (z. B. Username vs. E-Mail), nicht pauschal behandeln.
- Redirect nach Login gegen Open-Redirect-Regeln validieren, dann role-backed Fallback.
- Self-Service-Endpunkte (Passwort/Profil): Bei Business-Validierungsfehlern können Auth. Nutzer 401 erhalten. Interceptor muss `_retry`-Flag prüfen, nicht blindlings Logout auslösen.

### Frontend Tests
- Verhaltensbasierte Tests: Lifecycle, Error-Paths, Refetch, Redirects (nicht nur Existenzprüfungen).
- Keine `any`-Types; konkrete Library-Typen verwenden.
- i18n-Tests: Nach Sprachwechsel auf neue Sprache in Labels/Buttons asserten; alte sind dann weg aus DOM.
- Debounced/async Assertions: Call-Count + Last-Call kombinieren.
- CI: `vitest run` statt Watch-Mode; Testanzahlen nicht hardcoden (CI ist Quelle der Wahrheit).

## Backend / API

### Architecture & Layering
- Business-Regeln in Service-Layer; Router nur für HTTP/DI.
- Autorisierung/Ownership VOR Mutation und vor No-op-Short-Circuits.
- Stateful Logik als explizite State-Machine/Transition-Allowlist modellieren.
- Idempotente Updates zulassen ohne Informationsleck für Unbefugte.
- Optional-Auth im Router, zentrale Zugriffsentscheidung im Service.

### Content & Moderation
- Öffentliche APIs nur freigegebene Inhalte zeigen; Moderations-/Pending-Reads separieren.
- Nach Content-Updates Moderationsstatus auf `pending` zurücksetzen, Metadaten bereinigen.
- Admin-Takedown: Dedizierte Endpoint-Semantik, idempotente Wiederholung, strukturierte Audit-Metadaten, explizite Cache-Invalidierung.
- User-Flagging robust über drei Ebenen absichern: Service-Guard (Self-Flag 403), DB-Unique-Constraint (`nano_id`,`flagging_user_id`) + `IntegrityError`→409, und sofortige `ModerationCase`-Verknüpfung mit `reporter_id`.

### Validierung & Sicherheit
- Query-/Enum-Parameter serverseitig validieren; ungültige Werte → sauber 4xx.
- Response-Schema vollständig: alle updatebaren Felder enthalten, sonst API-Vertrag-Bruch + Testfehler.
- Self-Service-Profilupdates: Response muss alle Felder (z. B. `company`, `job_title`, `phone`) enthalten.
- CORS: Credentials nur mit expliziten Origins (nie `*`).
- Infrastrukturfehler am API-Rand gezielt auf stabile HTTP-Fehler mappen.
- In FastAPI `HTTP_422_UNPROCESSABLE_CONTENT` statt `HTTP_422_UNPROCESSABLE_ENTITY` (vermeidet DeprecationWarnings).
- Für Base-URL-Normalisierung ist `urlparse()` allein bei schema-losen `host:port`-Werten unzuverlässig (`host` wird als `scheme` interpretiert); robustes Schema-Detection über `://` (plus Empty-Check nach `rstrip('/')`) verhindert fehlerhafte Verifikationslinks.

### Data Integrity & Error Handling
- DB-Constraints + Service-Guards kombinieren (z. B. `UNIQUE` + 409-Precheck + `IntegrityError`-Handling).
- `IntegrityError` bei konkurrenten Creates: nach `rollback()` existierende Zeile re-selecten, `reused=True` returnen (Race-Condition-Resilienz).
- Create-or-reuse: HTTP-Semantik explizit (`201` = neu, `200` = reuse).
- Paarweise Session-Identität: Teilnehmerreihenfolge deterministisch normalisieren für Eindeutigkeit.
- Denormalisierte Aggregatfelder zentral und konsistent neu berechnen.
- Pagination stabil über deterministische Sortierung + Tie-Breaker (z. B. `order_by(created_at.asc(), id.asc())`).
- User-Content normalisieren/sanitizen, auf persistiertem Wert validieren.

### Passwort-Hashing & Bcrypt
- Passwort-Hashing-Abhängigkeiten reproduzierbar pinnen (CI-kompatibel).
- Wenn nur bcrypt benötigt: direkte `bcrypt`-Nutzung statt `passlib` (vermeidet Python-3.13-DeprecationWarnings um stdlib-`crypt`).
- SHA256-Pre-Hashing: 64 Bytes Output sicher unter bcrypt 72-Byte-Limit.

### SQLAlchemy & Async
- Nach `commit()`: ORM-Objekte mit `onupdate`-Feldern (z. B. `updated_at`) per `await session.refresh(obj)` laden, sonst `MissingGreenlet`.
- Neue SQLAlchemy-Modelle/Enums auf Top-Level einfügen (nicht eingerückt in Klassen); verschachtelte Definitionen → `NameError`/Typauflösungsfehler erst zur Laufzeit.
- Config-Validierung: nur Felder strikt typisieren, deren bestehende `.env`-Werte sicher passen; spezialisierte Typen (z. B. `EmailStr`) in nested Models, um Startup-Regressionen durch Legacy-Werte zu vermeiden.

### SMTP & Fehlerbehandlung
- Input-Validierungsfehler (z. B. CRLF-Header-Injection): nicht in generische Delivery-Retries überführen; `ValueError` direkt throwthrough.
- Nur transient 4xx-Zustände wiederholen; Timeout/Connect klar auf stabile Delivery-Fehler mappen.
- Mailpit SMTP: `login()` nur ausführen wenn AUTH unterstützt + Credentials gesetzt (vermeidet 503 in Auth-Flows).

### Policy & Audit
- API-Dependencies und Signaturen strikt typkonsistent halten.
- Audit-Logging fault-tolerant (Savepoint/try-catch): fehlgeschlagener Audit-Insert darf Entscheidung nicht rückgängig machen.

## Search, Cache, Redis

- Cache-Keys vollständig + deterministisch aus allen Query-Parametern bilden.
- Cache-Invalidierung zentral im Service-Layer bei relevanten Writes triggern.
- Key-Löschung in produktionsnahen Pfaden: `SCAN` statt `KEYS`.
- Redis-Ausfälle: degraded Fallback + Recovery-Strategie (blockieren nicht Kernfunktionen).
- In-Memory-TTL-Stores: bei `set` prunen; `expires_in_seconds <= 0` = sofortiges Entfernen.
- Cache-Logging ohne Roh-User-Queries (nur sichere Fingerprints).
- Search-/Filter-Contracts sync halten: Backend + Frontend + Tests gleichzeitig updaten.

## Observability & Monitoring

- Generische HTTP-Metriken durch fachliche Flow-Metriken ergänzen (niedrige Label-Kardinalität).
- FastAPI-Metriken robust über `APIRoute`-Wrapper + Exception-Pfade instrumentieren.
- Moderationsentscheidungen als eigene Event-Metrik zählen.
- Monitoring-Artefakte (Dashboards, Alerts) als versionierte Dateien verwalten.
- Alert-Regeln: einheitenkonsistent (`rate()` = pro Sekunde, `increase()` = absolut); bei Quoten-Metriken Mindest-Traffic-Guard gegen False-Positives.
- Healthchecks auf robuste, image-native Probes stützen (keine fragilen Tool-Abhängigkeiten).

## Docker, Runtime, Migrationen

- Bei `docker-compose.yml`-`command: >` mit `/bin/sh -c` OpenSSL-Aufrufe als einzelne Kommandozeile (oder mit expliziten `\`-Fortsetzungen) schreiben; sonst können Flags wie `-keyout` als eigene Shell-Kommandos ausgeführt werden.
- Nginx-Upstreams auf optionale Services (z. B. Grafana) nicht als statischen `upstream` beim Startup erzwingen: request-time DNS mit `resolver 127.0.0.11` + `proxy_pass http://$variable` verhindert `host not found`-Bootloops.
- Service-URLs im Container: explizit setzen (kein `localhost`-Default).
- Nach Docker-Image-Rebuilds mit geänderten Python-Abhängigkeiten den App-Container per `docker compose up -d --force-recreate app` neu erzeugen; ein bloßes `up -d` kann einen laufenden Container mit veraltetem Site-Packages-Stand stehen lassen.
- Integrations-Tasks (`Test: Verified`): alle benötigten Services in Readiness-Checks (z. B. Mailpit + App/DB/Redis).
- Runtime-Pfade (Root-Redirects, API-Bases) über Umgebungsvariablen steuern.
- Services mit Host-Port-Mapping: zusätzlich nicht-internes Bridge-Netzwerk anbinden (nur `internal: true` – kein Host-Zugriff).
- Alembic-Recovery: `stamp base` → `upgrade head`.
- Enum-Migrationen PostgreSQL: korrekte Reihenfolge (Type anlegen/nutzen/droppen).
- SQLAlchemy `Enum(MyEnum)` persistiert Namen (z. B. `PENDING`), nicht `.value` (z. B. `pending`); PostgreSQL-Enum-Werte müssen passen oder Model explizit auf `.value` konfigurieren.
- Neue Enum-Mitglieder in produktiven PostgreSQL-Types: dedizierte Alembic-Migration mit `ALTER TYPE ... ADD VALUE`.
- Jedes neue SQLAlchemy-Modell: Alembic-Migration nötig. Tests mit `Base.metadata.create_all` maskieren fehlende Migrationen.
- `nano_id`-Filter-Queryparameter + `meta.nano_filter_applied` in Tests explizit testen, nicht nur Abwesenheits-Fall.

## MCP / Tooling

- `mcp_github_pull_request_read` ist NICHT gültig. Korrekte Tool-Namen: `mcp_github_get_pull_request`, `mcp_github_get_pull_request_reviews`, `mcp_github_get_pull_request_review_comments`, `mcp_github_get_pull_request_comments`.
- MCP-Tools müssen zur Laufzeit vom Server registriert werden. Eintrag in `tools:` erlaubt nur Nutzung.
- Wenn MCP-Tools ausfallen: `github-pull-request_activePullRequest` + `gh pr view/api` als Fallback verwenden; im Report ausweisen welcher Pfad genutzt wurde.

## Tests & QA

### Test Architecture
- App-Setup muss produktives Router-/Dependency-Verhalten spiegeln.
- Fixture-Ketten explizit aufbauen: User → Auth → Ressource; Auth-Token-Fixtures zentralisieren.
- Idempotente API-Flows: Erstaufruf + Wiederholaufruf separat testen (unterschiedliche Statuscodes).

### Integration & Polling
- Bei `?since=`-Queries: `httpx params={"since": cursor}` statt F-String; `+` in ISO-8601-Timezone wird → Leerzeichen → 422.
- `expire_all()` auf SQLAlchemy `AsyncSession`: synchrone Methode (kein `await`).
- Wenn Test + App dieselbe `AsyncSession` teilen: ORM-Objekte nach Service-Commit direkt aktualisiert (Identity-Map); expliziter Refresh unnötig.
- Chat-Session-Writes: `session.last_message_at` in derselben DB-Transaktion updaten für sortiertes Session-Listing.

### Quality Standards
- Performance-/Latenztests: CI-stabil halten (tolerante Schwellen, stabile Metriken, keine Flakes).
- QA-Gates: reproduzierbare Befehle + evidenzbasierte Ergebnisse dokumentieren.
- Ergebnisse aus frischen vollständigen Läufen ableiten, nicht gemischter Task-Historie.
- Doku + Implementierung synchron (Codeblöcke, Contracts, Fehlerverhalten).
- Keine nicht versionierten Workspace-Annahmen in Gate-/Ops-Dokumente.

### PR Automation
- Bei Doku-Änderungen Codefences auf Balance prüfen.
- Unvollständige Comment-Daten einkalkulieren; bei Unklarheit in der UI verifizieren.

## Merge-Checkliste

- Alle neuen UI-Texte lokalisiert?
- Async-Fehlerpfade mit sichtbarem Nutzerfeedback?
- URL↔State-Sync, Auth-Redirects, RBAC-Guards loop-sicher?
- Service-Regeln, Ownership, Status-Transitionen, Audit vollständig?
- Test-Setup spiegelt produktive App-Struktur?
- Cache-/Search-Invalidierung + degraded Fallbacks abgedeckt?

## Chat UI (Frontend)

- Absender-Labels rollenbasiert auflösen: `senderId === user?.id` → "Ich", `senderId === session.creatorId` → Verkäufer-Label, sonst → Käufer-Label (nie Fallback-Label hardcoden).
- Creator `POST /chats` → Backend 403 (Creator kann Session nicht initiieren). Frontend-Fallback: `GET /chats?nano_id=...` (listChatSessions), kein Fehler anzeigen.
- Chat-Session-Abfragen rollenbasiert: Creator → `WHERE creator_id = current_user.id`, Teilnehmer → `WHERE participant_user_id = current_user.id AND creator_id = nano.creator_id`.
- Docker-/Env-/CORS-/URL-Pfade korrekt?

## Frontend hinter Reverse Proxy

- Vite-Dev über HTTPS-Reverse-Proxy braucht CSP-Ausnahmen für Inline-Assets in Dev (`script-src 'unsafe-inline'` und `style-src 'unsafe-inline'`), aber nur auf Vite/HMR-Asset-Routen (nicht global), um XSS-Schutz auf normalen Seiten strikt zu halten.
- Vite injectet inline React Refresh Preamble in SPA HTML (nicht nur in Asset-Responses). CSP-Ausnahmen müssen daher auf **beide** scoped werden: (1) Vite HMR Asset-Routes (`/@vite`, `/@react-refresh`, ...) und (2) Frontend-Document-Route (`/`, SPA-Entry). Runtime-Verifikation (HTTP-Header einer echten Page-Request) ist kritisch, da statische Config-Inspektion Vite-Injection nicht zeigt.
- CSP-Regression-Tests müssen Scoping validieren (z. B. "relaxed CSP appears exactly 2x"), nicht nur Präsenz. Verhindert versehentliche Globalisierung von `unsafe-inline`.

## QA-Gates & E2E Tests

- User-Journeys abbilden, nicht einzelne Features.
- Test-Fixtures: Creator + Published Nano als Basis für Chat-Tests.
- Rate-Limiting: konfigurierbar testen; Config.py: `RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS=30`, `_WINDOW_SECONDS=60`.
- Polling-Tests: `?since=timestamp`-Filter → `created_at > since` (strikt nach).
- QA-Gate-Befunde dokumentieren: funktioniert, offen, Risiken.
- Chat-Session Determinismus: (nano_id, creator_id, participant_user_id); creator_id = nano.creator_id.
- Message-Ordering: `order_by(created_at.asc(), id.asc())` mit id als Tie-Breaker.

## Spam Prevention / Rate Limiting

- Chat-Rate-Limits mit Burst-Konzept immer als `base + burst` modellieren; QA- und E2E-Tests müssen den ersten `429` auf dem `(base + burst + 1)`-Request prüfen.
- Chat-Rate-Limit-Schlüssel pro Nutzer **und** Session bilden (`user_id + session_id`), damit Last in einer Unterhaltung nicht andere Sessions desselben Nutzers ungewollt blockiert.
- Bei Spam-Filtern die Reihenfolge im Request-Pfad beachten: Rate-Limit vor Content-Filter anwenden, damit geblockte Spam-Versuche ebenfalls das Budget verbrauchen.
- Domain-basierte Filter immer auf normalisiertem Hostname (`urlparse(...).hostname` + IDNA) statt `netloc` bauen, damit Ports keine Blocklisten umgehen.
- Nginx Endpoint-Regexe auf einzelne Pfadsegmente begrenzen (`[^/]+` statt `.+`), um unbeabsichtigte Matches in Rate-Limit-Locations zu vermeiden.

## Admin Panel / Moderation

- KPI-Karten-Zähler von gefilterten Listen-Response entkoppeln (dedizierte API-Anfrage mit `limit=1`). Sonst ändert sich KPI bei Filterwechsel.
- Audit-Logging fault-tolerant (Savepoint/try-catch): fehlgeschlagener Audit-Insert darf Moderationsentscheidung nicht rückgängig machen.
- PostgreSQL-Enum-Typ + SQLAlchemy-Enum sync halten; neue Werte per dedizierter Alembic-Migration (`ALTER TYPE ... ADD VALUE`).
- Legacy-Seiten (flaches Moderator-API-Format) → Case-basiertes Admin-API-Format (`ModerationCaseItem`): alle Helper-Funktionen anpassen (z. B. `content_type`, `target_id`).
- Komponenten mit `<GlobalNav>` (nutzt `useNavigate()`) in Vitest-Tests: `<MemoryRouter>`-Wrapper erforderlich (braucht Router-Kontext).
