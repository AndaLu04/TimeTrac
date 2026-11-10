# TimeTrac – Architektur-Design

Plattformunabhängige Zeiterfassungssoftware für (Frei-)Kirchen-Mitarbeitende.
Python + Kivy, layerbasiert, statusbasiert (kein Live-Timer).

Dieses Dokument ist die verbindliche Design-Grundlage für die Implementierung.
Es beantwortet die offenen Fragen zu Datenstruktur, Klassenstruktur und listet
die noch zu klärenden Entscheidungen am Ende auf.

---

## 1. Ziele und Grundsätze

1. **Plattformunabhängig**: Android, iOS, Windows, macOS, Linux (Kivy).
2. **Statusbasiert**: Es existiert kein laufender Timer. Ein aktiver Zeitraum
   ist ein Datenbankeintrag mit Status `ACTIVE`. Die Dauer wird in der UI aus
   `start_time` und der aktuellen Uhrzeit **kontinuierlich berechnet**, ohne
   erneut auf die Datenbank zuzugreifen.
3. **Absturzsicherheit**: Da alles Persistierte in der Datenbank liegt, kann
   die App nach einem Absturz ihren vollständigen Zustand wiederherstellen
   (Stichwort: „State Restoration").
4. **Layer-Trennung**: `data` → `logic` → `ui`. Kein Layer greift nach oben.
5. **PEP 8**, sprechende Namen, keine Abkürzungen außer etablierten
   Fachbegriffen (z. B. `csv`).

### Nicht-Ziele (v1)

- Kein echter Mehrbenutzer-Betrieb im Sinne einer Server-Anwendung; Sync
  erfolgt später über einen abstrahierenden `SyncBackend` (Stub in v1).
- Keine Lohn-/Gehaltsabrechnung. Die App liefert Ist/Soll/Überstunden als
  Datenbasis, ersetzt aber keine Payroll-Logik.

---

## 2. Architekturübersicht (Layer)

```
+-------------------------------------------------------------+
| ui/            Kivy-Widgets, Screens, ViewModel-Adapter     |
|                liest NUR aus logic-Services, nie aus data    |
+-------------------------------------------------------------+
| logic/         Services: TimeTrackingService,                |
|                WorkingTimeModel, OvertimeService,             |
|                ExportService, SettingsService, SyncService   |
|                (pure Python, ohne Kivy-Import!)              |
+-------------------------------------------------------------+
| data/          Repositories (CRUD), SQLite-Schema,          |
|                Migrationen, DTOs/Entitäten                   |
+-------------------------------------------------------------+
```

**Regeln:**

- `logic` importiert niemals `kivy`.
- `ui` importiert niemals `sqlite3` oder Repositories direkt.
- `data` kennt keine Fachlogik (keine Überstundenberechnung im DataLayer).
- Kommunikation UI ↔ Logic über Rückgabewerte und einen einfachen
  `EventBus` (Observer-Pattern, Beobachtung von DB-Änderungen für
  Live-Aktualisierung der Listen).

### Paketstruktur

```
timetrac/
├── __main__.py
├── app.py                     # Kivy-App-Einstieg, ScreenManager-Aufbau
├── core/                      # Querschnitt
│   ├── events.py              # EventBus
│   ├── localization.py       # i18n (gettext, .po/.mo)
│   └── errors.py              # fachliche Exceptions
├── data/
│   ├── entities.py            # dataclasses: Entry, Employer, Settings …
│   ├── database.py            # Verbindung, Schema, Migrationen
│   ├── repositories/
│   │   ├── entry_repository.py
│   │   ├── employer_repository.py
│   │   └── settings_repository.py
│   └── sync/                  # später: SyncBackend-Implementierungen
│       └── sync_backend.py    # abstrakte Basisklasse (Stub v1)
├── logic/
│   ├── tracking_service.py    # Einstempeln/Ausstempeln/CRUD-Orchestrierung
│   ├── working_time_model.py # Strategien für Sollstunden
│   ├── overtime_service.py   # Wochen/Monat/Gesamt-Aggregationen
│   ├── analysis_service.py   # Verlaufsansichten (Woche/Monat/Jahr/Total)
│   ├── export_service.py     # CSV-Export
│   └── settings_service.py
├── ui/
│   ├── screens/
│   │   ├── dashboard_screen.py
│   │   ├── history_screen.py
│   │   ├── entries_screen.py
│   │   ├── entry_edit_screen.py
│   │   └── settings_screen.py
│   ├── widgets/
│   │   ├── live_duration_label.py   # statusbasierte Live-Uhr (Clock-Auswertung)
│   │   └── …
│   └── view_models/                # UI-Zustand je Screen
└── resources/
    ├── i18n/de/LC_MESSAGES/…
    └── i18n/en/LC_MESSAGES/…
```

---

## 3. Datenmodell

**Grundsatz: In der Datenbank liegt nur, was der Nutzer eingibt oder was ein
Status ist. Alles Abgeleitete (Dauern, Soll-, Ist-, Überstunden) wird zur
Laufzeit berechnet.** Ausnahmen: `updated_at` (Technik) und der Sync-Status.

### 3.1 Entitäten (logisch)

#### Employer (Projekt/Arbeitgeber)

| Feld            | Typ      | DB | Beschreibung                            |
|-----------------|----------|----|-----------------------------------------|
| id              | UUID     | ✔  | Primärschlüssel                         |
| name            | TEXT     | ✔  | z. B. „Ev. Kirchengemeinde X"           |
| notes            | TEXT     | ✔  | optional                                |
| is_active       | BOOL     | ✔  | Archivierung ohne Löschen              |
| created_at      | DATETIME | ✔  |                                         |
| updated_at      | DATETIME | ✔  |                                         |

#### WorkingTimeModel (Sollstunden-Modell je Employer)

Das Modell gehört zum Arbeitgeber, damit ein Mitarbeiter mehrere Anstellungen
mit unterschiedlichen Modellen verwalten kann.

| Feld                    | Typ      | DB | Beschreibung                              |
|-------------------------|----------|----|-------------------------------------------|
| id                      | UUID     | ✔  |                                           |
| employer_id             | UUID     | ✔  | FK Employer                               |
| model_type              | ENUM     | ✔  | siehe 5.1                                 |
| weekly_hours            | REAL     | ✔  | „Stundenanker" für WeeklyEven / WeeklyFlat|
| daily_hours             | REAL     | ✔  | für DailySpecific (pro Wochentag)         |
| monthly_hours           | REAL     | ✔  | für Monthly                               |
| valid_from              | DATE     | ✔  | Modellwechsel ohne Historienverfälschung  |
| valid_to                | DATE     | ✔  | NULL = offen                              |

`daily_hours` wird als JSON-Spalte `{0: 8.0, 2: 8.0}` (Wochentag → Stunden,
ISO-Nummerierung Montag=0) gespeichert. Nur für `model_type = DAILY_SPECIFIC`
relevant.

#### Entry (Zeiteintrag)

| Feld            | Typ      | DB | Beschreibung                                     |
|-----------------|----------|----|--------------------------------------------------|
| id              | UUID     | ✔  |                                                   |
| employer_id     | UUID     | ✔  | FK Employer                                       |
| entry_type      | ENUM     | ✔  | WORK, VACATION, SICK_LEAVE, PARENTAL_LEAVE,       |
|                 |          |    | TIME_OFF_IN_LIEU, PUBLIC_HOLIDAY, OTHER            |
| status          | ENUM     | ✔  | ACTIVE, FINISHED, DRAFT                           |
| start_time      | DATETIME | ✔  | Einstempel-Zeitpunkt                             |
| end_time        | DATETIME | ✔  | NULL solange ACTIVE                              |
| break_minutes   | INT      | ✔  | bezahlte Pause abziehen, Default 0                |
| note            | TEXT     | ✔  | optional                                          |
| project         | TEXT     | ✔  | optional (z. B. „Jugendgruppe")                    |
| created_at      | DATETIME | ✔  |                                                   |
| updated_at      | DATETIME | ✔  |                                                   |
| deleted_at      | DATETIME | ✔  | Soft Delete (Wiederherstellung/History)          |

**Nicht in der DB** (Laufzeitberechnung): `duration`, alle Soll-/Ist-/
Überstundenwerte, Live-Dauer des aktiven Eintrags.

**Warum UUIDs statt Autoincrement?** Sie sind die Voraussetzung für spätere
Geräte-Synchronisation (offline erzeugte IDs kollidieren nicht).

**Warum Soft Delete?** Einträge, die in Überstundenberechnungen eingingen,
dürfen nicht spurbar verschwinden; außerdem Grundlage für Sync-Konfliktauflösung.

#### Settings (Key-Value je Gerät)

| key                    | Beispielwert                                       |
|------------------------|----------------------------------------------------|
| language               | `de` / `en`                                        |
| active_employer_id     | UUID (Vorauswahl beim Einstempeln)                |
| overtime_carryover     | bool – ob Überstunden monatlich verfallen sollen  |
| default_break_minutes  | 0                                                  |
| sync_backend           | `none` (v1), später `webdav`, `gdrive`, `file`     |
| sync_config            | JSON (Backend-spezifisch)                          |
| last_sync_at           | ISO-Datum                                          |

Gerätebezogene Einstellungen leben bewusst **nicht** in den zu synchronisierenden
Fachdaten.

### 3.2 SQLite-Schema (Auszug)

```sql
CREATE TABLE employer (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    notes       TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE working_time_model (
    id            TEXT PRIMARY KEY,
    employer_id   TEXT NOT NULL REFERENCES employer(id),
    model_type    TEXT NOT NULL CHECK (model_type IN
                  ('WEEKLY_EVEN','WEEKLY_FLAT','DAILY_SPECIFIC','MONTHLY')),
    weekly_hours  REAL,
    daily_hours   TEXT,   -- JSON {weekday: hours}
    monthly_hours REAL,
    valid_from    TEXT NOT NULL,
    valid_to      TEXT
);

CREATE TABLE entry (
    id             TEXT PRIMARY KEY,
    employer_id    TEXT NOT NULL REFERENCES employer(id),
    entry_type     TEXT NOT NULL CHECK (entry_type IN
                   ('WORK','VACATION','SICK_LEAVE','PARENTAL_LEAVE',
                    'TIME_OFF_IN_LIEU','PUBLIC_HOLIDAY','OTHER')),
    status         TEXT NOT NULL CHECK (status IN ('ACTIVE','FINISHED','DRAFT')),
    start_time     TEXT NOT NULL,
    end_time       TEXT,
    break_minutes  INTEGER NOT NULL DEFAULT 0,
    note           TEXT,
    project        TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    deleted_at     TEXT
);

CREATE INDEX idx_entry_start_time ON entry(start_time);
CREATE INDEX idx_entry_employer   ON entry(employer_id);
CREATE INDEX idx_entry_status     ON entry(status);

CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

Alle Datumsangaben als **ISO 8601 UTC** (`datetime.isoformat()`); die UI
konvertiert in lokale Zeit. Das verhindert Fehler bei Zeitumstellung und
ist Sync-freundlich.

### 3.3 Statuskonzept im Detail

```
Einstempeln:  [kein aktiver Eintrag] → Entry(status=ACTIVE, start_time=now)
Ausstempeln:  Entry(status=ACTIVE)  → Entry(status=FINISHED, end_time=now)
Anpassen:     start_time/end_time editierbar (VALIDIERUNG: end > start)
Löschen:      Entry → deleted_at = now (Soft Delete)
```

**Invarianten (in `tracking_service` erzwungen):**

- Pro Employer maximal **ein** `ACTIVE`-Eintrag gleichzeitig.
- `end_time > start_time` (falls gesetzt).
- `status = FINISHED` ⟹ `end_time IS NOT NULL`.

Die Live-Uhr im Dashboard: `LiveDurationLabel` holt sich **einmal** den aktiven
Eintrag beim Screen-Aufbau und aktualisiert danach nur noch die Anzeige mit
`Clock.schedule_interval` gegen die Wanduhr – **keine** DB-Lesezugriffe pro Tick.
Nach einem App-Neustart ergibt sich derselbe Stand aus `start_time` – damit ist
das „Status statt Timer"-Prinzip erfüllt.

---

## 4. Zeit-Typen (Deutsches Arbeitsrecht)

| Typ               | DB-Wert           | Zählt als Arbeitszeit | Anmerkung                          |
|-------------------|-------------------|:---------------------:|------------------------------------|
| Arbeit            | `WORK`            | ja                    | Normalfall                         |
| Urlaub            | `VACATION`        | ja (Soll)             | zählt als erfüllte Sollstunden     |
| Elternzeit        | `PARENTAL_LEAVE`  | je Konfiguration      | in v1: zählt als erfülltes Soll     |
| Krankheit          | `SICK_LEAVE`      | ja (Soll)             | Entgeltfortzahlung → Soll gilt     |
| Überstundenausgleich| `TIME_OFF_IN_LIEU`| negativ auf Überstunden | Freizeitausgleich für Überstunden |
| Feiertag           | `PUBLIC_HOLIDAY`  | ja (Soll)             |                                    |
| Sonstiges          | `OTHER`           | konfigurierbar       | z. B. Fortbildung, Dienstfahrt     |

Das Mapping Typ → Soll-Behandlung liegt als Konstante in
`logic/overtime_service.py` und ist bewusst zentral, weil sich hier
arbeitsrechtliche Semantik bündelt.

---

## 5. Arbeitszeitmodelle (Strategy-Pattern)

### 5.1 Modelltypen

```python
class WorkingTimeModelType(Enum):
    WEEKLY_EVEN     = "WEEKLY_EVEN"      # Wochenstunden gleichverteilt
    WEEKLY_FLAT     = "WEEKLY_FLAT"      # Wochenstunden pauschal (keine Tagesaufteilung)
    DAILY_SPECIFIC  = "DAILY_SPECIFIC"   # feste Stunden je Wochentag
    MONTHLY         = "MONTHLY"           # Monatsstunden
```

Jeder Typ implementiert das gemeinsame Interface:

```python
class AbstractWorkingTimeModel(ABC):
    @abstractmethod
    def target_hours_for_day(self, date: date) -> float: ...
    @abstractmethod
    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float: ...
    @abstractmethod
    def target_hours_for_month(self, year: int, month: int) -> float: ...
    @abstractmethod
    def target_hours_for_year(self, year: int) -> float: ...
    @abstractmethod
    def target_hours_total(self, since: date | None = None) -> float: ...
```

Die **Sollstunden-Variable** (`weekly_hours`, `daily_hours`, `monthly_hours`)
ist der „Ankerpunkt" der Formeln:

| Modell            | Tagesformel                                  | Beispiel                    |
|-------------------|----------------------------------------------|-----------------------------|
| `WEEKLY_EVEN`     | `weekly_hours / 5` (Mo–Fr)                   | 40 h → 8 h/Tag              |
| `WEEKLY_FLAT`     | Tagesformel undefiniert; nur Woche/Monat     | 20 h Werkstudent            |
| `DAILY_SPECIFIC`  | Lookup `daily_hours[weekday]`, sonst 0       | Teilzeit Di+Mi je 8 h       |
| `MONTHLY`         | `monthly_hours / Arbeitstage des Monats`     | Pastor: 40 h/Woche als Monatspauschale |

`MONTHLY` verteilt auf die werktäglichen Arbeitstage des konkreten Monats
(kalendergenau), damit Wochen-/Monatsansichten konsistent bleiben.

### 5.2 Überstundenberechnung

Aggregation je Zeitraum (Woche/Monat/Jahr/Gesamt):

```
ist_hours   = Σ duration(WORK-Entries, netto von Pausen)
              + Σ target_credit(VACATION, SICK_LEAVE, PUBLIC_HOLIDAY, …)
soll_hours  = Σ target_hours je Modell (nur WORK-Tage, Feiertage ausgenommen)
overtime    = ist_hours − soll_hours
```

- **ÜberstundenWoche / ÜberstundenMonat**: Überstunden der aktuellen
  Kalenderwoche / des aktuellen Kalendermonats (ISO-Woche).
- **ÜberstundenInsgesamt**: kumulierte Differenz seit dem frühesten Eintrag
  bzw. einem konfigurierbaren Startdatum (`overtime_carryover`-Logik: monatlich
  verfallene Überstunden fließen ab dem Stichtag nicht mehr ein).
- `TIME_OFF_IN_LIEU`-Einträge reduzieren den Überstundenstand im Zeitraum,
  in dem sie liegen.

Alle Werte sind **reine Funktionen** der DB-Inhalte → jederzeit reproduzierbar,
keine Gefahr inkonsistenter Zwischenspeicher.

---

## 6. Klassenstruktur (Kern)

```python
# data/entities.py – reine Datenbehälter
@dataclass(frozen=True)
class Employer: ...
@dataclass(frozen=True)
class WorkingTimeModel: ...
@dataclass(frozen=True)
class Entry:
    ...
    def duration(self) -> timedelta | None:   # reine Hilfsberechnung, kein DB-Zugriff
        ...

# data/repositories/*.py – nur CRUD + Abfragen
class EntryRepository:
    def get_active(self, employer_id: UUID) -> Entry | None: ...
    def list_between(self, start: datetime, end: datetime) -> list[Entry]: ...
    def save(self, entry: Entry) -> None: ...
    def soft_delete(self, entry_id: UUID) -> None: ...

# logic – Fachlogik
class TrackingService:        # Einstempeln, Ausstempeln, Validierung, CRUD-Orchestrierung
class OvertimeService:        # ist/soll/overtime je Zeitraum
class AnalysisService:        # Verlaufsansichten (liefert DTOs für die UI)
class ExportService:          # CSV (utf-8-sig, ; oder , konfigurierbar)
class SettingsService:        # key-value mit Typvalidierung
class SyncService:            # nutzt SyncBackend-Interface (v1: no-op)

# data/sync/sync_backend.py
class SyncBackend(ABC):
    def push(self, snapshot: SyncSnapshot) -> None: ...
    def pull(self) -> SyncSnapshot | None: ...
```

### DTOs für die UI (Beispiel)

```python
@dataclass(frozen=True)
class PeriodSummary:          # Rückgabetyp von AnalysisService
    period_type: Literal["week","month","year","total"]
    start: date
    end: date
    target_hours: float
    actual_hours: float
    overtime_hours: float
    entries: list[Entry]
```

Die UI-Screens halten ausschließlich solche DTOs + den aktiven Entry und sind
damit trivial testbar.

---

## 7. UI-Konzept (Kivy)

- `ScreenManager` mit Screens: Dashboard, Verlauf, Einträge, Eintrag-Editor,
  Einstellungen.
- **Dashboard**: Live-Dauer-Label (statusbasiert, s. 3.3), WochenSoll,
  WochenIst, ÜberstundenWoche, ÜberstundenMonat, ÜberstundenInsgesamt;
  Kacheln sind ein-/ausblendbar und neu anordenbar (per Drag & Drop in
  `RecycleGridLayout`); Layout wird in `settings` als JSON gespeichert.
- **Verlauf**: Tabs/Filter Woche · Monat · Jahr · Insgesamt mit
  `PeriodSummary`-Inhalten.
- **Einträge**: `RecycleView`-Liste, sortiert nach `start_time` (neu → alt),
  Tap öffnet Editor.
- **Einstellungen**: Sprache, Arbeitgeber + Arbeitszeitmodelle verwalten,
  Pausen-Default, Überstunden-Verfall, Sync (v1 nur „kein Sync").
- **i18n**: gettext, `_()`-Auferuf in allen Screens; Sprachwechsel ohne
  Neustart (Neuaufbau der Screens).

---

## 8. Sync (Design jetzt, Implementierung später)

- Einzige Sync-Einheit: die SQLite-Datei bzw. ein exportierter
  `SyncSnapshot` (JSON) mit den Tabellen `employer`,
  `working_time_model`, `entry` + `last_sync_at`.
- Konfliktstrategie: **Last-Writer-Wins je Eintrag** anhand `updated_at`;
  Soft-Deletes gewinnen gegen Updates (Tombstones).
- UUIDs machen offline erzeugte Einträge kollisionsfrei.
- `SyncBackend`-Interface erlaubt spätere Implementierungen:
  `WebDavBackend`, `GoogleDriveBackend`, `FileBackend` (nativer
  File-Manager / geteiltes Verzeichnis), ohne dass Logic oder UI angefasst
  werden müssen.

---

## 9. Offene Fragen (nächste Schritte)

1. **Elternzeit**: zählt sie als erfüllte Sollstunden oder scheidet sie
   (wie arbeitsrechtlich üblich) aus der Sollarbeitszeit aus? → Entscheidung
   vor Implementierung des `entry_type`-Mappings.
2. **Überstundenverfall**: Sollen Überstunden monatlich/jährlich verfallen
   (Kirchen haben oft eigene Dienstvereinbarungen)? Konfigurierbar über
   `overtime_carryover`, aber der Default muss definiert werden.
3. **Arbeitstag-Definition**: Ist Montag–Freitag fix oder pro Employer
   konfigurierbar (z. B. Pastor mit Samstagsdienst)?
4. **Gleitzeit/Puffer**: Soll es eine tägliche Gleitzeitbandbreite geben
   (±x Minuten gelten als 0 Überstunden)?
5. **Feiertage**: Manuell eintragen oder automatischer Feiertagskalender
   (Bundesland!)?
6. **Monatsmodell**: Pauschale 40 h/Woche als 160–176 h/Monat oder
   kalendergenaue Verteilung? (Design aktuell: kalendergenau.)
7. **CSV-Format**: deutsches Format (`;`, Dezimalkomma) vs. internationales
   Format – oder beides wählbar?
8. **Backup**: Reicht der Sync als Backup, oder soll es zusätzlich einen
   manuellen DB-Export/Import geben (empfohlen für v1)?

---

## 10. Umsetzungsreihenfolge (Vorschlag)

1. `data` (Schema, Entities, Repositories) + Tests
2. `logic` (Modelle, TrackingService, OvertimeService) + Tests
3. `ui` Dashboard + Ein-/Ausstempeln
4. Einträge-Liste + Editor
5. Verlauf + Export
6. Einstellungen + i18n
7. Sync-Backends (WebDAV zuerst)
