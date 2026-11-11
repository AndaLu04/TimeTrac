from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.overtime_service import OvertimeService

PeriodType = Literal["week", "month", "year", "total"]


@dataclass(frozen=True)
class PeriodSummary:
    """DTO für Verlaufsansichten der UI (ARCHITECTURE.md 5.4)."""

    period_type: PeriodType
    start: date
    end: date
    target_hours: float
    actual_hours: float
    overtime_hours: float
    entries: list[Entry]


class AnalysisService:
    """Liefert PeriodSummary-DTOs für Woche/Monat/Jahr/Insgesamt je Projekt."""

    def __init__(self, db: Database):
        self.db = db
        self.overtime_service = OvertimeService(self.db)

    def summary_for_range(
        self, project: Project, period_type: PeriodType, start: date, end: date
    ) -> PeriodSummary:
        actual = self.overtime_service.actual_hours(project, start, end)
        target = self.overtime_service.target_hours(project, start, end)
        entries = self.overtime_service.entries_between(project, start, end)
        return PeriodSummary(
            period_type=period_type,
            start=start,
            end=end,
            target_hours=target,
            actual_hours=actual,
            overtime_hours=actual - target,
            entries=entries,
        )

    def week_summary(self, project: Project, day: date | None = None) -> PeriodSummary:
        reference = day or date.today()
        start = reference - timedelta(days=reference.weekday())
        return self.summary_for_range(project, "week", start, start + timedelta(days=6))

    def month_summary(self, project: Project, day: date | None = None) -> PeriodSummary:
        reference = day or date.today()
        start = date(reference.year, reference.month, 1)
        next_month = date(
            reference.year + (reference.month == 12), reference.month % 12 + 1, 1
        )
        return self.summary_for_range(
            project, "month", start, next_month - timedelta(days=1)
        )

    def year_summary(self, project: Project, day: date | None = None) -> PeriodSummary:
        reference = day or date.today()
        return self.summary_for_range(
            project, "year", date(reference.year, 1, 1), date(reference.year, 12, 31)
        )

    def total_summary(self, project: Project) -> PeriodSummary:
        start = self._first_entry_date(project)
        return self.summary_for_range(project, "total", start, date.today())

    def _first_entry_date(self, project: Project) -> date:
        return self.db.get_first_entry_date(project.id) or date.today()
