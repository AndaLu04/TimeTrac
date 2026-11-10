# TimeTrac – Architektur-Design

Plattformunabhängige Zeiterfassungssoftware für (Frei-)Kirchen-Mitarbeitende.
Python + Kivy, layerbasiert, statusbasiert (kein Live-Timer).

Dieses Dokument ist die verbindliche Design-Grundlage für die Implementierung.
Es baut auf dem bereits vorhandenen Data-Layer des Branches `kivy_ui` auf
(Priorisierung: bestehender Data-Layer vor neuem Konzept) und entwirft den
Logic-Layer neu. Der UI-Prototyp gilt als verwerfbar; das tragfähige Konzept
(Tab-Navigation, ScreenManager-Struktur) bleibt erhalten.

---

## 1. Ziele und Grundsätze

1. **Plattformunabhängig**: Android, iOS, Windows, macOS, Linux (Kivy).
2. **Statusbasiert**: Kein laufender Timer. Ein aktiver Zeitraum ist ein
   Eintrag mit `is_active = 1`. Die Dauer wird in der UI kontinuierlich aus
   `begin_at` und der aktuellen Uhrzeit berechnet, ohne erneute DB-Zugriffe.
3. **Absturzsicherheit**: Alles Persistierte liegt in der Datenbank; die App
   kann ihren Zustand nach einem Absturz vollständig wiederherstellen.
4. **Layer-Trennung**: `data` → `logic` → `ui`. Kein Layer greift nach oben.
5. **PEP 8**, sprechende Namen, deutsche Fachbegriffe dort, wo sie die
   Domäne vorgibt (`EntryType`, `HourType` – wie im bestehenden Code).

### Nicht-Ziele (v1)

- Kein Mehrbenutzer-Serverbetrieb; Sync erfolgt später über ein
  `SyncBackend`-Interface (v1: Stub).
- Keine Gehaltsabrechnung. Die App liefert Ist/Soll/Überstunden als
  Datenbasis.

---

## 2. Bestandsaufnahme: was aus `kivy_ui` übernommen wird

### 2.1 Data-Layer (übernehmen, Priorität 1)

Der bestehende Data-Layer ist ausgereift und wird **als Baseline** übernommen:

| Baustein                        | Bewertung / Entscheidung                        |
|---------------------------------|--------------------------------------------------|
| `Database` mit generischem `set`/`get`/`insert_new_row` | behalten |
| SQLite-Adapter/Converter für `date`, `datetime`, `EntryType`, `HourType` | behalten – saubere Typisierung direkt aus der DB |
| `Entry` als Active Record mit Lazy Loading + Auto-Persistenz | behalten – Statuskonzept passt exakt dazu (`is_active`) |
| `Project` als Active Record     | behalten                                          |
| Tabellen `projects` / `entries` mit AUTOINCREMENT-IDs | behalten (siehe 3.4 zur Sync-Vorbereitung) |
| `ALLOWED_COLUMNS`-Whitelist     | behalten – Schutz vor SQL-Injection über Spaltennamen |

**Kleine Nachbesserungen am bestehenden Code** (kein Konzeptbruch, nur
Robustheit):

- `database.get_entry_ids_from_project_id` nutzt String-Interpolation statt
  Parameterbindung → auf `?`-Platzhalter umstellen.
- `Database.__init__` führt `PRAGMA foreign_keys = ON` ein (FKs werden sonst
  von SQLite ignoriert).
- Das auskommentierte Unique-Index auf `is_active = 1` aktivieren – es erzwingt
  die Invariante „**genau ein aktiver Eintrag global**" (Entscheidung) auf
  DB-Ebene. Ein Wechsel zu „ein aktiver Eintrag je Projekt" wäre später nur
  eine Index-Änderung auf `(project_id) WHERE is_active = 1` plus Anpassung
  im `TrackingService` – das Schema selbst bleibt davon unberührt.
