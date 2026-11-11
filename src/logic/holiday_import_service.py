from datetime import date
from pathlib import Path

from constants import EntryType
from data.database import Database
from data.entry import Entry
from data.project import Project


class HolidayImportService:
    """
    Importiert Feiertage aus einer ICS-Kalenderdatei als FEIERTAG-Entries
    (ARCHITECTURE.md 5.6). Die manuelle Feiertagseintragung bleibt davon
    unberührt; der Import ist rein optional.
    """

    def __init__(self, db: Database):
        self.db = db

    def import_ics(
        self, ics_path: Path, project: Project, year: int | None = None
    ) -> list[Entry]:
        """
        Liest ganztägige VEVENTs aus der ICS-Datei und erzeugt FEIERTAG-Entries.

        Args:
            ics_path: Pfad zur ICS-Datei.
            project: Projekt, dem die Feiertags-Entries zugeordnet werden.
            year: Optionaler Filter auf ein Kalenderjahr (None: alle Jahre).

        Returns:
            Die neu erzeugten Entries (Duplikate werden übersprungen).
        """
        created = []
        for holiday_date, summary in self.parse_ics(ics_path):
            if year is not None and holiday_date.year != year:
                continue
            if self._holiday_entry_exists(project, holiday_date):
                continue
            created.append(
                Entry(
                    self.db,
                    None,
                    project.id,
                    entry_type=EntryType.FEIERTAG,
                    entry_date=holiday_date,
                    notes=summary,
                )
            )
        return created

    def parse_ics(self, ics_path: Path) -> list[tuple[date, str]]:
        """Extrahiert (Datum, Zusammenfassung) aller ganztägigen VEVENTs."""
        events = []
        current_date = None
        current_summary = ""
        in_event = False
        for raw_line in Path(ics_path).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "BEGIN:VEVENT":
                in_event = True
                current_date = None
                current_summary = ""
            elif line == "END:VEVENT":
                if in_event and current_date is not None:
                    events.append((current_date, current_summary))
                in_event = False
            elif in_event and line.startswith("DTSTART;VALUE=DATE:"):
                value = line.split("DTSTART;VALUE=DATE:", 1)[1]
                if len(value) == 8 and value.isdigit():
                    try:
                        current_date = date(
                            int(value[:4]), int(value[4:6]), int(value[6:])
                        )
                    except ValueError:
                        current_date = None
                else:
                    current_date = None
            elif in_event and line.startswith("SUMMARY:"):
                current_summary = line.split("SUMMARY:", 1)[1]
        return events

    def _holiday_entry_exists(self, project: Project, day: date) -> bool:
        return self.db.entry_exists(project.id, EntryType.FEIERTAG, day)
