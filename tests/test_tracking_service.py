import os
import tempfile
import unittest
from datetime import date, datetime, timedelta

from constants import EntryType, HourType
from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.tracking_service import TrackingError, TrackingService


class TestTrackingService(unittest.TestCase):
    """TrackingService: Invarianten und Statusübergänge (ARCHITECTURE.md 3.6/5.2)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = TrackingService(self.db)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)

    def tearDown(self):
        self._tmp.cleanup()

    def test_clock_in_creates_active_entry(self):
        entry = self.service.clock_in(self.project)
        self.assertTrue(entry.is_active)
        self.assertIsNone(entry.end_at)
        self.assertEqual(entry.entry_type, EntryType.ARBEIT)
        self.assertEqual(entry.entry_date, date.today())
        self.assertEqual(self.service.get_active_entry().id, entry.id)

    def test_clock_in_rejects_second_active_entry(self):
        self.service.clock_in(self.project)
        with self.assertRaises(TrackingError):
            self.service.clock_in(self.project)

    def test_clock_out_ends_entry(self):
        entry = self.service.clock_in(self.project)
        finished = self.service.clock_out(entry)
        self.assertFalse(finished.is_active)
        self.assertIsNotNone(finished.end_at)
        self.assertIsNotNone(finished.edited_at)
        self.assertIsNone(self.service.get_active_entry())

    def test_clock_out_rejects_inactive_entry(self):
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        with self.assertRaises(TrackingError):
            self.service.clock_out(entry)

    def test_update_times_corrects_window(self):
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        begin = datetime(2026, 3, 30, 8, 0)
        end = datetime(2026, 3, 30, 16, 0)
        self.service.update_times(entry, begin, end)
        reloaded = Entry(self.db, entry.id)
        self.assertEqual(reloaded.begin_at, begin)
        self.assertEqual(reloaded.end_at, end)
        self.assertIsNotNone(reloaded.edited_at)

    def test_update_times_rejects_end_before_begin(self):
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        begin = datetime(2026, 3, 30, 16, 0)
        end = datetime(2026, 3, 30, 8, 0)
        with self.assertRaises(TrackingError):
            self.service.update_times(entry, begin, end)

    def test_update_times_rejects_end_on_active_entry(self):
        entry = self.service.clock_in(self.project)
        with self.assertRaises(TrackingError):
            self.service.update_times(
                entry, datetime(2026, 3, 30, 8, 0), datetime(2026, 3, 30, 16, 0)
            )

    def test_update_times_rejects_missing_end_on_finished_entry(self):
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        with self.assertRaises(TrackingError):
            self.service.update_times(entry, datetime(2026, 3, 30, 8, 0), None)

    def test_update_times_allows_begin_correction_on_active_entry(self):
        entry = self.service.clock_in(self.project)
        begin = datetime.now() - timedelta(hours=1)
        self.service.update_times(entry, begin, None)
        self.assertEqual(entry.begin_at, begin)
        self.assertTrue(entry.is_active)

    def test_delete_entry_is_soft(self):
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        self.service.delete_entry(entry)
        reloaded = Entry(self.db, entry.id)
        self.assertIsNotNone(reloaded.deleted_at)
        self.assertIsNotNone(reloaded.edited_at)

    def test_deleted_active_entry_is_not_returned(self):
        entry = self.service.clock_in(self.project)
        self.service.delete_entry(entry)
        self.assertIsNone(self.service.get_active_entry())

    def test_clock_in_after_soft_delete_works(self):
        entry = self.service.clock_in(self.project)
        self.service.delete_entry(entry)
        new_entry = self.service.clock_in(self.project)
        self.assertTrue(new_entry.is_active)

    def test_midnight_span_entry(self):
        """Grenzfall: Schicht über Mitternacht."""
        entry = self.service.clock_in(self.project)
        self.service.clock_out(entry)
        begin = datetime(2026, 3, 30, 22, 0)
        end = datetime(2026, 3, 31, 6, 0)
        self.service.update_times(entry, begin, end)
        self.assertEqual(entry.duration, timedelta(hours=8))
