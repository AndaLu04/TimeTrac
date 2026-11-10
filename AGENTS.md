# AGENTS.md — Projektanweisung TimeTrac

Vor jeder Aufgabe lesen. Bei Widerspruch zum Code: Nutzer fragen.

## Projekt
- Arbeitszeiterfassung für Kirchen-Angestellte, **Einzelnutzer**, Desktop, UI/Doku Deutsch.
- Stack: Python ≥ 3.10, Kivy ≥ 2.2, lokale Datenhaltung (SQLite/JSON), pytest.
- Keine Cloud, keine Netzwerkdienste, keine neuen Abhängigkeiten ohne Not.

## Architektur
- Strikte Trennung: `worktime/` (reine Logik, **keine Kivy-Imports**) ← `ui/` → `storage/`/`models/`.
- Layouts in .kv-Dateien; keine globalen Zustände.

## Domäne
- Arbeitszeitmodelle: Festzeit, Gleitzeit, Teilzeit, Dienstplan, AZV — konfigurierbar.
- Soll/Ist pro Tag/Woche/Monat, Überstunden mit Obergrenzen, Pausen (ArbZG), Urlaub/Krankheit/Fortbildung.
- Feiertage: kirchlich + regional (Bundesland wählbar), halbe Tage konfigurierbar.
- Fachliche Unsicherheiten (z. B. AVR): Nutzer fragen, nicht still entscheiden.

## Datenhaltung
- Schema-Änderungen immer mit Migration (keine Cloud-Kopie!); JSON/CSV-Export/Import obligatorisch.

## Konventionen & Tests
- Code Englisch, Kommentare/UI/Doku Deutsch; `black`, `isort`, `flake8` ohne Fehler; Typ-Hinweise.
- Jede Änderung an `worktime/`/`storage/` braucht Tests (ohne Kivy-Fenster), inkl. Grenzfälle: Monatswechsel, Sommerzeit, Mitternacht, halbe Feiertage.

## Git
- Commits: eine sinnvolle Änderung pro Commit, imperative Form.
- Branches: `feature/<kurz>`, `fix/<kurz>`; kein direkter Commit auf `master`.
- Vor jedem Commit: Tests + Linter laufen lassen.
