import unittest

from constants import HourType, Tables
from data.database import Database
from data.project import Project


class TestProject(unittest.TestCase):
    """Tests Project persistence, lazy loading and type validation.

    Each test uses its own temporary database file.
    """

    def setUp(self):
        import os
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_project_is_persisted(self):
        project = Project(self.db, None, "Jugendarbeit", 20.0, HourType.WEEKLY, False)
        self.assertIn(project.id, self.db.get_all_project_ids())
        self.assertEqual(self.db.get(Tables.projects, project.id, "name"), "Jugendarbeit")
        self.assertEqual(self.db.get(Tables.projects, project.id, "target_hours"), 20.0)
        self.assertEqual(self.db.get(Tables.projects, project.id, "hour_type"), HourType.WEEKLY)
        self.assertEqual(self.db.get(Tables.projects, project.id, "is_default"), False)

    def test_new_project_defaults(self):
        project = Project(self.db, None, "Standard")
        self.assertEqual(project.target_hours, 0)
        self.assertEqual(project.hour_type, HourType.WEEKLY)
        self.assertEqual(project.is_default, False)

    def test_load_existing_project_lazily(self):
        """Loading by ID must fetch all fields lazily from the database."""
        created = Project(self.db, None, "Büroarbeit", 15.0, HourType.DAILY, True)
        loaded = Project(self.db, created.id)
        self.assertEqual(loaded.name, "Büroarbeit")
        self.assertEqual(loaded.target_hours, 15.0)
        self.assertEqual(loaded.hour_type, HourType.DAILY)
        self.assertEqual(loaded.is_default, True)

    def test_setters_persist_changes(self):
        project = Project(self.db, None, "Alt", 10.0, HourType.WEEKLY, False)
        project.name = "Neu"
        project.target_hours = 25.5
        project.hour_type = HourType.MONTHLY
        project.is_default = True
        reloaded = Project(self.db, project.id)
        self.assertEqual(reloaded.name, "Neu")
        self.assertEqual(reloaded.target_hours, 25.5)
        self.assertEqual(reloaded.hour_type, HourType.MONTHLY)
        self.assertEqual(reloaded.is_default, True)

    def test_setters_update_cached_values(self):
        project = Project(self.db, None, "Cache", 10.0, HourType.WEEKLY, False)
        project.name = "Direkt"
        self.assertEqual(project.name, "Direkt")

    def test_name_type_check(self):
        project = Project(self.db, None, "Projekt")
        with self.assertRaises(TypeError):
            project.name = 42

    def test_target_hours_type_check(self):
        project = Project(self.db, None, "Projekt")
        with self.assertRaises(TypeError):
            project.target_hours = "20"

    def test_target_hours_accepts_int(self):
        project = Project(self.db, None, "Projekt")
        project.target_hours = 20
        self.assertEqual(project.target_hours, 20)

    def test_hour_type_type_check(self):
        project = Project(self.db, None, "Projekt")
        with self.assertRaises(TypeError):
            project.hour_type = "Weekly"

    def test_is_default_type_check(self):
        project = Project(self.db, None, "Projekt")
        with self.assertRaises(TypeError):
            project.is_default = "yes"

    def test_entry_list_empty_for_new_project(self):
        project = Project(self.db, None, "Ohne Einträge")
        self.assertEqual(project.entry_list, [])

    def test_entry_list_returns_project_entries(self):
        from data.entry import Entry
        project = Project(self.db, None, "Mit Einträgen")
        Entry(self.db, None, project.id)
        Entry(self.db, None, project.id)
        other = Project(self.db, None, "Anderes Projekt")
        Entry(self.db, None, other.id)
        entries = project.entry_list
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(entry.project_id == project.id for entry in entries))

    def test_load_entries_discards_cache(self):
        """load_entries must bypass the cached entry list."""
        from data.entry import Entry
        project = Project(self.db, None, "Cache-Test")
        self.assertEqual(project.entry_list, [])
        Entry(self.db, None, project.id)
        self.assertEqual(project.entry_list, [])
        entries = project.load_entries()
        self.assertEqual(len(entries), 1)


if __name__ == "__main__":
    unittest.main()
