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

## Ergänzung Issue #63 (Search QA/NFR Gate)

- Für das Python-Meilisearch-SDK `index.search(query, options)` verwenden; `q=...` als Keyword wie in REST führt zu Laufzeitfehlern.
- Latenztests für Suchsysteme besser gegen Engine-Metriken (`processingTimeMs`) statt reiner End-to-End-HTTP-Zeit baselinen, damit CI-Streuung/Container-Overhead nicht zu falschen NFR-Fehlschlägen führt.
- In Docker-Compose die App-internen Service-URLs explizit setzen (`MEILI_URL=http://meilisearch:7700`), da `localhost` im Container-Kontext auf den App-Container selbst zeigt.
- PowerShell-Healthchecks in VSCode-Tasks sollten Exit-Codes statt String-Matches auf stdout prüfen; das macht Readiness-Loops stabiler und verhindert „false negative“ Timeouts.
- Search-Contract-Änderungen (Filterparameter und `meta`-Struktur) immer synchron in Backend-Schemas, Frontend-Mapping und Tests aktualisieren, um Drift zwischen API und UI zu vermeiden.

## Review-Nachtrag PR #68

- Live-Integrationstests gegen externe Services dürfen keine produktiv/standardmäßig genutzten Ressourcen mutieren; immer isolierte, test-spezifische IDs/Namespaces verwenden.
- Async-Tests dürfen keine blockierenden SDK-Calls in Schleifen ausführen; entweder native async Clients nutzen oder Sync-Aufrufe explizit in Worker-Threads auslagern.
- Gemeinsame Query-Normalisierung (z. B. Level-Mapping) an einer zentralen Stelle halten und in UI + API-Client wiederverwenden, um Drift zwischen URL-State und Request-Parametern zu vermeiden.

## Ergänzung Issue #64 (Search UI/API Integration)

