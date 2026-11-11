import os
import tempfile
import unittest
from datetime import date, datetime

from constants import HourType
from data.database import Database
from data.entry import Entry
from data.project import Project
from logic.export_service import ExportService


class TestExportService(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)
        self.service = ExportService(self.db)
        self.project = Project(self.db, None, "Gemeinde", 40, HourType.WEEKLY)

    def tearDown(self):
        self._tmp.cleanup()

    def _add_entry(self, day, begin, end, notes=None, break_minutes=0, project=None):
        entry = Entry(
            self.db,
            None,
            (project or self.project).id,
            entry_date=day,
            begin_at=datetime.combine(day, begin),
            end_at=datetime.combine(day, end),
        )
        entry.break_minutes = break_minutes
        if notes:
            entry.notes = notes
        return entry

    def test_header_and_row_content(self):
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=16),
        )
        csv = self.service.export_csv(self.project, day, day)
        lines = csv.strip().split("\n")
        self.assertEqual(lines[0], "Datum,Beginn,Ende,Pause,Typ,Projekt,Notiz,Dauer")
        self.assertEqual(
            lines[1],
            '2026-11-16,08:00,16:00,0,Arbeit,Gemeinde,,"8,00"',
        )

    def test_custom_delimiter(self):
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=16),
        )
        csv = self.service.export_csv(self.project, day, day, delimiter=";")
        self.assertIn("2026-11-16;08:00;16:00", csv)

    def test_decimal_separator_english(self):
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=16).replace(minute=30),
        )
        csv = self.service.export_csv(self.project, day, day, decimal_separator=".")
        self.assertIn("8.50", csv)

    def test_notes_with_delimiter_are_quoted(self):
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
            notes="a,b",
        )
        csv = self.service.export_csv(self.project, day, day)
        self.assertIn('"a,b"', csv)

    def test_empty_period_yields_only_header(self):
        csv = self.service.export_csv(
            self.project, date(2026, 11, 16), date(2026, 11, 22)
        )
        self.assertEqual(len(csv.strip().split("\n")), 1)

    def test_deleted_entries_are_excluded(self):
        day = date(2026, 11, 16)
        entry = self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
        )
        entry.deleted_at = datetime.now()
        csv = self.service.export_csv(self.project, day, day)
        self.assertEqual(len(csv.strip().split("\n")), 1)

    def test_range_filters_by_entry_date(self):
        day = date(2026, 11, 16)
        other = date(2026, 11, 20)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
        )
        self._add_entry(
            other,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
        )
        csv = self.service.export_csv(self.project, day, day)
        self.assertEqual(len(csv.strip().split("\n")), 2)

    def test_formula_leading_text_is_neutralized(self):
        """Werte mit führendem =, +, -, @ werden mit ' maskiert (Formelinjektion)."""
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
            notes="=BÖSEWICHT()",
        )
        csv = self.service.export_csv(self.project, day, day)
        self.assertIn("'=BÖSEWICHT()", csv)

    def test_normal_notes_are_unchanged(self):
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
            notes="Jugendgruppe",
        )
        csv = self.service.export_csv(self.project, day, day)
        self.assertIn("Jugendgruppe", csv)
        self.assertNotIn("'Jugendgruppe", csv)

    def test_numeric_columns_stay_unchanged(self):
        """Numerische Spalten (Pause, Dauer) werden nicht maskiert."""
        day = date(2026, 11, 16)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=16),
            break_minutes=30,
        )
        csv = self.service.export_csv(self.project, day, day)
        data_row = csv.strip().split("\n")[1]
        self.assertIn(",30,Arbeit,", data_row)
        self.assertIn('"8,00"', data_row)
        self.assertNotIn("'30", data_row)
        self.assertNotIn("'8,00", data_row)

    def test_formula_leading_project_name_is_neutralized(self):
        """Auch ein Projektname mit führendem = wird maskiert."""
        day = date(2026, 11, 16)
        project = Project(self.db, None, '=HYPERLINK("böse")', 8, HourType.DAILY)
        self._add_entry(
            day,
            datetime.min.time().replace(hour=8),
            datetime.min.time().replace(hour=9),
            project=project,
        )
        csv = self.service.export_csv(project, day, day)
        self.assertIn("'=HYPERLINK", csv)

    def test_all_formula_prefixes_are_neutralized(self):
        """Notizen mit führendem =, +, -, @ werden jeweils mit ' maskiert."""
        day = date(2026, 11, 16)
        for index, note in enumerate(("=A()", "+B()", "-C()", "@D()")):
            with self.subTest(note=note):
                project = Project(self.db, None, f"P{index}", 8, HourType.DAILY)
                self._add_entry(
                    day,
                    datetime.min.time().replace(hour=8),
                    datetime.min.time().replace(hour=9),
                    notes=note,
                    project=project,
                )
                csv = self.service.export_csv(project, day, day)
                self.assertIn(f"'{note}", csv)
                self.assertNotIn(f",{note},", csv)

    def test_midnight_span_exported_on_entry_date(self):
        day = date(2026, 11, 16)
        Entry(
            self.db,
            None,
            self.project.id,
            entry_date=day,
            begin_at=datetime(2026, 11, 16, 22, 0),
            end_at=datetime(2026, 11, 17, 6, 0),
        )
        csv = self.service.export_csv(self.project, day, day)
        self.assertIn("8,00", csv)
