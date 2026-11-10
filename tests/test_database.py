import unittest
from datetime import date, datetime, timedelta

from constants import ALLOWED_COLUMNS, DATABASE, EntryType, HourType, Tables
from data.database import Database, database_cursor, init_sqlite_converters_and_adapters


class TestConstants(unittest.TestCase):
    def test_entry_type_values(self):
        self.assertEqual(EntryType.ARBEIT, "Arbeit")
        self.assertEqual(EntryType.KRANKHEIT, "Krankheit")
        self.assertEqual(EntryType.URLAUB, "Urlaub")
        self.assertEqual(EntryType.FEIERTAG, "Feiertag")
        self.assertEqual(EntryType.PLATZHALTER, "Platzhalter")

    def test_hour_type_values(self):
        self.assertEqual(HourType.ALLTIME, "Alltime")
        self.assertEqual(HourType.MONTHLY, "Monthly")
        self.assertEqual(HourType.WEEKLY, "Weekly")
        self.assertEqual(HourType.DAILY, "Daily")

    def test_tables_enum(self):
        self.assertEqual(Tables.projects.name, "projects")
        self.assertEqual(Tables.entries.name, "entries")

    def test_allowed_columns_cover_schema(self):
        self.assertEqual(
            ALLOWED_COLUMNS[Tables.projects],
            {"name", "target_hours", "hour_type", "is_default"},
        )
        self.assertEqual(
            ALLOWED_COLUMNS[Tables.entries],
            {"project_id", "entry_type", "is_active", "created_at", "edited_at",
             "entry_date", "begin_at", "end_at", "notes"},
        )


