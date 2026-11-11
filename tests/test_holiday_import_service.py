import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from constants import EntryType, HourType
from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.holiday_import_service import HolidayImportService

ICS_CONTENT = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Reformationstag
DTSTART;VALUE=DATE:20261031
END:VEVENT
BEGIN:VEVENT
SUMMARY:1. Weihnachtstag
DTSTART;VALUE=DATE:20261225
END:VEVENT
BEGIN:VEVENT
SUMMARY:Neujahr 2027
DTSTART;VALUE=DATE:20270101
END:VEVENT
END:VCALENDAR
"""


class TestHolidayImportService(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = HolidayImportService(self.db)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)
        self.ics_path = Path(self._tmp.name) / "feiertage.ics"
        self.ics_path.write_text(ICS_CONTENT, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_import_creates_feiertag_entries(self):
        created = self.service.import_ics(self.ics_path, self.project)
        self.assertEqual(len(created), 3)
        self.assertTrue(
            all(entry.entry_type == EntryType.FEIERTAG for entry in created)
        )
        self.assertEqual(created[0].entry_date, date(2026, 10, 31))
        self.assertEqual(created[0].notes, "Reformationstag")

    def test_year_filter(self):
        created = self.service.import_ics(self.ics_path, self.project, year=2026)
        self.assertEqual(len(created), 2)
        self.assertTrue(all(entry.entry_date.year == 2026 for entry in created))

    def test_second_import_skips_duplicates(self):
        self.service.import_ics(self.ics_path, self.project)
        created_again = self.service.import_ics(self.ics_path, self.project)
        self.assertEqual(created_again, [])

    def test_manual_feiertag_blocks_import_for_same_day(self):
        Entry(
            self.db,
            None,
            self.project.id,
            entry_type=EntryType.FEIERTAG,
            entry_date=date(2026, 10, 31),
        )
        created = self.service.import_ics(self.ics_path, self.project)
        self.assertEqual(len(created), 2)
        self.assertNotIn(date(2026, 10, 31), [entry.entry_date for entry in created])

    def test_deleted_feiertag_does_not_block_import(self):
        entry = Entry(
            self.db,
            None,
            self.project.id,
            entry_type=EntryType.FEIERTAG,
            entry_date=date(2026, 10, 31),
        )
        entry.deleted_at = entry.begin_at
        created = self.service.import_ics(self.ics_path, self.project)
        self.assertEqual(len(created), 3)

    def test_invalid_dtstart_is_skipped(self):
        """Ungültige DTSTART-Werte überspringen das Event, brechen den Import nicht ab."""
        broken = Path(self._tmp.name) / "broken.ics"
        broken.write_text(
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "SUMMARY:Kaputtes Datum\n"
            "DTSTART;VALUE=DATE:20261340\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "SUMMARY:Reformationstag\n"
            "DTSTART;VALUE=DATE:20261031\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n",
            encoding="utf-8",
        )
        created = self.service.import_ics(broken, self.project)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].entry_date, date(2026, 10, 31))

    def test_non_digit_dtstart_is_skipped(self):
        broken = Path(self._tmp.name) / "broken2.ics"
        broken.write_text(
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "SUMMARY:Kein Datum\n"
            "DTSTART;VALUE=DATE:heute\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n",
            encoding="utf-8",
        )
        created = self.service.import_ics(broken, self.project)
        self.assertEqual(created, [])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.service.import_ics(
                Path(self._tmp.name) / "gibt-es-nicht.ics", self.project
            )
