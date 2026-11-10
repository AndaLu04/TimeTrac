import os
import tempfile
import unittest
from datetime import date

from constants import HourType
from data.database import Database
from data.project import Project
from logic.working_time_model import (AllTimeModel, DailyModel, MonthlyModel,
                                      WeeklyModel, get_working_time_model)


class ModelTestBase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmp.name, "test.db")
        self.db = Database(database_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def make_project(self, hour_type, target_hours, workdays=None, override=None):
        project = Project(self.db, None, "Projekt", target_hours, hour_type)
        if workdays is not None:
            project.workdays = workdays
        if override is not None:
            project.daily_hours_override = override
        return project


class TestWeeklyModel(ModelTestBase):

    def test_day_distributes_over_workdays(self):
        model = WeeklyModel(self.make_project(HourType.WEEKLY, 40))
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 16)), 8.0)  # Montag
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 22)), 0.0)  # Sonntag

    def test_week_equals_target(self):
        model = WeeklyModel(self.make_project(HourType.WEEKLY, 40))
        self.assertEqual(model.target_hours_for_week(2026, 47), 40.0)

    def test_month_sums_days(self):
        model = WeeklyModel(self.make_project(HourType.WEEKLY, 40))
        self.assertEqual(model.target_hours_for_month(2026, 11), 168.0)  # 21 Werktage

    def test_weekend_project_tuesday_to_saturday(self):
        project = self.make_project(HourType.WEEKLY, 40, workdays={1, 2, 3, 4, 5})
        model = WeeklyModel(project)
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 16)), 0.0)  # Montag
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 21)), 8.0)  # Samstag

    def test_week_spanning_two_months(self):
        """Grenzfall: ISO-Woche über Monatswechsel (KW 48: 23.-29.11.)."""
        model = WeeklyModel(self.make_project(HourType.WEEKLY, 40))
        self.assertEqual(model.target_hours_for_week(2026, 48), 40.0)

    def test_total_since(self):
        model = WeeklyModel(self.make_project(HourType.WEEKLY, 40))
        self.assertEqual(
            model.target_hours_total(date.today()), 8.0
        )  # heute ist ein Arbeitstag


class TestDailyModel(ModelTestBase):

    def test_day_equals_target(self):
        model = DailyModel(self.make_project(HourType.DAILY, 8))
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 16)), 8.0)
        self.assertEqual(model.target_hours_for_day(date(2026, 11, 22)), 0.0)

    def test_override_single_weekday(self):
        project = self.make_project(HourType.DAILY, 8, override={1: 6.0})
        model = DailyModel(project)
        self.assertEqual(
            model.target_hours_for_day(date(2026, 11, 17)), 6.0
        )  # Dienstag
        self.assertEqual(
            model.target_hours_for_day(date(2026, 11, 18)), 8.0
        )  # Mittwoch

    def test_week_sums_days(self):
        project = self.make_project(
            HourType.DAILY, 8, workdays={1, 2}, override={1: 6.0}
        )
        model = DailyModel(project)
        self.assertEqual(model.target_hours_for_week(2026, 47), 14.0)

    def test_month_sums_days(self):
        model = DailyModel(self.make_project(HourType.DAILY, 8, workdays={1, 2}))
        self.assertEqual(model.target_hours_for_month(2026, 11), 64.0)  # 4x Di + 4x Mi


class TestMonthlyModel(ModelTestBase):

    def test_month_equals_target(self):
        model = MonthlyModel(self.make_project(HourType.MONTHLY, 20))
        self.assertEqual(model.target_hours_for_month(2026, 11), 20.0)

    def test_week_is_proportional_share(self):
        model = MonthlyModel(self.make_project(HourType.MONTHLY, 20))
        week = model.target_hours_for_week(2026, 47)  # 16.-22.11., 5 Arbeitstage
        self.assertAlmostEqual(week, 20.0 * 5 / 21, places=6)

    def test_day_is_uniform_share(self):
        model = MonthlyModel(self.make_project(HourType.MONTHLY, 20))
        self.assertAlmostEqual(
            model.target_hours_for_day(date(2026, 11, 16)), 20.0 / 21, places=6
        )

    def test_week_at_month_boundary_uses_thursday_month(self):
        """Grenzfall: Woche am Monatswechsel zählt zum Monat des Donnerstags."""
        model = MonthlyModel(self.make_project(HourType.MONTHLY, 20))
        week = model.target_hours_for_week(
            2026, 49
        )  # 30.11.-06.12., Donnerstag im Dezember
        workdays_december = 23
        workdays_in_week = 5
        self.assertAlmostEqual(
            week, 20.0 * workdays_in_week / workdays_december, places=6
        )

    def test_total_since_sums_months(self):
        model = MonthlyModel(self.make_project(HourType.MONTHLY, 20))
        self.assertEqual(model.target_hours_total(date(2026, 11, 1)), 20.0)


class TestAllTimeModel(ModelTestBase):

    def test_total_equals_target(self):
        project = self.make_project(HourType.ALLTIME, 300)
        model = AllTimeModel(project, self.db)
        self.assertEqual(model.target_hours_total(), 300.0)

    def test_month_is_share_of_total(self):
        project = self.make_project(HourType.ALLTIME, 300)
        model = AllTimeModel(project, self.db)
        month = model.target_hours_for_month(2026, 11)
        self.assertGreaterEqual(month, 0.0)
        self.assertLessEqual(month, 300.0)


class TestFactory(ModelTestBase):

    def test_factory_selects_strategy(self):
        self.assertIsInstance(
            get_working_time_model(self.make_project(HourType.WEEKLY, 40), self.db),
            WeeklyModel,
        )
        self.assertIsInstance(
            get_working_time_model(self.make_project(HourType.DAILY, 8), self.db),
            DailyModel,
        )
        self.assertIsInstance(
            get_working_time_model(self.make_project(HourType.MONTHLY, 20), self.db),
            MonthlyModel,
        )
        self.assertIsInstance(
            get_working_time_model(self.make_project(HourType.ALLTIME, 300), self.db),
            AllTimeModel,
        )
