from datetime import date
from pathlib import Path

from constants import HALF_DAY_MARKER, EntryType
from data.database import Database
from data.entry import Entry
from data.project import Project


class HolidayImportService:
    """
    Importiert Feiertage aus einer ICS-Kalenderdatei als FEIERTAG-Entries
    (ARCHITECTURE.md 5.6). Die manuelle Feiertagseintragung bleibt davon
    unberührt; der Import ist rein optional.

    Der Parser unterstützt ausschließlich ganztägige Events (DTSTART als
    Datum, mit oder ohne VALUE=DATE-Parameter). Events mit Datum-Zeit-
    DTSTART werden übersprungen.
    """

    def __init__(self, db: Database):
        self.db = db

    def import_ics(
        self,
        ics_path: Path,
        project: Project,
        year: int | None = None,
        bundesland: str | None = None,
        half_day_summaries: frozenset[str] = frozenset(),
    ) -> list[Entry]:
        """
        Liest ganztägige VEVENTs aus der ICS-Datei und erzeugt FEIERTAG-Entries.

        Args:
            ics_path: Pfad zur ICS-Datei.
            project: Projekt, dem die Feiertags-Entries zugeordnet werden.
            year: Optionaler Filter auf ein Kalenderjahr (None: alle Jahre).
            bundesland: Optionaler Filter; behält nur Events, deren
                CATEGORIES das Bundesland enthalten (Groß-/Kleinschreibung
                egal). None: alle Events.
            half_day_summaries: Zusammenfassungen, die als halbe Feiertage
                gelten; ihre Entries werden im Notes mit HALF_DAY_MARKER
                markiert, sodass der OvertimeService nur das halbe Soll erlässt.

        Returns:
            Die neu erzeugten Entries (Duplikate werden übersprungen).
        """
        created = []
        for holiday_date, summary, categories in self.parse_ics(ics_path):
            if year is not None and holiday_date.year != year:
                continue
            if bundesland is not None and bundesland.lower() not in categories:
                continue
            if self._holiday_entry_exists(project, holiday_date):
                continue
            notes = summary
            if summary in half_day_summaries:
                notes = f"{HALF_DAY_MARKER}: {summary}"
            created.append(
                Entry(
                    self.db,
                    None,
                    project.id,
                    entry_type=EntryType.FEIERTAG,
                    entry_date=holiday_date,
                    notes=notes,
                )
            )
        return created

    def parse_ics(self, ics_path: Path) -> list[tuple[date, str, frozenset[str]]]:
        """
        Extrahiert (Datum, Zusammenfassung, Kategorien) aller ganztägigen VEVENTs.

        Faltet zunächst RFC-5545-Fortsetzungszeilen (Zeilen, die mit Leerzeichen
        oder Tab beginnen, hängen an der vorherigen logischen Zeile).
        """

        def unfold(lines: list[str]) -> list[str]:
            """Faltet Fortsetzungszeilen (führendes Leerzeichen/Tab) an die Vorgängerzeile."""
            logical = []
            for raw_line in lines:
                if raw_line[:1] in (" ", "\t") and logical:
                    logical[-1] += raw_line[1:]
                else:
                    logical.append(raw_line)
            return logical

        events = []
        current_date = None
        current_summary = ""
        current_categories: frozenset[str] = frozenset()
        in_event = False
        for line in unfold(Path(ics_path).read_text(encoding="utf-8").splitlines()):
            line = line.strip()
            if line == "BEGIN:VEVENT":
                in_event = True
                current_date = None
                current_summary = ""
                current_categories = frozenset()
            elif line == "END:VEVENT":
                if in_event and current_date is not None:
                    events.append((current_date, current_summary, current_categories))
                in_event = False
            elif in_event and (
                line.startswith("DTSTART;VALUE=DATE:") or line.startswith("DTSTART:")
            ):
                value = line.split(":", 1)[1]
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
            elif in_event and line.startswith("CATEGORIES:"):
                current_categories = frozenset(
                    category.strip().lower()
                    for category in line.split("CATEGORIES:", 1)[1].split(",")
                )
        return events

    def _holiday_entry_exists(self, project: Project, day: date) -> bool:
        """Prüft, ob für das Projekt bereits ein Feiertag am Tag existiert."""
        return self.db.entry_of_type_exists(project.id, EntryType.FEIERTAG, day)