- `Project.entry_list` lädt beim Konstruieren **alle** Entries eager → auf
  eine explizite Methode `load_entries()` bzw. Lazy-Property umstellen
  (Performance bei großen Historien).

### 2.2 Logic-Layer (neu entwerfen, Priorität gleichwertig)

`src/logic/` existiert als Paket noch ohne Inhalt. Entwurf in Abschnitt 5.

### 2.3 UI-Layer (Prototyp, verwerfbar)

`src/ui/app.py` ist leer. Nur die Grundentscheidung bleibt: **Kivy
App + ScreenManager**. Screens werden neu gebaut (Abschnitt 6), orientiert am
Feature-Set der Anforderungen.

---

## 3. Datenmodell (auf bestehendem Schema aufbauend)

**Grundsatz: In der Datenbank liegt nur, was der Nutzer eingibt oder was ein
Status ist. Alles Abgeleitete (Dauern, Soll-, Ist-, Überstunden) wird zur
Laufzeit berechnet.**

### 3.1 Tabelle `projects` (bestehend, erweitert)

Bestehende Spalten: `id`, `name`, `target_hours`, `hour_type`, `is_default`.

**Erweiterungen (additive Migration):**

| Spalte     | Typ    | Default      | Zweck                                              |
|------------|--------|--------------|----------------------------------------------------|
| `workdays` | TEXT   | `"[0,1,2,3,4]"` | JSON-Liste der Arbeitstage (ISO: Mo=0 … So=6) – **konfigurierbar** für Wochenendarbeit |
| `daily_hours_override` | TEXT | NULL | JSON `{weekday: hours}` – überschreibt `target_hours` einzelner Wochentage; nur für `hour_type = DAILY` relevant. NULL = gleichmäßige Verteilung |
| `is_active` | INTEGER | `1`        | Archivierung ohne Löschen                         |
| `notes`    | TEXT   | NULL         | optionale Notiz                                    |

**Zur Frage „reicht ein Feld für Sollstunden?": Ja.** Es bleibt bei
`target_hours` als einzigem Stundenfeld; die Semantik ergibt sich aus
`hour_type` (siehe 5.1). Die ursprünglich vorgeschlagenen Felder
`weekly_hours`/`daily_hours`/`monthly_hours` entfallen. Das Muster
„8 h Di + 8 h Mi" wird über `hour_type = DAILY` mit `target_hours = 8` und
`workdays = [1, 2]` abgebildet.

**Ungleiche Tagesstunden** (z. B. 6 h Di + 8 h Mi) werden über das optionale
JSON-Feld `daily_hours_override` abgebildet (ab v1, Entscheidung):

### 3.2 Tabelle `entries` (bestehend, erweitert)

Bestehende Spalten: `id`, `project_id`, `entry_type`, `is_active`,
`created_at`, `edited_at`, `entry_date`, `begin_at`, `end_at`, `notes`.

**Erweiterungen (additive Migration):**

