from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date, timedelta

from constants import HourType
from data.database import Database
from data.project import Project

DEFAULT_WORKDAYS = {0, 1, 2, 3, 4}


def _count_workdays(days: set[int], start: date, end: date) -> int:
    """Zählt Tage zwischen start und end (inklusive), die in days liegen."""
    count = 0
    current = start
    while current <= end:
        if current.weekday() in days:
            count += 1
        current += timedelta(days=1)
    return count


class AbstractWorkingTimeModel(ABC):
    """
    Sollstunden-Strategie je HourType (ARCHITECTURE.md 5.1).

    Ein Projekt hat genau einen Stundenanker target_hours; die Semantik
    ergibt sich aus hour_type. workdays ist die Menge der ISO-Wochentage
    (Mo=0 ... So=6), an denen das Projekt Arbeitszeit vorsieht.
    """

    def __init__(self, project: Project):
        self.project = project
        self.workdays = project.workdays or DEFAULT_WORKDAYS

    @abstractmethod
    def target_hours_for_day(self, day: date) -> float:
        """Sollstunden eines einzelnen Tages."""

    @abstractmethod
    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float:
        """Sollstunden einer ISO-Kalenderwoche."""

    @abstractmethod
    def target_hours_for_month(self, year: int, month: int) -> float:
        """Sollstunden eines Kalendermonats."""

    @abstractmethod
    def target_hours_total(self, since: date | None = None) -> float:
        """Kumulierte Sollstunden ab einem Datum (None: Projektbeginn/gesamt)."""

    def _sum_days(self, start: date, end: date) -> float:
        """Summiert die Tagessollstunden zwischen start und end (inklusive)."""
        return sum(
            self.target_hours_for_day(start + timedelta(days=i))
            for i in range((end - start).days + 1)
        )


class WeeklyModel(AbstractWorkingTimeModel):
    """target_hours = Stunden pro Woche, gleichverteilt auf workdays."""

    def target_hours_for_day(self, day: date) -> float:
        """Sollstunden eines einzelnen Tages."""
        if day.weekday() not in self.workdays:
            return 0.0
        return self.project.target_hours / len(self.workdays)

    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float:
        """Sollstunden einer ISO-Kalenderwoche."""
        return self.project.target_hours

    def target_hours_for_month(self, year: int, month: int) -> float:
        """Sollstunden eines Kalendermonats."""
        return self._sum_days(
            date(year, month, 1), date(year, month, monthrange(year, month)[1])
        )

    def target_hours_total(self, since: date | None = None) -> float:
        """Kumulierte Sollstunden ab einem Datum (None: Projektbeginn/gesamt)."""
        if since is None:
            return self.project.target_hours
        return self._sum_days(since, date.today())


class DailyModel(AbstractWorkingTimeModel):
    """target_hours = Stunden pro Arbeitstag; daily_hours_override überschreibt einzelne Tage."""

    def target_hours_for_day(self, day: date) -> float:
        """Sollstunden eines einzelnen Tages."""
        if day.weekday() not in self.workdays:
            return 0.0
        return self.project.daily_hours_override.get(
            day.weekday(), self.project.target_hours
        )

    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float:
        """Sollstunden einer ISO-Kalenderwoche."""
        start = date.fromisocalendar(iso_year, iso_week, 1)
        return self._sum_days(start, start + timedelta(days=6))

    def target_hours_for_month(self, year: int, month: int) -> float:
        """Sollstunden eines Kalendermonats."""
        return self._sum_days(
            date(year, month, 1), date(year, month, monthrange(year, month)[1])
        )

    def target_hours_total(self, since: date | None = None) -> float:
        """Kumulierte Sollstunden ab einem Datum (None: Projektbeginn/gesamt)."""
        if since is None:
            return self.target_hours_for_day(date.today())
        return self._sum_days(since, date.today())


