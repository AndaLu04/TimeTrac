import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from constants import EntryType, HourType
from data.database import Database
from data.entry import Entry
from data.project import Project


class TestDatabaseQueries(unittest.TestCase):
    """Neue Abfrage-Schnittstellen des Data-Layers für den Logic-Layer (#19)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)

    def tearDown(self):
        self._tmp.cleanup()

    def _add_entry(
        self, day, entry_type=EntryType.ARBEIT, is_active=False, deleted=False
    ):
        entry = Entry(
            self.db,
            None,
            self.project.id,
            entry_type=entry_type,
            is_active=is_active,
            entry_date=day,
            begin_at=datetime.combine(day, datetime.min.time()).replace(hour=8),
        )
        if deleted:
            entry.deleted_at = datetime.now()
        return entry

    def test_get_active_entry_id(self):
        self.assertIsNone(self.db.get_active_entry_id())
        day = date(2026, 11, 16)
        entry = self._add_entry(day, is_active=True)
        self.assertEqual(self.db.get_active_entry_id(), entry.id)
        entry.is_active = False
        self.assertIsNone(self.db.get_active_entry_id())

    def test_get_active_entry_id_ignores_deleted(self):
        self._add_entry(date(2026, 11, 16), is_active=True, deleted=True)
        self.assertIsNone(self.db.get_active_entry_id())

    def test_get_entry_ids_between_dates(self):
        self._add_entry(date(2026, 11, 16))
        self._add_entry(date(2026, 11, 17))
        self._add_entry(date(2026, 11, 20))
        ids = self.db.get_entry_ids_between_dates(
            self.project.id, date(2026, 11, 16), date(2026, 11, 17)
        )
        self.assertEqual(len(ids), 2)

    def test_get_entry_ids_between_dates_ignores_deleted(self):
        self._add_entry(date(2026, 11, 16), deleted=True)
        self._add_entry(date(2026, 11, 17))
        ids = self.db.get_entry_ids_between_dates(
            self.project.id, date(2026, 11, 16), date(2026, 11, 17)
        )
        self.assertEqual(len(ids), 1)

    def test_get_first_entry_date(self):
        self.assertIsNone(self.db.get_first_entry_date(self.project.id))
        self._add_entry(date(2026, 11, 17))
        first = self._add_entry(date(2026, 11, 16))
        self.assertEqual(
            self.db.get_first_entry_date(self.project.id), date(2026, 11, 16)
        )
        first.deleted_at = datetime.now()
        self.assertEqual(
            self.db.get_first_entry_date(self.project.id), date(2026, 11, 17)
        )

    def test_entry_exists(self):
        day = date(2026, 10, 31)
        self.assertFalse(self.db.entry_exists(self.project.id, EntryType.FEIERTAG, day))
        Entry(
            self.db,
            None,
            self.project.id,
            entry_type=EntryType.FEIERTAG,
            entry_date=day,
        )
        self.assertTrue(self.db.entry_exists(self.project.id, EntryType.FEIERTAG, day))
        self.assertFalse(self.db.entry_exists(self.project.id, EntryType.URLAUB, day))

    def test_entry_exists_ignores_deleted(self):
        day = date(2026, 10, 31)
        entry = Entry(
            self.db,
            None,
            self.project.id,
            entry_type=EntryType.FEIERTAG,
            entry_date=day,
        )
        entry.deleted_at = datetime.now()
        self.assertFalse(self.db.entry_exists(self.project.id, EntryType.FEIERTAG, day))

    def test_is_valid_database_accepts_timetrac_db(self):
        self.assertTrue(Database.is_valid_database(Path(self.db_path)))

    def test_is_valid_database_rejects_garbage(self):
        bogus = Path(self._tmp.name) / "bogus.db"
        bogus.write_text("keine datenbank")
        self.assertFalse(Database.is_valid_database(bogus))

    def test_is_valid_database_rejects_missing_file(self):
        self.assertFalse(
            Database.is_valid_database(Path(self._tmp.name) / "gibt-es-nicht.db")
        )
