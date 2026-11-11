import os
import tempfile
import unittest
from datetime import date, datetime

from constants import HourType
from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.analysis_service import AnalysisService, PeriodSummary


class TestAnalysisService(unittest.TestCase):
    """AnalysisService: PeriodSummary-DTOs für Woche/Monat/Jahr/Insgesamt."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = AnalysisService(self.db)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)

    def tearDown(self):
        self._tmp.cleanup()

    def _add_work(self, day, hours=8.0):
        begin = datetime.combine(day, datetime.min.time()).replace(hour=8)
        Entry(
            self.db,
            None,
            self.project.id,
            entry_date=day,
            begin_at=begin,
            end_at=begin.replace(hour=8 + int(hours)),
        )

    def test_week_summary_contains_dto(self):
        day = date(2026, 11, 16)
        self._add_work(day)
        summary = self.service.week_summary(self.project, day)
        self.assertIsInstance(summary, PeriodSummary)
        self.assertEqual(summary.period_type, "week")
        self.assertEqual(summary.start, date(2026, 11, 16))
        self.assertEqual(summary.end, date(2026, 11, 22))
        self.assertAlmostEqual(summary.actual_hours, 8.0)
        self.assertAlmostEqual(summary.target_hours, 40.0)
        self.assertAlmostEqual(summary.overtime_hours, -32.0)
        self.assertEqual(len(summary.entries), 1)

    def test_month_summary(self):
        day = date(2026, 11, 16)
        self._add_work(day)
        summary = self.service.month_summary(self.project, day)
        self.assertEqual(summary.period_type, "month")
        self.assertEqual(summary.start, date(2026, 11, 1))
        self.assertEqual(summary.end, date(2026, 11, 30))
        self.assertAlmostEqual(summary.target_hours, 168.0)

    def test_year_summary(self):
        day = date(2026, 11, 16)
        self._add_work(day)
        summary = self.service.year_summary(self.project, day)
        self.assertEqual(summary.period_type, "year")
        self.assertEqual(summary.start, date(2026, 1, 1))
        self.assertEqual(summary.end, date(2026, 12, 31))

    def test_total_summary_starts_at_first_entry(self):
        day = date(2026, 11, 2)
        self._add_work(day)
        summary = self.service.total_summary(self.project)
        self.assertEqual(summary.period_type, "total")
        self.assertEqual(summary.start, day)
        self.assertEqual(summary.end, date.today())

    def test_empty_project_summary(self):
        empty = Project(self.db, None, "Leer", 40, HourType.WEEKLY)
        summary = self.service.week_summary(empty, date(2026, 11, 16))
        self.assertEqual(summary.actual_hours, 0.0)
        self.assertEqual(summary.entries, [])

    def test_year_boundary_entries(self):
        """Grenzfall: Einträge an Jahreswechsel gehören ins richtige Jahr."""
        december = date(2026, 12, 31)
        january = date(2027, 1, 1)
        self._add_work(december)
        self._add_work(january)
        summary_2026 = self.service.year_summary(self.project, december)
        self.assertAlmostEqual(summary_2026.actual_hours, 8.0)
        summary_2027 = self.service.year_summary(self.project, january)
        self.assertAlmostEqual(summary_2027.actual_hours, 8.0)

    def test_dto_is_frozen(self):
        from dataclasses import FrozenInstanceError

        summary = self.service.week_summary(self.project, date(2026, 11, 16))
        with self.assertRaises(FrozenInstanceError):
            summary.actual_hours = 1.0
