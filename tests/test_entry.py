import unittest
from datetime import date, datetime, timedelta

from constants import EntryType
from data.database import Database
from data.entry import Entry
from data.project import Project


class TestEntry(unittest.TestCase):
    """Tests Entry persistence, lazy loading, type validation and duration.

    Each test uses its own temporary database file and project.
    """

    def setUp(self):
        import os
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.project = Project(self.db, None, "Testprojekt")
        self.project_id = self.project.id

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_entry_requires_project_id(self):
        """Creating a new entry without a project must fail."""
        with self.assertRaises(ValueError):
            Entry(self.db, None, None)

    def test_new_entry_is_persisted(self):
        entry = Entry(self.db, None, self.project_id)
        self.assertIn(entry.id, self.db.get_entry_ids_from_project_id(self.project_id))

    def test_new_entry_defaults(self):
        before = datetime.now()
        entry = Entry(self.db, None, self.project_id)
        self.assertEqual(entry.project_id, self.project_id)
        self.assertEqual(entry.entry_type, EntryType.ARBEIT)
        self.assertFalse(entry.is_active)
        self.assertIsNone(entry.end_at)
        self.assertIsNone(entry.notes)
        self.assertGreaterEqual(entry.created_at, before)
        self.assertGreaterEqual(entry.begin_at, before)
        self.assertEqual(entry.entry_date, date.today())

    def test_new_entry_with_explicit_values(self):
        begin = datetime(2024, 5, 1, 8, 0, 0)
        end = datetime(2024, 5, 1, 12, 30, 0)
        entry = Entry(self.db, None, self.project_id,
                      entry_type=EntryType.URLAUB, is_active=False,
                      created_at=begin, entry_date=begin.date(),
                      begin_at=begin, end_at=end, notes="Notiz")
        self.assertEqual(entry.entry_type, EntryType.URLAUB)
        self.assertEqual(entry.begin_at, begin)
        self.assertEqual(entry.end_at, end)
        self.assertEqual(entry.entry_date, date(2024, 5, 1))
        self.assertEqual(entry.notes, "Notiz")

    def test_load_existing_entry_lazily(self):
        created = Entry(self.db, None, self.project_id,
                        entry_type=EntryType.KRANKHEIT,
                        created_at=datetime(2024, 3, 1, 9, 0, 0),
                        entry_date=date(2024, 3, 1),
                        begin_at=datetime(2024, 3, 1, 9, 0, 0),
                        end_at=datetime(2024, 3, 1, 17, 0, 0),
                        notes="Krank")
        loaded = Entry(self.db, created.id)
        self.assertEqual(loaded.project_id, self.project_id)
        self.assertEqual(loaded.entry_type, EntryType.KRANKHEIT)
        self.assertEqual(loaded.created_at, datetime(2024, 3, 1, 9, 0, 0))
        self.assertEqual(loaded.entry_date, date(2024, 3, 1))
        self.assertEqual(loaded.begin_at, datetime(2024, 3, 1, 9, 0, 0))
        self.assertEqual(loaded.end_at, datetime(2024, 3, 1, 17, 0, 0))
        self.assertEqual(loaded.notes, "Krank")

    def test_setters_persist_changes(self):
        entry = Entry(self.db, None, self.project_id)
        entry.entry_type = EntryType.FEIERTAG
        entry.notes = "Feiertag"
        entry.edited_at = datetime(2024, 6, 1, 10, 0, 0)
        entry.end_at = datetime(2024, 6, 1, 12, 0, 0)
        reloaded = Entry(self.db, entry.id)
        self.assertEqual(reloaded.entry_type, EntryType.FEIERTAG)
        self.assertEqual(reloaded.notes, "Feiertag")
        self.assertEqual(reloaded.edited_at, datetime(2024, 6, 1, 10, 0, 0))
        self.assertEqual(reloaded.end_at, datetime(2024, 6, 1, 12, 0, 0))

    def test_setters_update_cached_values(self):
        entry = Entry(self.db, None, self.project_id)
        entry.notes = "Direkt"
        self.assertEqual(entry.notes, "Direkt")

    def test_project_id_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.project_id = "1"

    def test_entry_type_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.entry_type = "Arbeit"

    def test_is_active_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.is_active = 1

    def test_created_at_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.created_at = "2024-01-01"

    def test_edited_at_accepts_none(self):
        entry = Entry(self.db, None, self.project_id)
        entry.edited_at = None
        self.assertIsNone(entry.edited_at)

    def test_edited_at_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.edited_at = 123

    def test_entry_date_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.entry_date = "2024-01-01"

    def test_begin_at_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.begin_at = "08:00"

    def test_end_at_accepts_none(self):
        entry = Entry(self.db, None, self.project_id)
        entry.end_at = None
        self.assertIsNone(entry.end_at)

    def test_end_at_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.end_at = 123

    def test_notes_type_check(self):
        entry = Entry(self.db, None, self.project_id)
        with self.assertRaises(TypeError):
            entry.notes = 42

    def test_calculate_duration_with_end(self):
        entry = Entry(self.db, None, self.project_id,
                      begin_at=datetime(2024, 1, 1, 8, 0, 0),
                      end_at=datetime(2024, 1, 1, 12, 0, 0))
        self.assertEqual(entry.calculate_duration(entry.end_at), timedelta(hours=4))

    def test_calculate_duration_uses_now_when_open(self):
        """Without an explicit end, duration is measured against now."""
        begin = datetime.now() - timedelta(minutes=10)
        entry = Entry(self.db, None, self.project_id, begin_at=begin)
        duration = entry.calculate_duration()
        self.assertGreaterEqual(duration, timedelta(minutes=10))
        self.assertLess(duration, timedelta(minutes=11))

    def test_duration_with_end_at(self):
        entry = Entry(self.db, None, self.project_id,
                      begin_at=datetime(2024, 1, 1, 8, 0, 0),
                      end_at=datetime(2024, 1, 1, 16, 30, 0))
        self.assertEqual(entry.duration, timedelta(hours=8, minutes=30))

    def test_duration_is_stable_when_ended(self):
        entry = Entry(self.db, None, self.project_id,
                      begin_at=datetime(2024, 1, 1, 8, 0, 0),
                      end_at=datetime(2024, 1, 1, 9, 0, 0))
        self.assertEqual(entry.duration, entry.duration)

    def test_duration_open_entry_grows_with_time(self):
        begin = datetime.now() - timedelta(seconds=1)
        entry = Entry(self.db, None, self.project_id, begin_at=begin)
        first = entry.duration
        second = entry.calculate_duration(datetime.now() + timedelta(seconds=1))
        self.assertGreater(second, first)

    def test_duration_recomputed_after_end_at_change(self):
        """Changing end_at must invalidate the cached duration."""
        entry = Entry(self.db, None, self.project_id,
                      begin_at=datetime(2024, 1, 1, 8, 0, 0),
                      end_at=datetime(2024, 1, 1, 9, 0, 0))
        entry.end_at = datetime(2024, 1, 1, 10, 0, 0)
        self.assertEqual(entry.duration, timedelta(hours=2))

    def test_duration_recomputed_after_begin_at_change(self):
        """Changing begin_at must invalidate the cached duration."""
        entry = Entry(self.db, None, self.project_id,
                      begin_at=datetime(2024, 1, 1, 8, 0, 0),
                      end_at=datetime(2024, 1, 1, 9, 0, 0))
        entry.begin_at = datetime(2024, 1, 1, 7, 0, 0)
        entry.end_at = datetime(2024, 1, 1, 9, 0, 0)
        self.assertEqual(entry.duration, timedelta(hours=2))

    def test_is_active_persisted_and_unique(self):
        """is_active must persist and stay unique across the database."""
        from sqlite3 import IntegrityError
        entry = Entry(self.db, None, self.project_id, is_active=True)
        self.assertTrue(Entry(self.db, entry.id).is_active)
        with self.assertRaises(IntegrityError):
            Entry(self.db, None, self.project_id, is_active=True)


if __name__ == "__main__":
    unittest.main()
