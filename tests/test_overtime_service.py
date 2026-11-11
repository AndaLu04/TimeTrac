import os
import tempfile
import unittest
from datetime import date, datetime, timedelta

from constants import EntryType, HourType
from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.overtime_service import OvertimeService


class TestOvertimeService(unittest.TestCase):
    """OvertimeService: Ist/Soll/Überstunden je Zeitraum (ARCHITECTURE.md 5.3)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = OvertimeService(self.db)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)

    def tearDown(self):
        self._tmp.cleanup()

    def _work_entry(
        self,
        day,
        begin,
        end,
        break_minutes=0,
        entry_type=EntryType.ARBEIT,
        counts_as_work=None,
    ):
        entry = Entry(
            self.db,
            None,
            self.project.id,
            entry_type=entry_type,
            entry_date=day,
            begin_at=(
                datetime.combine(day, begin) if isinstance(begin, timedelta) else begin
            ),
            end_at=datetime.combine(day, end) if isinstance(end, timedelta) else end,
        )
        entry.break_minutes = break_minutes
        if counts_as_work is not None:
            entry.counts_as_work = counts_as_work
        return entry

    def test_actual_hours_net_of_breaks(self):
        day = date(2026, 11, 16)
        self._work_entry(
            day,
            datetime(2026, 11, 16, 8, 0),
            datetime(2026, 11, 16, 16, 30),
            break_minutes=30,
        )
        self.assertAlmostEqual(self.service.actual_hours(self.project, day, day), 8.0)

    def test_actual_hours_counts_explicit_work_flag(self):
        day = date(2026, 11, 16)
        self._work_entry(
            day,
            datetime(2026, 11, 16, 10, 0),
            datetime(2026, 11, 16, 12, 0),
            entry_type=EntryType.SONSTIGES,
            counts_as_work=True,
        )
        self.assertAlmostEqual(self.service.actual_hours(self.project, day, day), 2.0)

    def test_sonstiges_without_flag_does_not_count(self):
        day = date(2026, 11, 16)
        self._work_entry(
            day,
            datetime(2026, 11, 16, 10, 0),
            datetime(2026, 11, 16, 12, 0),
            entry_type=EntryType.SONSTIGES,
        )
        self.assertEqual(self.service.actual_hours(self.project, day, day), 0.0)

    def test_absence_fulfills_target(self):
        """Urlaubstag gilt als erfülltes Soll, auch wenn nicht gearbeitet wurde."""
        day = date(2026, 11, 16)  # Montag, 8h Soll
        Entry(
            self.db, None, self.project.id, entry_type=EntryType.URLAUB, entry_date=day
        )
        self.assertAlmostEqual(self.service.target_hours(self.project, day, day), 0.0)
        self.assertAlmostEqual(self.service.overtime(self.project, day, day), 0.0)

    def test_krankheit_and_feiertag_fulfill_target(self):
        for entry_type in (EntryType.KRANKHEIT, EntryType.FEIERTAG):
            day = date(2026, 11, 17)
            Entry(self.db, None, self.project.id, entry_type=entry_type, entry_date=day)
            self.assertAlmostEqual(self.service.overtime(self.project, day, day), 0.0)

    def test_elternzeit_is_informative_only(self):
        """Elternzeit scheidet aus: kein Sollguthaben, keine Ist-Stunden."""
        day = date(2026, 11, 17)
        Entry(
            self.db,
            None,
            self.project.id,
            entry_type=EntryType.ELTERNZEIT,
            entry_date=day,
        )
        self.assertEqual(self.service.actual_hours(self.project, day, day), 0.0)
        self.assertAlmostEqual(self.service.overtime(self.project, day, day), -8.0)

    def test_ueberstundenausgleich_reduces_balance(self):
        """Voller Arbeitstag plus 4h Ausgleich reduziert den Bestand um 4h."""
        day = date(2026, 11, 16)
        self._work_entry(
            day, datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 16, 0)
        )
        self._work_entry(
            day,
            datetime(2026, 11, 16, 17, 0),
            datetime(2026, 11, 16, 21, 0),
            entry_type=EntryType.UEBERSTUNDENAUSGLEICH,
        )
        self.assertAlmostEqual(self.service.overtime(self.project, day, day), -4.0)

    def test_overtime_week(self):
        monday = date(2026, 11, 16)
        self._work_entry(
            monday, datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 18, 0)
        )
        self.assertAlmostEqual(
            self.service.overtime_week(self.project, monday), 10.0 - 40.0
        )

    def test_overtime_month(self):
        day = date(2026, 11, 16)
        self._work_entry(
            day, datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 18, 0)
        )
        self.assertAlmostEqual(
            self.service.overtime_month(self.project, day), 10.0 - 21 * 8
        )

    def test_overtime_total_since_first_entry(self):
        day = date(2026, 11, 2)
        self._work_entry(day, datetime(2026, 11, 2, 8, 0), datetime(2026, 11, 2, 18, 0))
        balance = self.service.overtime_total(self.project)
        expected = self.service.overtime(self.project, day, date.today())
        self.assertAlmostEqual(balance, expected)

    def test_deleted_entries_are_excluded(self):
        day = date(2026, 11, 16)
        entry = self._work_entry(
            day, datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 16, 0)
        )
        entry.deleted_at = datetime.now()
        self.assertEqual(self.service.actual_hours(self.project, day, day), 0.0)

    def test_midnight_span_counts_on_entry_date(self):
        """Grenzfall: Schicht 22:00-06:00 gehört zum entry_date."""
        day = date(2026, 11, 16)
        self._work_entry(
            day, datetime(2026, 11, 16, 22, 0), datetime(2026, 11, 17, 6, 0)
        )
        self.assertAlmostEqual(self.service.actual_hours(self.project, day, day), 8.0)
        self.assertEqual(
            self.service.actual_hours(
                self.project, date(2026, 11, 17), date(2026, 11, 17)
            ),
            0.0,
        )

    def test_summer_time_week_is_correct(self):
        """Grenzfall: Woche der Sommerzeitumstellung (29.03.2026)."""
        day = date(2026, 3, 30)  # Montag nach Umstellung
        self._work_entry(day, datetime(2026, 3, 30, 8, 0), datetime(2026, 3, 30, 16, 0))
        self.assertAlmostEqual(self.service.actual_hours(self.project, day, day), 8.0)

    def test_month_boundary_entries_split_correctly(self):
        """Grenzfall: Einträge am letzten und ersten Tag des Monats."""
        end_of_month = date(2026, 11, 30)
        first_of_next = date(2026, 12, 1)
        self._work_entry(
            end_of_month, datetime(2026, 11, 30, 8, 0), datetime(2026, 11, 30, 16, 0)
        )
        self._work_entry(
            first_of_next, datetime(2026, 12, 1, 8, 0), datetime(2026, 12, 1, 16, 0)
        )
        month_hours = self.service.actual_hours(
            self.project, date(2026, 11, 1), end_of_month
        )
        self.assertAlmostEqual(month_hours, 8.0)

    def test_no_entries_gives_zero(self):
        empty_project = Project(self.db, None, "Leer", 40, HourType.WEEKLY)
        self.assertEqual(self.service.overtime_total(empty_project), 0.0)
