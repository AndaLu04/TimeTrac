import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from constants import HourType, Tables
from data.database import Database, database_cursor
from data.entry import Entry
from data.project import Project
from logic.backup_service import BackupError, BackupService
from logic.settings_service import SettingsService


class TestSettingsService(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = SettingsService(self.db)

    def tearDown(self):
        self._tmp.cleanup()

    def test_defaults_without_values(self):
        self.assertEqual(self.service.get_language(), "de")
        self.assertIsNone(self.service.get_active_project_id())
        self.assertEqual(self.service.get_default_break_minutes(), 0)
        self.assertEqual(self.service.get_csv_delimiter(), ",")
        self.assertIsNone(self.service.get_dashboard_layout())

    def test_roundtrip_all_keys(self):
        self.service.set_language("en")
        self.service.set_active_project_id(3)
        self.service.set_default_break_minutes(30)
        self.service.set_csv_delimiter(";")
        self.service.set_dashboard_layout(["week", "month"])
        self.assertEqual(self.service.get_language(), "en")
        self.assertEqual(self.service.get_active_project_id(), 3)
        self.assertEqual(self.service.get_default_break_minutes(), 30)
        self.assertEqual(self.service.get_csv_delimiter(), ";")
        self.assertEqual(self.service.get_dashboard_layout(), ["week", "month"])

    def test_active_project_id_clearable(self):
        self.service.set_active_project_id(1)
        self.service.set_active_project_id(None)
        self.assertIsNone(self.service.get_active_project_id())

    def test_survives_service_recreation(self):
        self.service.set_csv_delimiter("|")
        fresh = SettingsService(self.db)
        self.assertEqual(fresh.get_csv_delimiter(), "|")


class TestBackupService(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = BackupService(self.db)
        project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)
        Entry(
            self.db,
            None,
            project.id,
            entry_date=date(2026, 11, 16),
            begin_at=datetime(2026, 11, 16, 8, 0),
            end_at=datetime(2026, 11, 16, 16, 0),
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_export_creates_copy(self):
        target = Path(self._tmp.name) / "backup.db"
        self.service.export_backup(target)
        self.assertTrue(target.exists())
        restored = Database(database_path=target)
        self.assertEqual(len(restored.get_all_project_ids()), 1)
        self.assertIsNotNone(self.service.settings.get_last_backup_at())

    def test_import_restores_entries(self):
        target = Path(self._tmp.name) / "backup.db"
        self.service.export_backup(target)
        fresh_db = Database(database_path=os.path.join(self._tmp.name, "fresh.db"))
        BackupService(fresh_db).import_backup(target)
        self.assertEqual(len(fresh_db.get_all_project_ids()), 1)
        self.assertEqual(len(fresh_db.get_entry_ids_from_project_id(1)), 1)

    def test_import_rejects_invalid_file(self):
        bogus = Path(self._tmp.name) / "bogus.db"
        bogus.write_text("keine datenbank")
        with self.assertRaises(BackupError):
            self.service.import_backup(bogus)

    def test_failed_import_leaves_live_database_intact(self):
        """Bei Ablehnung bleibt die Live-DB vollständig erhalten."""
        bogus = Path(self._tmp.name) / "bogus.db"
        bogus.write_text("keine datenbank")
        with self.assertRaises(BackupError):
            self.service.import_backup(bogus)
        live = Database(database_path=self.db_path)
        self.assertEqual(len(live.get_all_project_ids()), 1)
        self.assertEqual(len(live.get_entry_ids_from_project_id(1)), 1)

    def test_import_migrates_old_schema_backup(self):
        """Backups im Altschema werden beim Import migriert (Staging-Phase)."""
        from tests.test_migrations import _legacy_database_path

        legacy = Path(_legacy_database_path(self._tmp.name))
        self.service.import_backup(legacy)
        restored = Database(database_path=self.db_path)
        self.assertEqual(restored.get_all_project_ids(), [1])
        self.assertEqual(restored.get(Tables.projects, 1, "workdays"), "[0,1,2,3,4]")
        self.assertTrue(Database.is_valid_database(Path(self.db_path)))
        with database_cursor(self.db_path) as cursor:
            cursor.execute("PRAGMA table_info(entries)")
            entry_columns = {row[1] for row in cursor.fetchall()}
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
            )
            settings_table = cursor.fetchone()
        self.assertTrue(
            {"break_minutes", "project_label", "counts_as_work", "deleted_at"}
            <= entry_columns
        )
        self.assertIsNotNone(settings_table)

    def test_import_leaves_no_staging_file(self):
        target = Path(self._tmp.name) / "backup.db"
        self.service.export_backup(target)
        self.service.import_backup(target)
        leftovers = [
            p for p in Path(self._tmp.name).iterdir() if p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [])

    def test_import_rejects_missing_file(self):
        with self.assertRaises(BackupError):
            self.service.import_backup(Path(self._tmp.name) / "gibt-es-nicht.db")

    def test_backup_restore_integrity(self):
        """Export und Re-Import ergeben identischen Datenbestand."""
        target = Path(self._tmp.name) / "backup.db"
        self.service.export_backup(target)
        other = Path(self._tmp.name) / "other.db"
        Database(database_path=other)
        BackupService(Database(database_path=other)).import_backup(target)
        reloaded = Database(database_path=other)
        self.assertEqual(reloaded.get_all_project_ids(), self.db.get_all_project_ids())
        self.assertEqual(
            reloaded.get_entry_ids_from_project_id(1),
            self.db.get_entry_ids_from_project_id(1),
        )
