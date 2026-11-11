from csv import writer
from datetime import date
from io import StringIO

from data.database import Database
from data.project import Project
from logic.overtime_service import OvertimeService

CSV_COLUMNS = ["Datum", "Beginn", "Ende", "Pause", "Typ", "Projekt", "Notiz", "Dauer"]


class ExportService:
    """CSV-Export von Einträgen je Projekt und Zeitraum (ARCHITECTURE.md 5.5)."""

    def __init__(self, db: Database):
        self.db = db
        self.overtime_service = OvertimeService(self.db)

    def export_csv(
        self,
        project: Project,
        start: date,
        end: date,
        delimiter: str = ",",
        decimal_separator: str = ",",
    ) -> str:
        """
        Erzeugt CSV (UTF-8-Inhalt) der Einträge im Zeitraum.

        Args:
            project: Das zu exportierende Projekt.
            start/end: Zeitraum (inklusive), gefiltert nach entry_date.
            delimiter: Frei eintragbares Trennzeichen (Default ',').
            decimal_separator: Dezimaltrennzeichen der Stundenspalte
                (folgt der Sprache, z. B. ',' für de).
        """
        buffer = StringIO()
        csv_writer = writer(buffer, delimiter=delimiter, lineterminator="\n")
        csv_writer.writerow(CSV_COLUMNS)
        for entry in self.overtime_service.entries_between(project, start, end):
            csv_writer.writerow(
                [
                    entry.entry_date.isoformat(),
                    entry.begin_at.strftime("%H:%M") if entry.begin_at else "",
                    entry.end_at.strftime("%H:%M") if entry.end_at else "",
                    entry.break_minutes,
                    entry.entry_type.value,
                    self._neutralize_formula(project.name),
                    self._neutralize_formula(entry.notes or ""),
                    self._format_hours(entry.duration, decimal_separator),
                ]
            )
        return buffer.getvalue()

    def _format_hours(self, duration, decimal_separator: str) -> str:
        """Formatiert eine Dauer in Stunden mit konfigurierbarem Dezimaltrennzeichen."""
        hours = duration.total_seconds() / 3600
        return f"{hours:.2f}".replace(".", decimal_separator)

    def _neutralize_formula(self, text: str) -> str:
        """Neutralisiert Formelinjektion: führende =, +, -, @ werden mit ' maskiert."""
        if text and text[0] in ("=", "+", "-", "@"):
            return f"'{text}"
        return text
