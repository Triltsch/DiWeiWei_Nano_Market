# LEARNINGS

Ziel: Ein kompaktes, direkt anwendbares Regelwerk für Implementierung und Review.

## Frontend (UX, State, i18n)

- Asynchrone `useEffect`-Flows immer mit `try/catch` und sichtbarem Fehlerzustand implementieren.
- In asynchronen Effekten immer Abbruchschutz (`isActive` + Cleanup) gegen State-Updates nach Unmount nutzen.
- UX-Magic-Numbers (Debounce, Page Size, Timeouts) als Modulkonstanten führen.
- URL↔State-Sync nur mit Write-Guard (`useRef`) um Feedback-Loops zu vermeiden.
- Alle sichtbaren Strings über `t()` lokalisieren (inkl. Fallbacks und Fehlermeldungen).
- Keine statischen `id`-Werte in wiederverwendbaren Komponenten; `useId()` verwenden.
- API-Boundary ehrlich typisieren (`string | null`, optionale Felder) und Fallbacks erst im Rendering anwenden.
- Detail-/Action-UX auth- und statusbewusst bauen: bei `!isAuthenticated` früh redirecten, nur sinnvolle Aktionen anbieten.

## Frontend (Routing, RBAC, API-Clients)

- Route-Guards rollenfähig umsetzen (`requiredRoles`), nicht nur auth-basiert.
- Navigation strikt rollenbasiert rendern; sichtbare Links und API-Berechtigung müssen konsistent sein.
- JWT-Claim `role` zentral in den User-State übernehmen und nach Refresh neu ableiten.
- API-Clients pro Domäne kapseln (z. B. Feedback, Detail, Search) und HTTP-Status auf typisierte Fehlercodes mappen.
- 401/403 im Frontend explizit trennen: 401 = Re-Login, 403 = Forbidden-State.
- Redirect-Parameter nach Login zuerst gegen Open-Redirect-Regeln validieren, dann role-aware Fallback anwenden.

## Frontend-Tests

- Tests verhaltensbasiert schreiben (Lifecycle, Error-Path, Refetch, Redirect), nicht nur Existenzprüfungen.
- In Tests kein `any`; konkrete Library-Typen verwenden.
- Asynchrone Assertions mit `waitFor`, `await` und `rejects` stabilisieren.
- Debounced/async Mock-Assertions mit Call-Count + Last-Call kombinieren.
- Für CI-nahe Frontend-Läufe `vitest run`/`npx vitest run` statt Watch-Mode nutzen.
- Exakte Testanzahlen nicht in Doku festschreiben; CI ist die autoritative Quelle.

## Backend/API (Architektur, RBAC, Validierung)

- Business-Regeln in den Service-Layer, Router nur für HTTP/DI.
- Autorisierung/Ownership immer vor Mutation und vor No-op-Short-Circuits prüfen.
- Stateful Logik als explizite State-Machine/Transition-Allowlist modellieren.
- Idempotente Updates zulassen, aber ohne Informationsleck für Unbefugte.
- Query-/Enum-Parameter serverseitig validieren und bei ungültigen Werten sauber mit 4xx antworten.
- Optional-Auth im Router verwenden, finale Zugriffsentscheidung zentral im Service treffen.
- Öffentliche APIs nur freigegebene Inhalte zeigen; Moderations-/Pending-Reads separat modellieren.
- Nach Content-Updates Moderationsstatus auf `pending` zurücksetzen und Moderationsmetadaten bereinigen.

## Backend/API (Datenintegrität, Fehler, Security)

- DB-Constraints und Service-Guards kombinieren (z. B. `UNIQUE` + 409-Precheck + `IntegrityError`-Handling).
- Für "create-or-reuse" Endpunkte HTTP-Semantik explizit halten (`201` bei Neuanlage, `200` bei Reuse).
- Bei paarweiser Session-Identität Teilnehmerreihenfolge deterministisch normalisieren, damit Eindeutigkeit robust bleibt.
- Denormalisierte Aggregatfelder zentral und konsistent neu berechnen.
- Pagination stabil über deterministische Sortierung inkl. Tie-Breaker umsetzen.
- User-Content serverseitig normalisieren/sanitizen und auf persistiertem Wert validieren.
- API-Dependencies und Signaturen strikt typkonsistent halten.
- CORS mit Credentials nur mit expliziten Origins konfigurieren (nie `*`).
- Infrastrukturfehler am API-Rand gezielt auf stabile HTTP-Fehler mappen.
- Passwort-Hashing-Abhängigkeiten reproduzierbar pinnen (CI-kompatibel).