class MonthlyModel(AbstractWorkingTimeModel):
    """target_hours = Stunden pro Monat (pauschal); Woche anteilig nach Arbeitstagen."""

    def _workdays_in_month(self, year: int, month: int) -> int:
        """Zählt die Arbeitstage eines Kalendermonats."""
        return _count_workdays(
            self.workdays,
            date(year, month, 1),
            date(year, month, monthrange(year, month)[1]),
        )

    def target_hours_for_day(self, day: date) -> float:
        """Sollstunden eines einzelnen Tages."""
        if day.weekday() not in self.workdays:
            return 0.0
        return self.project.target_hours / self._workdays_in_month(day.year, day.month)

    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float:
        """Sollstunden einer ISO-Kalenderwoche."""
        start = date.fromisocalendar(iso_year, iso_week, 1)
        month_of_week = (start + timedelta(days=3)).month
        year_of_week = (start + timedelta(days=3)).year
        workdays_in_week = _count_workdays(
            self.workdays, start, start + timedelta(days=6)
        )
        return self.project.target_hours * (
            workdays_in_week / self._workdays_in_month(year_of_week, month_of_week)
        )

    def target_hours_for_month(self, year: int, month: int) -> float:
        """Sollstunden eines Kalendermonats."""
        return self.project.target_hours

    def target_hours_total(self, since: date | None = None) -> float:
        """Kumulierte Sollstunden ab einem Datum (None: Projektbeginn/gesamt)."""
        if since is None:
            return self.project.target_hours
        total = 0.0
        current = date(since.year, since.month, 1)
        today = date.today()
        while current <= date(today.year, today.month, 1):
            total += self.target_hours_for_month(current.year, current.month)
            current = date(
                current.year + (current.month == 12), current.month % 12 + 1, 1
            )
        return total


class AllTimeModel(AbstractWorkingTimeModel):
    """target_hours = Gesamtvolumen; Zeitraumanteil nach Arbeitstagen (v1 UI-deaktiviert)."""

    def __init__(self, project: Project, db: Database):
        super().__init__(project)
        self.db = db
        self._anchor: date | None = None

    def anchor_date(self) -> date:
        """Frühestes entry_date des Projekts als Verteilungsbeginn."""
        if self._anchor is None:
            self._anchor = self.db.get_first_entry_date(self.project.id) or date.today()
        return self._anchor

    def _total_workdays(self) -> int:
        """Zählt die Arbeitstage vom Anker bis heute (mindestens 1)."""
        return max(_count_workdays(self.workdays, self.anchor_date(), date.today()), 1)

    def _share(self, period_workdays: int) -> float:
        """Anteil des Gesamtvolmens nach Arbeitstagen, geklemmt auf [0, 1]."""
        return min(period_workdays / self._total_workdays(), 1.0)

    def target_hours_for_day(self, day: date) -> float:
        """Sollstunden eines einzelnen Tages."""
        if day.weekday() not in self.workdays:
            return 0.0
        return self.project.target_hours * self._share(1)

    def target_hours_for_week(self, iso_year: int, iso_week: int) -> float:
        """Sollstunden einer ISO-Kalenderwoche."""
        start = date.fromisocalendar(iso_year, iso_week, 1)
        workdays_in_week = _count_workdays(
            self.workdays, start, start + timedelta(days=6)
        )
        return self.project.target_hours * self._share(workdays_in_week)

    def target_hours_for_month(self, year: int, month: int) -> float:
        """Sollstunden eines Kalendermonats."""
        workdays_in_month = _count_workdays(
            self.workdays,
            date(year, month, 1),
            date(year, month, monthrange(year, month)[1]),
        )
        return self.project.target_hours * self._share(workdays_in_month)

    def target_hours_total(self, since: date | None = None) -> float:
        """Kumulierte Sollstunden ab einem Datum (None: Projektbeginn/gesamt)."""
        return self.project.target_hours


def get_working_time_model(project: Project, db: Database) -> AbstractWorkingTimeModel:
    """Factory: erzeugt die Sollstunden-Strategie passend zum HourType."""
    if project.hour_type == HourType.WEEKLY:
        return WeeklyModel(project)
    if project.hour_type == HourType.DAILY:
        return DailyModel(project)
    if project.hour_type == HourType.MONTHLY:
        return MonthlyModel(project)
    if project.hour_type == HourType.ALLTIME:
        return AllTimeModel(project, db)
    raise ValueError(f"Unbekannter HourType: {project.hour_type}")
