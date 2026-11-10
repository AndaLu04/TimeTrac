# AGENTS.md — Projektanweisung TimeTrac

Vor jeder Aufgabe lesen. Bei Widerspruch zum Code: Nutzer fragen.

## Projekt
- Arbeitszeiterfassung für Kirchen-Angestellte, **Einzelnutzer**, Mobile first, Desktop second, UI/Doku Deutsch.
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

## Token-Sparen (gilt für jede Anfrage)
- Erst `grep`/gezieltes Lesen, dann erst ganze Dateien lesen; nur die Dateien öffnen, die die Aufgabe wirklich betrifft.
- Antworten knapp: keine Zusammenfassung des Codes, keine Wiederholung der Anweisung, keine Füller; Ergebnisse als Bullets.
- Kleinste korrekte Änderung; keine Refactors nebenbei, keine auskommentierten Altversionen.
- Nur den engsten nötigen Test laufen lassen (z. B. `pytest tests/test_worktime_x.py`), nicht immer die Suite.
- Dateien nicht vollständig neu schreiben, wenn ein kleiner Edit genügt.

## Git
- Commits: eine sinnvolle Änderung pro Commit, imperative Form.
- Branches: `feature/<kurz>`, `fix/<kurz>`; kein direkter Commit auf `master`.
- Vor jedem Commit: Tests + Linter laufen lassen.
