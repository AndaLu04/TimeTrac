# TimeTrac

Plattformunabhängige Zeiterfassungssoftware für (Frei-)Kirchen-Mitarbeitende.
Python + Kivy.

## Status

Projekt in der Designphase. Die Architektur, das Datenmodell, die
Arbeitszeitmodelle und die Klassenstruktur sind in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) beschrieben.

## Geplante Features

- Einstempeln & Ausstempeln (Anpassung der Anfangs- und Endzeit)
- Einträge erstellen, bearbeiten & löschen
- Bearbeitbares Dashboard mit statusbasierter Live-Berechnung
- Verlaufs-/Analyseansichten: Woche, Monat, Jahr, Insgesamt
- CSV-Export
- Mehrere Projekte/Arbeitgeber
- Arbeitszeitmodelle: Wochenstunden gleichverteilt, Tagespezifisch,
  Wochenstunden pauschal, Monatsstunden
- Zeit-Typen gemäß deutschem Arbeitsrecht (Arbeit, Urlaub, Krankheit, …)
- Geräte-Sync (WebDAV, Google Drive, Dateiablage – später)
