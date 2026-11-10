from datetime import date, timedelta

from constants import EntryType
from data.database import Database, database_cursor
from data.entry import Entry
from data.project import Project
from logic.working_time_model import get_working_time_model

ABSENCE_FULFILLS_TARGET = {EntryType.URLAUB, EntryType.KRANKHEIT, EntryType.FEIERTAG}


class OvertimeService:
    """
    Ist/Soll/Überstunden je Zeitraum (ARCHITECTURE.md 5.3).

    Alle Werte sind reine Funktionen der DB-Inhalte; es gibt keine
    Zwischenspeicher. Berechnungen je Projekt.
    """

    def __init__(self, db: Database):
        self.db = db

    def entries_between(self, project: Project, start: date, end: date) -> list[Entry]:
        """Nicht gelöschte Einträge eines Projekts im Zeitraum (nach entry_date)."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute(
                "SELECT id FROM entries "
                "WHERE project_id = ? AND deleted_at IS NULL AND entry_date BETWEEN ? AND ?",
                (project.id, start, end),
            )
            return [Entry(self.db, row[0]) for row in cursor.fetchall()]

    def _absence_dates(self, entries: list[Entry]) -> set[date]:
        return {
            entry.entry_date
            for entry in entries
            if entry.entry_type in ABSENCE_FULFILLS_TARGET
        }

    def actual_hours(self, project: Project, start: date, end: date) -> float:
        """
        Ist-Stunden: Arbeitseinträge netto von Pausen; counts_as_work zählt stets.

        Überstundenausgleich reduziert die Ist-Stunden des Zeitraums.
        """
        total = timedelta()
        for entry in self.entries_between(project, start, end):
            if entry.entry_type == EntryType.UEBERSTUNDENAUSGLEICH:
                total -= entry.duration
            elif entry.entry_type == EntryType.ARBEIT or entry.counts_as_work:
                total += entry.duration - timedelta(minutes=entry.break_minutes)
        return total.total_seconds() / 3600

    def target_hours(self, project: Project, start: date, end: date) -> float:
        """
        Soll-Stunden: Tagessoll je Arbeitsmodell; Abwesenheitstage
        (Urlaub/Krankheit/Feiertag) gelten als erfülltes Soll.
        """
        model = get_working_time_model(project, self.db)
        absence_dates = self._absence_dates(self.entries_between(project, start, end))
        total = 0.0
        current = start
        while current <= end:
            if current not in absence_dates and current.weekday() in model.workdays:
                total += model.target_hours_for_day(current)
            current += timedelta(days=1)
        return total

    def overtime(self, project: Project, start: date, end: date) -> float:
        """Überstunden = Ist - Soll im Zeitraum (jede Minute über Soll zählt)."""
        return self.actual_hours(project, start, end) - self.target_hours(
            project, start, end
        )

    def overtime_week(self, project: Project, day: date | None = None) -> float:
        """Überstunden der ISO-Kalenderwoche von day (Default: heute)."""
        reference = day or date.today()
        start = reference - timedelta(days=reference.weekday())
        return self.overtime(project, start, start + timedelta(days=6))

    def overtime_month(self, project: Project, day: date | None = None) -> float:
        """Überstunden des Kalendermonats von day (Default: heute)."""
        reference = day or date.today()
        start = date(reference.year, reference.month, 1)
        next_month = date(
            reference.year + (reference.month == 12), reference.month % 12 + 1, 1
        )
        return self.overtime(project, start, next_month - timedelta(days=1))

    def overtime_total(self, project: Project) -> float:
        """Kumulierte Überstunden seit dem frühesten Eintrag (ohne Verfall)."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute(
                "SELECT MIN(entry_date) FROM entries WHERE project_id = ? AND deleted_at IS NULL",
                (project.id,),
            )
            row = cursor.fetchone()
        if not row or row[0] is None:
            return 0.0
        first_day = (
            row[0] if isinstance(row[0], date) else date.fromisoformat(str(row[0]))
        )
        return self.overtime(project, first_day, date.today())
