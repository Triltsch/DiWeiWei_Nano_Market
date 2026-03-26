---
name: 00_nano_sprint_planning
description: Plane den nächsten Sprint auf Basis von Backlog und Architektur und lege dafür GitHub-Issues an
agent: agent
---

# Objective

> Deine Aufgabe ist ausschließlich die Planung des nächsten Sprints `#{{sprint_number}}` für dieses Softwareprojekt auf Basis der bereitgestellten Dokumentation sowie das Anlegen der dafür nötigen GitHub-Issues.

# Nutzung

- Parameter: `{{sprint_number}}` (Integer, z. B. `5` oder `6`).
- Setze den Parameter vor der Ausführung auf die gewünschte Sprint-Nummer.
- Beispiel-Nutzung: „Plane Sprint `#6` auf Basis der angegebenen Dokumente und lege die zugehörigen GitHub-Issues an.“

# Strikte Grenzen

- Kein Code.
- Keine Implementierung.
- Keine Änderungen am Repository.
- Keine Pull Requests.
- Keine Commits.
- Keine Code-Patches.
- Keine Architekturentscheidungen als bereits umgesetzt darstellen.
- Ausschließlich Analyse, Sprintplanung, Priorisierung, Strukturierung und GitHub-Issue-Erstellung.

# Verbindliche Quellen

Arbeite ausschließlich auf Basis dieser Dokumente:
- `file:/08_backlog_roadmap.md`
- `file:/05_system_architecture.md`

Wenn Informationen außerhalb dieser Dokumente verwendet werden müssen, markiere diese explizit als **Annahme**.

# Pflichtablauf

## A) Dokumente auslesen

1. Lies beide angegebenen Dateien vollständig.
2. Extrahiere und konsolidiere zuerst:
   - Produkt- und MVP-Ziele
   - Sprint- und Roadmap-Plan
   - Stories, Akzeptanzkriterien, Aufwände, Abhängigkeiten
   - Architektur- und Infrastrukturvorgaben
   - Technologieentscheidungen
   - Sicherheits-, Compliance- und Betriebsvoraussetzungen
3. Identifiziere explizit Widersprüche, Lücken und Unklarheiten zwischen beiden Dokumenten.

## B) Konsolidierten Projektstand ableiten

- Ermittle den aktuellen fachlichen und technischen Planungsstand.
- Nutze die dokumentierte Sprintreihenfolge als Primärleitlinie.
- Nutze keine generischen Standard-Sprints, wenn die Dokumentation bereits konkrete Reihenfolge, Stories, Aufwände oder Abhängigkeiten vorgibt.

## C) Kritische Abhängigkeiten und Blocker bestimmen

Prüfe mindestens:
- kritischer Pfad / Blocker
- Enabler vor Feature-Umsetzung
- Abhängigkeiten zwischen Backend, Frontend, Infrastructure und QA
- Unterschiede zwischen MVP und späteren Phasen
- Unterschiede bei Technologie- oder Suchlösungen
- Unterschiede zwischen Epic-/Story-Übersicht und technischen Detailabschnitten

## D) Nächsten Sprint definieren

Plane `Sprint #{{sprint_number}}` so, dass:
- er sich logisch in die vorhandene Roadmap einfügt,
- dokumentierte Abhängigkeiten berücksichtigt,
- nur sprinttaugliche und klar abgrenzbare Arbeitspakete enthält,
- realistisch und umsetzbar bleibt,
- Blocker, Enabler und kritische Infrastruktur zuerst adressiert,
- Backend-, Frontend-, DevOps-/Infrastructure- und QA-Anteile aufeinander abgestimmt sind,
- keine Aufgaben vorgezogen werden, die laut Dokumentation erst für spätere Sprints/Phasen vorgesehen sind (außer zwingend zur Entblockung).

## E) Sprint in GitHub-Issues zerlegen

Lege für alle Sprintbestandteile GitHub-Issues an.

Für jedes Issue erfasse:
- Titel
- Typ (`Feature`, `Bug`, `Tech Debt`, `Infrastructure`, `Security`, `Documentation`, `QA`, `Refactoring`, `Research`)
- Kurzbeschreibung
- Kontext / Begründung
- Scope / konkrete Aufgabe
- Akzeptanzkriterien
- Abhängigkeiten
- Priorität
- Aufwandsschätzung
- passende Labels
- Zuordnung zu Sprint/Milestone (`Sprint #{{sprint_number}}`)

Qualitätsanforderungen an Issues:
- präzise
- umsetzbar
- ohne generische Platzhalter
- direkt teamfähig
- keine Implementierungsdetails als Code, nur Arbeitsbeschreibung und Zielkriterien

## F) Issues in GitHub anlegen

- Erstelle die geplanten Issues in GitHub.
- Die Erstellung der Issues muss über den MCP Server erfolgen.
- Erstelle keine PRs.
- Ändere keine Dateien im Repository.

## G) Ergebnisbericht ausgeben

Nutze exakt diese Reihenfolge:

## 1. Gelesene Quellen
Liste, welche Dateien gelesen wurden.

## 2. Konsolidierter Projektstand
Kurze, präzise Zusammenfassung.

## 3. Annahmen, Lücken, Inkonsistenzen
Explizit und nummeriert.

## 4. Vorschlag für den nächsten Sprint
Mit Begründung, warum genau dieser Sprint als nächster sinnvoll ist.

## 5. Sprintziel
Ein präziser Sprint Purpose.

## 6. GitHub-Issues
Für jedes Issue:
- Titel
- Typ
- Beschreibung
- Scope
- Akzeptanzkriterien
- Abhängigkeiten
- Priorität
- Aufwand
- Labels
- Sprint/Milestone

## 7. GitHub-Aktionen
Bestätige, welche Issues tatsächlich angelegt wurden.

## 8. Risiken und offene Fragen
Klar getrennt.

## 9. Empfehlung für Sprint danach
Kurz und logisch anschlussfähig.

# Wichtige Planungslogik

- Priorität 1: Blocker und technische Enabler.
- Priorität 2: MVP-Kernfunktionalität.
- Priorität 3: Qualität, Tests, Dokumentation, Monitoring, technische Schulden.
- Nice-to-have nur einplanen, wenn dokumentiert sprintreif.
- Widersprüche immer explizit benennen, nie stillschweigend entscheiden.
- Annahmen immer explizit als **Annahme** markieren.

# Ausführungsstart

Starte jetzt mit Schritt A und arbeite strikt entlang des Pflichtablaufs.