## Search, Cache, Redis

- Search-Cache-Keys vollständig und deterministisch aus allen Query-Parametern bilden.
- Cache-Invalidierung zentral im Service-Layer bei relevanten Writes triggern.
- Für Key-Löschung in produktionsnahen Pfaden `SCAN` statt `KEYS` verwenden.
- Redis-Ausfälle dürfen Kernfunktionen nicht blockieren: degraded Fallback + Recovery-Strategie vorsehen.
- Bei Redis-Recovery Read-Miss-Fälle mit best-effort Re-Sync behandeln.
- In-Memory-TTL-Stores bei `set` prunen; `expires_in_seconds <= 0` als sofortiges Entfernen behandeln.
- Cache-Logging ohne Roh-User-Queries (nur sichere Fingerprints).
- Search-/Filter-Contracts gleichzeitig in Backend, Frontend und Tests aktualisieren.

## Observability & Monitoring

- Generische HTTP-Metriken durch fachliche Flow-Metriken ergänzen (niedrige Label-Kardinalität).
- FastAPI-Metriken robust über `APIRoute`-Wrapper inkl. Exception-Pfaden instrumentieren.
- Moderationsentscheidungen als eigene Event-Metrik zählen.
- Monitoring-Artefakte (Dashboards, Alerts) als versionierte Dateien verwalten.
- "No data" in Grafana als erwartbar behandeln, bis gezielter Traffic erzeugt wurde.
- Healthchecks auf robuste, image-native Probes stützen; keine fragilen Tool-Abhängigkeiten.

## Docker, Runtime, Migrationen

- Line-Endings in Entrypoints auf LF normalisieren.
- Vite-Multistage-Builds mit explizitem `frontend/public`-Copy absichern.
- Service-URLs im Container-Kontext explizit setzen (kein `localhost`-Default im Container).
- Runtime-Pfade (Root-Redirects, API-Bases) über Umgebungsvariablen steuern.
- Alembic-Recovery bei inkonsistentem Local-State klar durchführen (`stamp base` → `upgrade head`).
- Enum-Migrationen in PostgreSQL in korrekter Reihenfolge durchführen (Type anlegen/nutzen/droppen).

## Tests, QA, Doku, Review

- Test-App-Setup muss produktives Router-/Dependency-Verhalten spiegeln.
- Fixture-Ketten explizit aufbauen (User → Auth → Ressource); Auth-Token-Fixtures zentralisieren.
- Für idempotente API-Flows sowohl Erstaufruf als auch Wiederholaufruf separat testen (inkl. unterschiedlicher Statuscodes).
- Performance-/Latenztests CI-stabil halten (tolerante Schwellen, stabile Metriken, keine Flakes).
- QA-Gates mit reproduzierbaren Befehlen und evidenzbasierten Ergebnissen dokumentieren.
- Ergebnisse immer aus frischen vollständigen Läufen ableiten, nicht aus gemischter Task-Historie.
- Doku und Implementierung synchron halten (Codeblöcke, Contracts, Fehlerverhalten).
- Keine nicht versionierten Workspace-Annahmen in Gate-/Ops-Dokumente aufnehmen.
- Bei PR-Automation unvollständige Comment-Daten einkalkulieren und bei Unklarheit in der UI verifizieren.
- Bei Doku-Änderungen Codefences explizit auf Balance prüfen.

## Merge-Checkliste

- Sind alle neuen UI-Texte lokalisiert?
- Gibt es für alle Async-Fehlerpfade sichtbares Nutzerfeedback?
- Sind URL↔State-Sync, Auth-Redirects und RBAC-Guards loop-sicher?
- Sind Service-Regeln, Ownership, Status-Transitionen und Audit vollständig?
- Spiegelt das Test-Setup die produktive App-Struktur?
- Sind Cache-/Search-Invalidierung und degraded Fallbacks abgedeckt?
- Sind Docker-/Env-/CORS-/URL-Pfade korrekt?
