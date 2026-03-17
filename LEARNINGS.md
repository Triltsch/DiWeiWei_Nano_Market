# LEARNINGS (kompakt, nur für Umsetzung)

Ziel: Nur Regeln, die Umwege/Fehler in späteren Implementierungen vermeiden.  
Kein Projektbericht, keine Historie, kein Story-Log.

## Frontend: React/UX

- `useEffect` mit Async-Call immer mit `try/catch` + sichtbarem Fehlerzustand.
- Bei asynchronen Effekten immer Abbruchschutz (`isActive`/Cleanup) gegen Updates nach Unmount.
- UX-relevante Magic Numbers (z. B. Debounce, Page Size) als Modulkonstanten definieren.
- Bidirektionale URL-State-Synchronisation nur mit Write-Guard (`useRef`) gegen Feedback-Loops.
- Alle sichtbaren Texte über `t()` (auch Helper-Labels/Fallbacks/Fehlermeldungen).
- Komponenten, die mehrfach gerendert werden können, dürfen keine statische `id` nutzen → `useId()`.
- Backend-Felder am Boundary ehrlich typisieren (z. B. `string | null`) und Fallback erst im Rendering lokalisieren.

## Frontend: Tests & Typisierung

- Hook-Tests verhaltensbasiert schreiben (Lifecycle, `enabled`, `refetch`, Error-Path), nicht nur „existiert“.
- In Tests kein `any`; konkrete Library-Typen verwenden.
- Async-Interceptor/Handler in Tests immer mit `await`/`rejects` prüfen.
- Wenn ein Testwert erfasst wird, muss er explizit asserted werden.

## Backend/API: Architektur

- Business-Regeln in den Service-Layer, Router nur HTTP/DI.
- Ownership-/Autorisierungschecks im Service-Layer vor jeder Mutation.
- Stateful Regeln (z. B. Status-Übergänge) als explizite State-Machine (Transition-Map) implementieren.
- Idempotenz bevorzugen: No-op Updates früh erlauben und sauber zurückgeben.
- Audit-Logging erst nach erfolgreichem Commit.
- Zeitvergleiche defensiv: naive/aware Datetimes vor Berechnung normalisieren.

## Backend/API: Security & Konfiguration

- CORS: `allow_credentials=True` nur mit expliziten Origins (nie `*`).
- Vite-Proxy ist nur Dev; Docker/Prod braucht echte CORS-fähige Backend-Konfiguration.
- Infrastrukturfehler (z. B. DB down) am API-Rand gezielt auf stabile HTTP-Fehler mappen (nicht breit alles fangen).
- Passwort-Hashing-Kompatibilität in CI beachten (passlib/bcrypt-Versionen reproduzierbar pinnen).

## Docker/Runtime

- Shell-Entrypoints im Image auf LF normalisieren (CRLF verursacht irreführende „file not found“-Fehler).
- Bei Vite-Multistage-Build `frontend/public` explizit in den Build-Kontext kopieren.
- Backend-Root-Redirect über Umgebungsvariable steuern (lokal vs. Docker nicht hart codieren).

## Test-Infrastruktur

- Test-App muss Router-Setup der Produktiv-App spiegeln, sonst entstehen falsche 404-Befunde.
- Fixture-Abhängigkeiten explizit aufbauen (User → Auth/Token → Ressource), sonst FK-/State-Probleme.
- Wiederverwendbare Auth-Token-Fixture zentral bereitstellen statt Login-Setup pro Test.
- Performance-Tests CI-stabil halten (`perf_counter`, tolerante Schwellen, keine flakey Single-Run-Annahmen).

## Doku-/Review-Disziplin

- Doku-Codeblöcke müssen mit echter Implementierung konsistent sein (keine „Beispiel“-Drift).
- Änderungen an Fehlerverhalten/CORS/Auth immer auch in API-Doku/README nachziehen.
- Bei PR-Automation: API kann Review-Kommentare unvollständig liefern → bei Unklarheit UI prüfen.

## Schnell-Check vor Merge

- Sind neue User-Texte vollständig i18n-fähig?
- Gibt es Async-Fehlerpfade mit sichtbarem UI-Feedback?
- Ist URL↔State-Sync loop-sicher?
- Sind Service-Regeln + Ownership + Audit vollständig abgedeckt?
- Spiegelt Test-Setup die produktive Router-/Dependency-Struktur?
- Sind Docker-/Env-Pfade (Origins, Frontend-URL, Assets, Line Endings) korrekt?

## Ergänzung Issue #62 (Redis Search Cache)

- Search-Cache-Keys immer vollständig und deterministisch aus **allen** Query-Parametern bauen (`q`, `category`, `level`, `duration`, `page`, `limit`), sonst entstehen falsche Cache-Hits.
- Cache-Invalidierung bei content-relevanten Writes (hier: Nano-Metadaten + Statuswechsel) zentral aus dem Service-Layer triggern.
- Redis-Ausfälle dürfen Search nicht blockieren: Cache `get/set/invalidate` defensiv kapseln, Live-Search als Fallback (degraded mode).
- Healthcheck sollte Degraded-Zustand sichtbar machen (`status: degraded`, `services.redis: down`) statt nur pauschal `ok`.
- Tests für Search-Service immer Redis mocken, wenn Meilisearch-Aufrufe asserted werden; sonst werden Tests durch reale Cache-Hits flakey.

## Review-Nachtrag PR #67

- Für Redis-Key-Löschung in produktionsnahen Pfaden nie `KEYS` verwenden; stattdessen `SCAN`/`scan_iter` mit Batch-Deletes, um Blocking-Latenzen zu vermeiden.
- Cache-Logging darf keine Roh-Keys mit User-Query enthalten; stattdessen nur gehashte Key-Fingerprints loggen.
- Health-Endpunkte dürfen bei Redis-Störung nicht hängen: `ping()` mit kurzem Timeout kapseln (z. B. `asyncio.wait_for`).
- Pagination-Tests müssen mindestens erste, mittlere und letzte Seite abdecken, damit `has_next_page`/`has_prev_page` nicht regressieren.