class TestDatabaseBasics(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def _insert_project(self, db, name="Projekt", target_hours=20.0,
                        hour_type=HourType.WEEKLY, is_default=False):
        return db.insert_new_row(
            content={"name": name, "target_hours": target_hours,
                     "hour_type": hour_type, "is_default": is_default},
            table=Tables.projects,
        )

    def _insert_entry(self, db, project_id, **overrides):
        content = {
            "project_id": project_id,
            "entry_type": EntryType.ARBEIT,
            "is_active": False,
            "created_at": datetime(2024, 1, 1, 8, 0, 0),
            "edited_at": None,
            "entry_date": date(2024, 1, 1),
            "begin_at": datetime(2024, 1, 1, 8, 0, 0),
            "end_at": datetime(2024, 1, 1, 12, 0, 0),
            "notes": None,
        }
        content.update(overrides)
        return db.insert_new_row(content=content, table=Tables.entries)

    def test_tables_created(self):
        with database_cursor(self.db_path) as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            names = {row[0] for row in cursor.fetchall()}
        self.assertIn("projects", names)
        self.assertIn("entries", names)

    def test_database_default_path_constant(self):
        self.assertTrue(DATABASE.name.endswith("database.db"))

    def test_insert_and_get_project(self):
        row_id = self._insert_project(self.db, name="Gottesdienst")
        self.assertEqual(self.db.get(Tables.projects, row_id, "name"), "Gottesdienst")
        self.assertEqual(self.db.get(Tables.projects, row_id, "target_hours"), 20.0)
        self.assertEqual(self.db.get(Tables.projects, row_id, "hour_type"), HourType.WEEKLY)

    def test_insert_returns_increasing_ids(self):
        first = self._insert_project(self.db, name="A")
        second = self._insert_project(self.db, name="B")
        self.assertEqual(second, first + 1)

    def test_set_updates_field(self):
        row_id = self._insert_project(self.db, name="Alt")
        self.db.set(Tables.projects, row_id, "name", "Neu")
        self.assertEqual(self.db.get(Tables.projects, row_id, "name"), "Neu")

    def test_set_invalid_column_raises(self):
        row_id = self._insert_project(self.db)
        with self.assertRaises(ValueError):
            self.db.set(Tables.projects, row_id, "not_a_column", 1)

    def test_get_invalid_column_raises(self):
        row_id = self._insert_project(self.db)
        with self.assertRaises(ValueError):
            self.db.get(Tables.projects, row_id, "not_a_column")

    def test_insert_invalid_column_raises(self):
        with self.assertRaises(ValueError):
            self.db.insert_new_row(content={"unknown": 1}, table=Tables.projects)

    def test_get_all_project_ids(self):
        self.assertEqual(self.db.get_all_project_ids(), [])
        first = self._insert_project(self.db, name="A")
        second = self._insert_project(self.db, name="B")
        self.assertEqual(self.db.get_all_project_ids(), [first, second])

    def test_get_entry_ids_from_project_id(self):
        project_a = self._insert_project(self.db, name="A")
        project_b = self._insert_project(self.db, name="B")
        entry_a1 = self._insert_entry(self.db, project_a)
        entry_a2 = self._insert_entry(self.db, project_a)
        entry_b1 = self._insert_entry(self.db, project_b)
        self.assertEqual(self.db.get_entry_ids_from_project_id(project_a), [entry_a1, entry_a2])
        self.assertEqual(self.db.get_entry_ids_from_project_id(project_b), [entry_b1])
        self.assertEqual(self.db.get_entry_ids_from_project_id(999), [])

    def test_foreign_key_enforced(self):
        from sqlite3 import IntegrityError
        with self.assertRaises(IntegrityError):
            self._insert_entry(self.db, project_id=999)

    def test_only_one_active_entry_allowed(self):
        from sqlite3 import IntegrityError
        project = self._insert_project(self.db)
        self._insert_entry(self.db, project, is_active=True)
        with self.assertRaises(IntegrityError):
            self._insert_entry(self.db, project, is_active=True)

    def test_inactive_entries_not_restricted(self):
        project = self._insert_project(self.db)
        self._insert_entry(self.db, project, is_active=False)
        self._insert_entry(self.db, project, is_active=False)
        self.assertEqual(len(self.db.get_entry_ids_from_project_id(project)), 2)

    def test_date_time_and_enum_roundtrip(self):
        project = self._insert_project(self.db)
        entry_id = self._insert_entry(self.db, project)
        self.assertEqual(self.db.get(Tables.entries, entry_id, "created_at"),
                         datetime(2024, 1, 1, 8, 0, 0))
        self.assertEqual(self.db.get(Tables.entries, entry_id, "entry_date"),
                         date(2024, 1, 1))
        self.assertEqual(self.db.get(Tables.entries, entry_id, "entry_type"),
                         EntryType.ARBEIT)

    def test_edited_at_roundtrip(self):
        project = self._insert_project(self.db)
        entry_id = self._insert_entry(self.db, project,
                                       edited_at=datetime(2024, 1, 2, 9, 30, 0))
        self.assertEqual(self.db.get(Tables.entries, entry_id, "edited_at"),
                         datetime(2024, 1, 2, 9, 30, 0))

    def test_init_converters_idempotent(self):
        init_sqlite_converters_and_adapters()
        init_sqlite_converters_and_adapters()
        project = self._insert_project(self.db)
        entry_id = self._insert_entry(self.db, project)
        self.assertEqual(self.db.get(Tables.entries, entry_id, "entry_type"),
                         EntryType.ARBEIT)

    def test_database_reopened_keeps_data(self):
        row_id = self._insert_project(self.db, name="Persistiert")
        reopened = Database(database_path=self.db_path)
        self.assertEqual(reopened.get(Tables.projects, row_id, "name"), "Persistiert")

    def test_duration_across_connections(self):
        project = self._insert_project(self.db)
        entry_id = self._insert_entry(self.db, project)
        with database_cursor(self.db_path) as cursor:
            cursor.execute("SELECT begin_at, end_at FROM entries WHERE id=?", (entry_id,))
            begin_at, end_at = cursor.fetchone()
        self.assertEqual(end_at - begin_at, timedelta(hours=4))


if __name__ == "__main__":
    unittest.main()
