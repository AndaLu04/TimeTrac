# AGENTS.md — Projektanweisung für TimeTrac

Diese Datei ist die verbindliche Arbeitsanweisung für alle KI-gestützten und manuellen
Änderungen an diesem Repository. Sie ist vor jeder Aufgabe vollständig zu lesen.

## 1. Projektüberblick

**TimeTrac** ist eine Arbeitszeiterfassung für Angestellte in Kirchen (Pfarrämter,
Kirchengemeinden, Diakonie etc.).

- **Zielgruppe:** Ein einzelner Nutzer (kein Mehrbenutzerbetrieb, keine Rollen,
  keine Authentifizierung außer ggf. lokalem Schutz).
- **Zweck:** Erfassung, Verwaltung und Auswertung der persönlichen Arbeitszeit
  unter Berücksichtigung kirchenspezifischer Arbeitszeitmodelle.
- **Plattform:** Desktop (Windows/Linux/macOS); mobil optional, aber nicht
  primäres Ziel.
- **Sprache der UI und Dokumentation:** Deutsch.

## 2. Technologie-Stack

| Bereich | Technologie |
|---|---|
| Programmiersprache | Python (>= 3.10) |
| UI-Framework | Kivy (>= 2.2) |
| Datenhaltung | Lokal, dateibasiert (SQLite oder JSON — siehe Abschnitt 4) |
| Packaging (später) | PyInstaller o. Ä. für eine ausführbare Datei |
| Tests | pytest (Unit-Tests für Logik-Schichten, keine UI-Tests nötig) |

Keine neuen Abhängigkeiten ohne echte Notwendigkeit. Web-Frameworks,
Datenbankserver oder Cloud-Dienste sind explizit **nicht** Teil des Projekts.

## 3. Architektur und Code-Struktur

Strikte Trennung von Logik und UI — Kivy-Widgets enthalten **keine**
Geschäftslogik:

```
timetrac/
  __init__.py
  main.py            # Einstiegspunkt, baut die App auf
  models/            # Datenklassen: Arbeitstag, Zeitbuchung, Arbeitszeitmodell
  storage/           # Persistenz (Lesen/Schreiben, Migrationen)
  worktime/          # Kernlogik: Summen, Überstunden, Gleitzeit, Feiertage
  ui/                # Kivy-Screens, Widgets, .kv-Layouts
  resources/         # Icons, Fonts, Beispiel-Daten
tests/                # pytest-Tests (Logik wird ohne Kivy getestet)
docs/                # Nutzer- und Entwicklerdokumentation
```

Regeln:

- **worktime/** muss ohne Kivy-Importe funktionieren (reine Logik, gut testbar).
- **ui/** ruft worktime/storage auf, niemals umgekehrt.
- .kv-Dateien für Layouts bevorzugen; Python-Widgets nur für dynamische Teile.
- Keine globalen Zustände; Abhängigkeiten werden explizig übergeben.

## 4. Datenhaltung

- Einzelnutzer, lokal: SQLite (`timetrac.db`) als Standard, Alternative JSON-Export.
- **Schema-Änderungen** brauchen immer eine Migrationslogik (nie bestehende
  Daten zerstören) — der Nutzer hat keine Cloud-Kopie!
- Export/Import als JSON/CSV für Datensicherung ist Pflichtfeature.
- Keine personenbezogenen Daten an Dritte oder Netzwerkdienste senden.

## 5. Fachliche Domäne (kirchliche Arbeitszeitmodelle)

Unterstützte Modelle (konfigurierbar, individuell pro Nutzer):

1. **Feste Arbeitszeit** — feste Tages-/Wochenstunden.
2. **Gleitzeit** — Kernzeit, Gleitspanne, Überstundenkonto.
3. **Teilzeit** — reduzierte Soll-Stunden, ggf. ungleich verteilt.
4. **Dienstpläne / Schichten** — wechselnde Soll-Zeiten pro Tag.
5. **AZV / Arbeitszeitverkürzung** — z. B. freie Tage pro Monat statt Gehalt.

Fachliche Anforderungen:

- Soll-/Ist-Stunden pro Tag, Woche, Monat, Jahr.
- Über-/Minderstunden mit konfigurierbaren Obergrenzen (z. B. Überstundenabbau).
- Pausenregelungen (Mindestpausen nach Arbeitszeitgesetz beachten).
- Feiertagslogik: kirchliche + regionale Feiertage (Bundesland wählbar),
  Heiligabend/Silvester oft halbe Tage — konfigurierbar.
- Urlaub, Krankheit, Fortbildung als eigene Buchungstypen.
- Monatsabschluss mit Korrekturhistorie.

Fachliche Unsicherheiten (z. B. AVR-Regelungen) sind als **Fragen an den Nutzer**
zu klären, nicht stillschweigend zu entscheiden.

## 6. Konventionen

- Sprache: Code-Identifikatoren auf Englisch, Kommentare/UI/Dokumentation auf Deutsch.
- Formatierung: `black` (Zeilenlänge 88), Import-Sortierung `isort`.
- Linting: `flake8` oder `ruff` — darf vor jedem Commit keine Fehler zeigen.
- Typ-Hinweise für alle neuen Funktionen (mypy-freundlich).
- Namen: aussagekräftig, keine Abkürzungen außer etablierten
  Fachbegriffen (AZV, AVR, Gleitzeit).
- Keine toten Codepfade, kein auskommentierter Altcode — Git ist die Historie.

## 7. Testing

- Jede Änderung an `worktime/` oder `storage/` braucht Tests (`tests/`).
- Reine Logik wird **ohne** Kivy-Ausführung getestet (kein Fenster nötig).
- Kivy-Abhängigkeiten in Tests nur mocken, nicht starten.
- Mindestens Grenzfälle abdecken: Monatswechsel, Sommerzeit, Mitternacht,
  halbe Feiertage, 0-Stunden-Tage.

## 8. Git- und PR-Workflow

- Commits: kurze, prägnante Messages, Deutsch oder Englisch konsistent,
  imperative Form (z. B. „Add gleitzeit overtime cap").
- Ein Commit = eine in sich sinnvolle Änderung.
- Feature-Branches: `feature/<kurz>`, Fixes: `fix/<kurz>`.
- Keine Commits direkt auf `master` ohne Absprache.
- Vor jedem Commit: Tests und Linter laufen lassen.

## 9. Umgang mit diesem Dokument

- Bei fachlichen oder technischen Änderungen, die diese Anweisung betreffen,
  ist AGENTS.md mit zu aktualisieren.
- Bei Widerspruch zwischen AGENTS.md und aktuellem Code: Nutzer fragen,
  welche Seite gilt, dann AGENTS.md anpassen.

## 10. Schnellstart (für neue Entwickler/KI-Agenten)

```bash
python -m venv .venv && source .venv/bin/activate
pip install kivy pytest
python -m timetrac.main
pytest
```

*(Pfade/Abhängigkeiten anpassen, sobald setup.py/pyproject.toml existiert.)*
