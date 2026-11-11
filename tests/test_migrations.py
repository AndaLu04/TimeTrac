import os
import tempfile
import unittest

from constants import EntryType, Tables
from data.database import Database, database_cursor
from data.entry import Entry
from data.project import Project
from data.settings import SettingsRepository
from data.sync.sync_backend import SyncBackend


class TestFreshSchema(unittest.TestCase):
    """Neue Spalten liegen direkt im CREATE-TABLE-Layout (keine Migration, pre-v1)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_projects_schema_contains_new_columns(self):
        with database_cursor(self.db_path) as cursor:
            cursor.execute("PRAGMA table_info(projects)")
            columns = {row[1] for row in cursor.fetchall()}
        self.assertTrue(
            {"workdays", "daily_hours_override", "is_active", "notes"} <= columns
        )

    def test_entries_schema_contains_new_columns(self):
        with database_cursor(self.db_path) as cursor:
            cursor.execute("PRAGMA table_info(entries)")
            columns = {row[1] for row in cursor.fetchall()}
        self.assertTrue(
            {"break_minutes", "project_label", "counts_as_work", "deleted_at"}
            <= columns
        )

    def test_settings_table_exists(self):
        with database_cursor(self.db_path) as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
            )
            self.assertIsNotNone(cursor.fetchone())

    def test_defaults_are_applied(self):
        project = Project(self.db, None, "Standard", 40)
        self.assertEqual(
            self.db.get(Tables.projects, project.id, "workdays"), "[0,1,2,3,4]"
        )
        self.assertEqual(self.db.get(Tables.projects, project.id, "is_active"), True)
        entry = Entry(self.db, None, project.id)
        self.assertEqual(self.db.get(Tables.entries, entry.id, "break_minutes"), 0)
        self.assertIsNone(self.db.get(Tables.entries, entry.id, "deleted_at"))


class TestSettingsRepository(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.repo = SettingsRepository(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_set_get_roundtrip(self):
        self.repo.set("language", "de")
        self.assertEqual(self.repo.get("language"), "de")
        self.repo.set("csv_delimiter", ";")
        self.assertEqual(self.repo.get("csv_delimiter"), ";")

    def test_get_returns_default_for_missing_key(self):
        self.assertIsNone(self.repo.get("missing"))
        self.assertEqual(self.repo.get("missing", "fallback"), "fallback")

    def test_set_overwrites_existing_value(self):
        self.repo.set("language", "de")
        self.repo.set("language", "en")
        self.assertEqual(self.repo.get("language"), "en")

    def test_delete_removes_key(self):
        self.repo.set("language", "de")
        self.repo.delete("language")
        self.assertIsNone(self.repo.get("language"))

    def test_keys_lists_all_keys(self):
        self.repo.set("language", "de")
        self.repo.set("active_project_id", "1")
        self.assertEqual(self.repo.keys(), ["active_project_id", "language"])


class TestExtendedColumns(unittest.TestCase):
    """Neue Spalten über die Active-Records Entry und Project."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_entry_new_columns_roundtrip(self):
        from datetime import date, datetime

        project = Project(self.db, None, "Projekt", 20)
        entry = Entry(
            self.db,
            None,
            project.id,
            entry_date=date(2026, 3, 30),
            begin_at=datetime(2026, 3, 30, 8, 0),
        )
        entry.break_minutes = 30
        entry.project_label = "Jugendgruppe"
        entry.counts_as_work = True
        reloaded = Entry(self.db, entry.id)
        self.assertEqual(reloaded.break_minutes, 30)
        self.assertEqual(reloaded.project_label, "Jugendgruppe")
        self.assertTrue(reloaded.counts_as_work)
        self.assertIsNone(reloaded.deleted_at)

    def test_project_new_columns_roundtrip(self):
        project = Project(self.db, None, "Pastor", 40)
        project.workdays = {1, 2, 3, 4, 5}
        project.daily_hours_override = {1: 6.0, 2: 8.0}
        project.is_active = False
        project.notes = "Di-Sa"
        reloaded = Project(self.db, project.id)
        self.assertEqual(reloaded.workdays, {1, 2, 3, 4, 5})
        self.assertEqual(reloaded.daily_hours_override, {1: 6.0, 2: 8.0})
        self.assertFalse(reloaded.is_active)
        self.assertEqual(reloaded.notes, "Di-Sa")

    def test_daily_hours_override_normalizes_string_keys(self):
        """Schlüssel werden zu int normalisiert; Cache und DB nutzen dieselbe Form."""
        project = Project(self.db, None, "Test", 8)
        project.daily_hours_override = {"1": 6.0, 2: 8.0}
        self.assertEqual(project.daily_hours_override, {1: 6.0, 2: 8.0})
        reloaded = Project(self.db, project.id)
        self.assertEqual(reloaded.daily_hours_override, {1: 6.0, 2: 8.0})

    def test_daily_hours_override_rejects_invalid_weekday(self):
        project = Project(self.db, None, "Test", 8)
        with self.assertRaises(TypeError):
            project.daily_hours_override = {9: 6.0}
        with self.assertRaises(TypeError):
            project.daily_hours_override = {"montag": 6.0}
        with self.assertRaises(TypeError):
            project.daily_hours_override = {True: 6.0}

    def test_workdays_rejects_invalid_weekday(self):
        project = Project(self.db, None, "Test", 40)
        with self.assertRaises(TypeError):
            project.workdays = {9}

    def test_workdays_rejects_empty_collection(self):
        project = Project(self.db, None, "Test", 40)
        with self.assertRaises(TypeError):
            project.workdays = set()

    def test_workdays_rejects_bool_values(self):
        project = Project(self.db, None, "Test", 40)
        with self.assertRaises(TypeError):
            project.workdays = {True, 2}

    def test_workdays_cache_is_a_set(self):
        project = Project(self.db, None, "Test", 40)
        project.workdays = [1, 2, 3]
        self.assertIsInstance(project._workdays, set)
        self.assertEqual(project.workdays, {1, 2, 3})

    def test_new_entry_types_exist(self):
        self.assertEqual(EntryType.ELTERNZEIT, "Elternzeit")
        self.assertEqual(EntryType.UEBERSTUNDENAUSGLEICH, "Überstundenausgleich")
        self.assertEqual(EntryType.SONSTIGES, "Sonstiges")


class TestSyncBackendStub(unittest.TestCase):

    def test_sync_backend_is_abstract(self):
        with self.assertRaises(TypeError):
            SyncBackend()

    def test_concrete_backend_can_implement(self):
        class Dummy(SyncBackend):
            def push(self):
                pass

            def pull(self):
                pass

        Dummy()