| Spalte           | Typ    | Default | Zweck                                          |
|------------------|--------|---------|------------------------------------------------|
| `break_minutes`  | INTEGER | `0`     | Pause (dt. Arbeitsrecht: ab 6 h ≥ 30 min)      |
| `project_label`  | TEXT   | NULL    | freies Tätigkeitsfeld („Jugendgruppe") – nicht zu verwechseln mit `project_id` |
| `counts_as_work` | INTEGER | NULL    | **pro Eintrag wählbar** (Entscheidung): zählt dieser Eintrag als Arbeitszeit? NULL = Default je `entry_type` (Tabelle 3.3); gesetzt nur sinnvoll bei `SONSTIGES`/`PLATZHALTER` |
| `deleted_at`     | TEXT   | NULL    | Soft Delete: Einträge in Überstundenberechnungen verschwinden nicht spurlos; Basis für spätere Sync-Konfliktauflösung |

`entry_date` bleibt das fachliche Zuordnungsdatum (für Woche/Monat/Jahr),
`begin_at`/`end_at` die Stempelzeiten – wie im bestehenden Schema.

### 3.3 `EntryType` (bestehend, ergänzt)

Bestehend: `ARBEIT`, `KRANKHEIT`, `URLAUB`, `FEIERTAG`, `PLATZHALTER`.
Ergänzt werden die für das deutsche Arbeitsrecht fehlenden:

```python
class EntryType(StrEnum):
    ARBEIT = "Arbeit"
    KRANKHEIT = "Krankheit"
    URLAUB = "Urlaub"
    FEIERTAG = "Feiertag"
    ELTERNZEIT = "Elternzeit"
    UEBERSTUNDENAUSGLEICH = "Überstundenausgleich"
    SONSTIGES = "Sonstiges"
    PLATZHALTER = "Platzhalter"
```

Soll-Behandlung (zentrale Konstante im `OvertimeService`, Abschnitt 5.3):

| Typ                    | Ist-Stunden      | Soll-Stunden                        |
|------------------------|------------------|-------------------------------------|
| Arbeit                 | zählt (netto von Pausen) | –                            |
| Einträge mit `counts_as_work = 1` | zählt | –                              |
| Urlaub                 | –                | gilt als erfüllt (Entgeltfortzahlung) |
| Krankheit              | –                | gilt als erfüllt (Entgeltfortzahlung) |
| Feiertag               | –                | gilt als erfüllt (gesetzl./tariflich) |
| **Elternzeit**         | –                | **scheidet aus** – rein informativer Eintrag, keine Gutschrift, keine Reduktion |
| Überstundenausgleich   | –                | reduziert den Überstundenstand im Zeitraum |
| Sonstiges              | default: nein; **pro Eintrag** über `counts_as_work` wählbar (Entscheidung) | – |
| Platzhalter            | –                | –                                   |

### 3.4 Sync-Vorbereitung (ohne Sync in v1)

AUTOINCREMENT-IDs bleiben. Für den späteren Sync wird **additiv** eine
`uuid`-Spalte (UUID4 als TEXT, bei Insert befüllt) ergänzt, sobald der erste
`SyncBackend` implementiert wird – offline erzeugte Einträge kollidieren dann
nicht. Konfliktstrategie: Last-Writer-Wins je Eintrag anhand `edited_at`;
Soft-Deletes (Tombstones) gewinnen gegen Updates. `SyncBackend`-Interface
(`push`/`pull`) als Stub in `data/sync/`, damit Logic und UI später nicht
angefasst werden müssen.

### 3.5 Einstellungen (neue Tabelle `settings`)

Key-Value je Gerät (bewusst **nicht** synchronisiert):

| key                    | Wert (Beispiel)                                  |
|------------------------|--------------------------------------------------|
| language               | `de` / `en`                                      |
| active_project_id      | int (Vorauswahl beim Einstempeln)                |
| default_break_minutes  | `0`                                              |
| csv_delimiter          | `,` (frei eintragbar, Textfeld)                   |
| sync_backend           | `none` (v1), später `webdav`, `gdrive`, `file`   |
| sync_config            | JSON                                              |
| last_backup_at         | ISO-Datum                                         |
| dashboard_layout      | JSON (sichtbare/reihenfolgte Kacheln)            |

### 3.6 Statuskonzept im Detail

```
Einstempeln:  [kein aktiver Eintrag] → Entry(is_active=1, begin_at=now)
Ausstempeln:  Entry(is_active=1)    → Entry(is_active=0, end_at=now)
Anpassen:     begin_at/end_at/entry_date editierbar (end > begin, VALIDIERUNG im TrackingService)
Löschen:      Entry → deleted_at = now (Soft Delete)
```

**Invarianten (im `TrackingService` erzwungen, zusätzlich durch den
Unique-Index abgesichert):**

- **Genau ein** `is_active = 1`-Eintrag **global** über alle Projekte
  (Entscheidung) – vor jedem `clock_in` prüfen.
- `end_at > begin_at` (falls gesetzt); `is_active = 0` ⟹ `end_at` gesetzt.

Die Live-Uhr im Dashboard: `LiveDurationLabel` holt **einmal** den aktiven
Eintrag und aktualisiert danach nur die Anzeige per `Clock.schedule_interval`
gegen die Wanduhr – keine DB-Lesezugriffe pro Tick. Nach einem App-Neustart
ergibt sich derselbe Stand aus `begin_at` → Status statt Timer, wie gefordert.

---

## 4. Paketstruktur

```
src/
├── constants.py               # EntryType, HourType, Tables (bestehend, ergänzt)
├── data/                      # bestehend, erweitert
│   ├── database.py            # Database (bestehend)
│   ├── entry.py               # Entry (bestehend)
│   ├── project.py             # Project (bestehend)
│   ├── settings.py            # neu: SettingsRepository (Key-Value)
│   └── sync/
│       └── sync_backend.py    # neu: abstrakte Basisklasse (Stub v1)
├── logic/                     # neu
│   ├── tracking_service.py    # Ein-/Ausstempeln, Validierung, CRUD-Orchestrierung
│   ├── working_time_model.py  # Sollstunden-Strategien je HourType
│   ├── overtime_service.py    # Ist/Soll/Überstunden je Zeitraum
│   ├── analysis_service.py    # Verlaufsansichten (DTOs für die UI)
│   ├── export_service.py      # CSV-Export (Trennzeichen konfigurierbar)
│   ├── settings_service.py
│   └── backup_service.py      # manualer DB-Export/-Import
├── ui/
│   ├── app.py                 # Kivy-App, ScreenManager
│   ├── screens/
│   │   ├── dashboard_screen.py
│   │   ├── history_screen.py
│   │   ├── entries_screen.py
│   │   ├── entry_edit_screen.py
│   │   ├── project_screen.py
│   │   └── settings_screen.py
│   ├── widgets/
│   │   └── live_duration_label.py
│   └── view_models/
└── resources/
    └── i18n/                  # gettext: de, en
```

**Regeln:**

- `logic` importiert niemals `kivy`.
- `ui` importiert niemals `data` direkt, sondern nur `logic`-Services.
- `data` enthält keine Fachlogik (keine Überstundenberechnung im DataLayer).
- Live-Updates der UI über einen einfachen `EventBus` in `core/events.py`
  (Screens registrieren sich für DB-Änderungsereignisse).

---

## 5. Logic-Layer (Entwurf)

### 5.1 Arbeitszeitmodelle (Strategy-Pattern auf `HourType`)

Der bestehende `HourType` (`ALLTIME`, `MONTHLY`, `WEEKLY`, `DAILY`) wird
umgesetzt als Strategien mit **einem** Stundenanker `target_hours`:

```python
class AbstractWorkingTimeModel(ABC):
    @abstractmethod
    def target_hours_for_day(self, day: date) -> float: ...
    @abstractmethod
    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float: ...
    @abstractmethod
    def target_hours_for_month(self, year: int, month: int) -> float: ...
    @abstractmethod
    def target_hours_total(self, since: date | None = None) -> float: ...
```

| HourType    | `target_hours` bedeutet | Tagesformel                                  | Beispiele                       |
|-------------|-------------------------|----------------------------------------------|---------------------------------|
| `WEEKLY`    | Stunden pro Woche       | gleichverteilt auf `workdays`               | 40 h Pastor (Mo–Fr → 8 h/Tag)   |
| `DAILY`     | Stunden pro Arbeitstag | `target_hours` an jedem Tag in `workdays`; `daily_hours_override` überschreibt einzelne Tage | Teilzeit 8 h Di + 8 h Mi; 6 h Di + 8 h Mi via Override |
| `MONTHLY`   | Stunden pro Monat      | **pauschal**: Monat = `target_hours`; Teilzeiträume werden anteilig nach Arbeitstagen hochgerechnet | 20 h Werkstudent                |
| `ALLTIME`   | Gesamtvolumen (Stunden)| Zeitraumanteil nach Arbeitstagen            | Projektauftrag „300 h gesamt"  |

**ALLTIME in v1 deaktiviert** (Entscheidung): Das Interface und die Strategie
bleiben implementiert (kein toter Code-Entwurf), aber die Projektauswahl-UI
bietet den Typ in v1 **nicht an**. Er wird erst aktiviert, wenn ein konkreter
Bedarf besteht – Logik und UI sind dann bereits vorbereitet.

`MONTHLY` ist bewusst **pauschal** (Entscheidung): Die Woche erhält
`target_hours × (Arbeitstage der Woche / Arbeitstage des Monats)`, der Monat
exakt `target_hours`. Keine kalendergenaue Tagesverteilung.

`workdays` (projektspezifisch, default Mo–Fr) macht Wochenendarbeit
abbildbar: ein Di–Sa-Pastor mit `WEEKLY/40` verteilt auf `[1,2,3,4,5]`
(Tue–Sat) → 8 h je Tag inkl. Samstag.

### 5.2 TrackingService

```python
class TrackingService:
    def clock_in(self, project: Project, entry_type: EntryType = EntryType.ARBEIT) -> Entry: ...
    def clock_out(self, entry: Entry) -> Entry: ...
    def update_times(self, entry: Entry, begin_at: datetime, end_at: datetime | None) -> Entry: ...
    def delete_entry(self, entry: Entry) -> None:      # Soft Delete
    def get_active_entry(self) -> Entry | None: ...
```

Der Service ist die einzige Stelle, die die Invarianten aus 3.6 prüft und
`edited_at` setzt. Die Active-Record-Persistenz des bestehenden Data-Layers
bleibt dabei unangetastet – der Service orchestriert nur.

### 5.3 OvertimeService

```
ist_hours   = Σ duration(ARBEIT-Entries, netto von break_minutes)
              + Gutschrift-Logik je EntryType (Tabelle in 3.3);
              `counts_as_work = 1` zählt stets als Ist-Stunden
soll_hours  = Σ target_hours je Zeitraum (nur Tage in workdays;
              Feiertags-Entries gelten als erfülltes Soll)
overtime    = ist_hours − soll_hours
```

- **ÜberstundenWoche**: laufende ISO-Kalenderwoche.
- **ÜberstundenMonat**: laufender Kalendermonat.
- **ÜberstundenInsgesamt**: kumulierte Differenz seit dem frühesten Eintrag
  – **ohne Verfall** (Entscheidung). `UEBERSTUNDENAUSGLEICH`-Einträge
  reduzieren den Bestand im Zeitraum, in dem sie liegen.
- **Keine Gleitzeitbandbreite** (Entscheidung): jede Minute über Soll zählt.
- Alle Werte sind reine Funktionen der DB-Inhalte → reproduzierbar, keine
  Zwischenspeicher.

### 5.4 AnalysisService (DTOs für die UI)

```python
@dataclass(frozen=True)
class PeriodSummary:
    period_type: Literal["week", "month", "year", "total"]
    start: date
    end: date
    target_hours: float
    actual_hours: float
    overtime_hours: float
    entries: list[Entry]
```

Verlaufsansichten Woche/Monat/Jahr/Insgesamt liefern genau diese DTOs.

### 5.5 ExportService / BackupService

- **CSV**: UTF-8, Spalten je Eintrag (Datum, Beginn, Ende, Pause, Typ,
  Projekt, Notiz, Dauer); **Trennzeichen frei eintragbar** (Textfeld,
  Default `,`); Dezimaltrennzeichen folgt der Sprache.
- **Backup**: manueller DB-Export – die SQLite-Datei wird über den nativen
  Datei-Dialog an einen vom Nutzer gewählten Ort kopiert (und von dort
  importierbar). Kein automatischer Cloud-Backup in v1.

### 5.6 Feiertage

Manuelle Eintragung als `FEIERTAG`-Entry (Entscheidung). Optionaler,
späterer **Kalender-Import** (ICS-Datei über den Datei-Dialog) erzeugt
automatisch Feiertags-Entries für ein Jahr/Bundesland – als eigener Service
`logic/holiday_import_service.py`, da die manuelle Eintragung vollständig
unabhängig davon funktioniert.

---

## 6. UI-Konzept (Kivy)

- `ScreenManager` mit Screens: Dashboard, Verlauf, Einträge, Eintrag-Editor,
  Projekte, Einstellungen.
- **Dashboard**: Live-Dauer-Label (statusbasiert, s. 3.6), WochenSoll,
  WochenIst, ÜberstundenWoche, ÜberstundenMonat, ÜberstundenInsgesamt;
  Kacheln ein-/ausblendbar und umsortierbar (`RecycleGridLayout`), Layout
  als JSON in `settings`.
- **Verlauf**: Filter Woche · Monat · Jahr · Insgesamt mit
  `PeriodSummary`-Inhalten.
- **Einträge**: `RecycleView`-Liste, sortiert nach `begin_at` (neu → alt),
  Tap öffnet Editor.
- **Einstellungen**: Sprache, Projekte + Arbeitszeitmodelle + Arbeitstage,
  Pausen-Default, CSV-Trennzeichen, Backup-Export/-Import, Sync (v1 „kein").
- **i18n**: gettext, `_()` in allen Screens; Sprachwechsel ohne Neustart
  (Neuaufbau der Screens). Enum-Werte in der DB bleiben deutsch (bestehender
  Data-Layer), Anzeige übersetzt über Mapping.

---

## 7. Getroffene Entscheidungen (aus Review)

| Frage                      | Entscheidung                                        |
|----------------------------|----------------------------------------------------|
| Elternzeit                 | scheidet aus – rein informativ, keine Sollgutschrift |
| Überstundenverfall         | kein Verfall – kumuliert seit erstem Eintrag        |
| Arbeitstage                | pro Projekt konfigurierbar (`workdays`), Wochenendarbeit möglich |
| Gleitzeit/Puffer           | keine Bandbreite – jede Minute zählt               |
| Feiertage                  | manuell, optionaler ICS-Kalender-Import später      |
| Monatsmodell               | pauschal (Monat = `target_hours`, Woche anteilig)   |
| CSV-Format                 | Trennzeichen frei eintragbar, Default `,`          |
| Backup                     | manueller DB-Export (Datei-Dialog)                 |
| Sollstunden-Felder         | **ein** Feld `target_hours`, Semantik via `hour_type` (wie im bestehenden Schema) |
| Ungleiche Tagesstunden     | `daily_hours_override` (JSON) **ab v1**, optional ausfüllbar |
| Aktive Einträge            | **genau einer global** (Unique-Index wie im Code vorbereitet) |
| Sonstiges                  | **pro Eintrag** wählbar (`counts_as_work`), Default: zählt nicht |
| ALLTIME-Modell             | Interface + Strategie implementiert, **UI-Auswahl in v1 deaktiviert** |

## 8. Verbleibende offene Fragen

Keine – alle Design-Entscheidungen sind getroffen. Die Implementierung kann
gemäß Abschnitt 9 beginnen. Neue Fragen (z. B. Details des ICS-Imports oder
der WebDAV-Authentifizierung) werden bei Erreichen des jeweiligen Schritts
als Erweiterung dieses Dokuments geklärt.

## 9. Umsetzungsreihenfolge (Vorschlag)

1. Data-Layer-Nachbesserungen (2.1) + additive Migrationen (3.1, 3.2, 3.5) + Tests
2. `logic`: WorkingTimeModel-Strategien + OvertimeService + Tests
3. `logic`: TrackingService + Tests
4. `ui`: Dashboard + Ein-/Ausstempeln
5. Einträge-Liste + Editor
6. Verlauf + CSV-Export + Backup
7. Einstellungen + i18n
8. Sync-Backends (WebDAV zuerst), optionaler ICS-Feiertagsimport