- Für Search-UX nicht nur Contract-Mapping testen, sondern explizit den UI-Error-Path (API-Fehler → lokalisierte Fehlermeldung) im Page-Test absichern.
- Für CI-nahe Frontend-Validierung `vitest run` statt Watch-Mode verwenden; `npm test` kann lokal grün sein, aber ohne `run` nicht deterministisch terminieren.
- **PR-Review (Issue #64):** Mock-Call-Assertions in asynchronen Tests immer in `waitFor` wrappen und `toHaveBeenLastCalledWith` + `toHaveBeenCalledTimes` kombinieren — einzelne naïve `expect(mock).toHaveBeenCalledWith(...)` ohne `waitFor` können bei debounced Effekten flaky sein (Race Condition zwischen DOM-Event und Timer-Auflösung).
- **PR-Review (Issue #64):** Exakte Test-Zählungen (z. B. „295/296 Tests") in Dokumenten/README nicht hart kodieren — Zahlen driften bei jedem neuen Test und führen zu irreführendem Veraltungs-Overhead. Stattdessen CI-Status als autoritative Quelle referenzieren.

## Ergänzung Issue #70 (Prometheus/Grafana Monitoring Baseline)

- Prometheus-Instrumentierung für FastAPI zentral an der App-Fabrik verdrahten und im Test-App-Setup spiegeln, damit `/metrics` in Runtime **und** Tests konsistent verfügbar ist.
- Für Exporter-Container keine Healthchecks verwenden, die auf nicht garantiert vorhandene Tools wie `wget`/`curl` angewiesen sind; lieber image-native Self-Checks oder stabile HTTP-Probes nutzen.
- VSCode-Readiness-Tasks robuster über Docker-Health + expliziten App-Health-Endpunkt prüfen als über hostseitige Inline-Python-Probes mit indirekter Exit-Code-Auswertung.
- Monitoring-Dashboards und Alert-Regeln als provisionierte Dateien versionieren; UI-only-Konfiguration driftet sonst schnell von Compose/Dokumentation weg.

## Ergänzung Issue #71 (Nano Detail View API)

- Für Endpunkte mit teils öffentlicher, teils eingeschränkter Sichtbarkeit (`published` vs. non-`published`) optionales Auth-Dependency (`get_optional_current_user`) im Router verwenden, die finalen RBAC-Entscheidungen aber im Service-Layer zentral halten.
- Download-Zugriff als separaten Endpunkt modellieren und strikt authentifiziert halten; aktueller Contract: Der Detail-Endpunkt gibt die Download-Info als Capability-Hinweis (`can_download`) zurück und – falls `true` – zusätzlich den konkreten `download_path`, der mit dem aus `/nanos/{id}/download-info` übereinstimmen muss.
- Einheitliches API-Envelope-Schema (`success/data/meta/timestamp`) für neue Read-Endpunkte früh in dedizierten Pydantic-Schemas modellieren, damit Router/Service/Tests denselben Contract erzwingen.
- Für nicht veröffentlichte Inhalte 401 (kein Token) und 403 (Token ohne Berechtigung) explizit unterscheiden; das vereinfacht Frontend-Routing und verhindert unscharfe Error-States.
- Service-Layer-Helfer für Zugriffslogik (z. B. `creator/admin/moderator`) kapseln, um RBAC-Regeln zwischen Detail- und Download-Flow ohne Drift wiederzuverwenden.

## Ergänzung Issue #72 (Creator Dashboard + Moderation Workflow)

- Bei Tailwind-Setups mit vollständigem `theme.colors`-Override funktionieren Default-Klassen wie `bg-blue-600`/`text-red-700` nicht; UI muss konsequent projektweite Tokens (`primary|error|warning|success|info|neutral`) verwenden, sonst entstehen unsichtbare Buttons/Badges.
- Neue Workflow-Status (`pending_review`) sollten an drei Stellen synchron eingeführt werden: Backend-State-Machine, API-Contracts (Schemas/Clients) und Frontend-Filter/Badges, damit keine stillen Inkonsistenzen zwischen UI und API entstehen.
- Rollenwechsel im Status-Endpoint (Creator vs. Moderator/Admin) am Service-Eingang klar trennen; so werden ungewollte Direkt-Publish-Pfade früh blockiert und Tests bleiben deterministisch.
- Für neue statische Routen wie `/my-nanos` Routenreihenfolge explizit testen, damit sie nicht vom dynamischen `/{nano_id}`-Pfad überschattet werden.
- Bestätigungsmodale für destructive/irreversible Aktionen (Submit/Withdraw/Delete) erhöhen Workflow-Sicherheit; Confirm-Button-Labels sollten den aktuellen Async-Zustand widerspiegeln (`Submitting...`, `Withdrawing...`, `Deleting...`).
## Review-Nachtrag PR #77 (Creator Dashboard + Moderation Workflow - Nachbesserungen)

- **RBAC immer vor No-op-Short-Circuit prüfen:** Wenn ein Service-Endpunkt vorzeitig mit "already-in-state" zurückkehrt, muss der Autorisierungscheck dennoch zuerst erfolgen - andernfalls können Unbefugte die Ressourcenexistenz durch den No-op-Pfad ableiten (Resource-Enumeration-Schwachstelle).
- **Creator-mit-Moderatoren-Rolle darf eigene Nanos genehmigen:** Ein Nutzer mit beiden Rollen (Creator + Moderator/Admin) darf seinen eigenen Nano direkt auf `published` setzen; der Blocker `is_creator and new_status == "published"` muss daher durch `is_creator and not is_moderator_or_admin` eingeschränkt werden.
- **Moderatoren-Übergänge auf Allowlist beschränken:** Moderator-seitige Status-Transitionen explizit auf `{published, draft}` begrenzen; ohne Allowlist können sie Nanos direkt auf `archived`, `deleted` o. ä. setzen.
- **Deletierbarkeit nicht nur auf `published` prüfen:** Der Delete-Endpunkt darf nur `DRAFT` und `ARCHIVED` zulassen; `PENDING_REVIEW` war bisher nicht blockiert und hätte Moderations-Workflow-State korrumpiert.
- **SQLAlchemy-Status-Mutations immer committen:** Eine Objekt-Mutation wie `nano.status = NanoStatus.DELETED` reicht nicht - ohne `await db.commit()` + `await db.refresh(nano)` danach wird die Änderung nicht persistiert.
- **`invalidate_search_cache` nimmt `reason: str`, kein Session-Objekt:** Falsche Argument-Übergabe (`invalidate_search_cache(db)`) führt zu einem stillen Runtime-Fehler; korrekt ist `invalidate_search_cache(reason="...")`.
- **`AuditLogger.log_action` Signatur: `session=db, metadata=dict`:** Falsche Keyword-Argumente (`event_data`, `db`) verursachen Runtime-Exceptions nach successivem Commit; korrekte Keys sind `session=db` und `metadata={...}`.
- **API-Enum-Parameter im Service validieren:** Query-Parameter wie `status_filter` als rohe Strings direkt in SQL-Filter zu übergeben, ohne vorher gegen das Enum zu prüfen, erlaubt ungültige Werte; stattdessen immer `NanoStatus(value)` in try/except und HTTP 400 bei ungültigem Wert.
- **Duplikate in API-Exporten vermeiden:** Wenn eine Funktion bereits in einem Feature-Modul (`creator.ts`) definiert und re-exportiert wird, darf sie nicht nochmal in einem anderen Utility-Modul (`upload.ts`) definiert werden - TypeScript meldet `TS2300 Duplicate identifier` bei doppelter Re-Export aus `index.ts`. Kanonischen Ort wählen und dort konsolidieren.
- **Upload-Wizard-Endschritt muss `pending_review` senden, nicht `published`:** Creators erhalten sonst einen 403-Fehler vom Backend-RBAC-Guard. Der Wizard-Step repräsentiert "Submit for Review", nicht "Publish", und muss entsprechend beschriftet und verdrahtet sein.
