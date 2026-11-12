import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from itertools import repeat
from pathlib import Path
from sqlite3 import (PARSE_COLNAMES, PARSE_DECLTYPES, Cursor, connect,
                     register_adapter, register_converter)
from typing import Iterator

from constants import ALLOWED_COLUMNS, DATABASE, EntryType, HourType, Tables


@contextmanager
def database_cursor(db: Path = DATABASE) -> Iterator[Cursor]:
    """
    Context manager for database cursor operations.

    Creates a connection and cursor to the SQLite database, with automatic commit
    and proper cleanup on exit.

    Args:
        db: Path to the SQLite database file. Defaults to DATABASE constant.

    Yields:
        A SQLite cursor for executing database operations.
    """
    connection = connect(
        database=db, detect_types=PARSE_DECLTYPES | PARSE_COLNAMES, autocommit=True
    )
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        yield cursor
    finally:
        cursor.close()


def init_sqlite_converters_and_adapters():
    """
    Initialize SQLite adapters and converters for custom types.

    Registers adapters for datetime.date and datetime.datetime to serialize them
    to ISO 8601 format, and converters to deserialize them back to Python objects.
    Also registers a converter for EntryType enum values.

    This should be called once before using the database to ensure proper type handling.
    """

    def adapt_date_iso(val: date):
        """Adapt datetime.date to ISO 8601 date."""
        return val.isoformat()

    def adapt_datetime_iso(val: datetime):
        """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
        return val.isoformat()

    def adapt_entry_type(val: EntryType) -> str:
        """Serialisiert EntryType nach TEXT."""
        return val.value

    def adapt_hour_type(val: HourType) -> str:
        """Serialisiert HourType nach TEXT."""
        return val.value

    def convert_date(val):
        """Convert ISO 8601 date to datetime.date object."""
        return date.fromisoformat(val.decode())

    def convert_datetime(val):
        """Convert ISO 8601 datetime to datetime.datetime object."""
        return datetime.fromisoformat(val.decode())

    def convert_entry_type(val):
        """Deserialisiert TEXT nach EntryType."""
        str_value = val.decode() if isinstance(val, bytes) else val
        return EntryType(str_value)

    def convert_hour_type(val):
        """Deserialisiert TEXT nach HourType."""
        str_value = val.decode() if isinstance(val, bytes) else val
        return HourType(str_value)

    register_adapter(date, adapt_date_iso)
    register_adapter(datetime, adapt_datetime_iso)
    register_adapter(EntryType, adapt_entry_type)
    register_adapter(HourType, adapt_hour_type)

    register_converter("date", convert_date)
    register_converter("datetime", convert_datetime)
    register_converter("entry_type", convert_entry_type)
    register_converter("hour_type", convert_hour_type)


class Database:
    """
    Manages database operations for the time tracking system.

    This class provides static methods for CRUD operations on the database tables.
    It initializes the database schema on instantiation and sets up type converters.

    Attributes:
        database_path: Path to the SQLite database file.
    """

    def __init__(self, database_path: Path = DATABASE):
        """
        Initialize the Database instance.

        Creates the database tables if they don't exist and initializes SQLite
        converters and adapters for custom types.

        Args:
            database_path: Path to the SQLite database file. Defaults to DATABASE constant.
        """
        self.database_path: Path = database_path

        self._create_table_projects()
        self._create_table_entries()
        self._create_table_settings()

        init_sqlite_converters_and_adapters()

    def set(self, table: Tables, row_id: int, key, value):
        """
        Update a single field in a database table.

        Args:
            table: The Tables enum value for the target table.
            row_id: The ID of the row to update.
            key: The column name to update.
            value: The new value to set.
        """
        if key not in ALLOWED_COLUMNS[table]:
            raise ValueError(f"Invalid column: {key}")
        statement = f"UPDATE {table.name} SET {key}=? where id=?"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement, (value, row_id))

    def get(self, table: Tables, row_id, key):
        """
        Retrieve a single field from a database table.

        Args:
            table: The Tables enum value for the target table.
            row_id: The ID of the row to retrieve from.
            key: The column name to retrieve.

        Returns:
            The value of the specified column from the database.

        Raises:
            ValueError: If the column is not in ALLOWED_COLUMNS for the table.
        """
        if key not in ALLOWED_COLUMNS[table]:
            raise ValueError(f"Invalid column: {key}")
        statement = f"SELECT {key} from {table.name} where id=?"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement, (row_id,))
            return cursor.fetchone()[0]

    def get_all_project_ids(self) -> list:
        """Listet die IDs aller Projekte auf."""
        statement = "SELECT id from projects"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement)
            return [row[0] for row in cursor.fetchall()]

    def get_active_entry_id(self) -> int | None:
        """
        Retrieve the ID of the single active, non-deleted entry.

        Returns:
            The entry ID, or None if no entry is active.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                "SELECT id FROM entries WHERE is_active = 1"
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def get_entry_ids_between_dates(
        self, project_id: int, start: date, end: date
    ) -> list[int]:
        """
        Retrieve IDs of non-deleted entries of a project within a date range.

        Args:
            project_id: The project ID to filter by.
            start: First entry_date (inclusive).
            end: Last entry_date (inclusive).

        Returns:
            A list of integer entry IDs.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                "SELECT id FROM entries "
                "WHERE project_id = ? AND deleted_at IS NULL AND entry_date BETWEEN ? AND ?",
                (project_id, start, end),
            )
            return [row[0] for row in cursor.fetchall()]


    def entry_exists(
        self, project_id: int, entry_type: EntryType, entry_date: date
    ) -> bool:
        """
        Check whether a non-deleted entry of a given type exists on a date.

        Args:
            project_id: The project ID to filter by.
            entry_type: The entry type to look for.
            entry_date: The entry date to look for.

        Returns:
            True if at least one matching entry exists.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                "SELECT id FROM entries "
                "WHERE project_id = ? AND entry_type = ? AND entry_date = ? AND deleted_at IS NULL",
                (project_id, entry_type, entry_date),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def is_valid_database(database_path: Path) -> bool:
        """
        Check whether a file is a valid TimeTrac database.

        Args:
            database_path: Path to the file to check.

        Returns:
            True if the file is a SQLite database with an entries table.
        """
        try:
            with database_cursor(database_path) as cursor:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
                )
                return cursor.fetchone() is not None
        except (sqlite3.Error, OSError):
            return False

    def get_entry_ids_from_project_id(self, project_id: int) -> list[int]:
        """
        Retrieve all row IDs from a database table.

        Args:
            project_id: The project ID to filter by.

        Returns:
            A list of integer row IDs.
        """
        statement = "SELECT id from entries where project_id=?"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement, (project_id,))
            return [row[0] for row in cursor.fetchall()]

    def insert_new_row(self, content: dict, table: Tables) -> int:
        """
        Insert a new row into a database table.

        Args:
            content: Dictionary of column names and values to insert.
            table: The Tables enum value for the target table.

        Returns:
            The ID of the newly inserted row.
        """
        invalid_columns = set(content) - ALLOWED_COLUMNS[table]
        if invalid_columns:
            raise ValueError(f"Invalid columns: {invalid_columns}")

        values: list = list(content.values())
        keys: list = list(content)

        statement: str = f"""
                         INSERT INTO {table.name} ({",".join(keys)})
                         Values ({",".join(repeat('?', times=len(values)))})
                         """

        with database_cursor(self.database_path) as cursor:
            try:
                cursor.execute(statement, values)
            except sqlite3.IntegrityError as e:
                if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                    raise ValueError(f"Entry cannot be made active. Current Active entry id: {self.get_active_entry_id()}")
                else:
                    raise e
            row_id = cursor.lastrowid
            print(f"Inserted row into database: table:{table.name}, row_id:{row_id}")
            return row_id

    def _create_table_projects(self) -> None:
        """
        Create the projects table if it doesn't exist.

        This is a private method called during Database initialization.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_hours REAL NOT NULL,
                    hour_type hour_type NOT NULL,
                    is_default BOOLEAN NOT NULL,
                    workdays TEXT NOT NULL DEFAULT '[0,1,2,3,4]',
                    daily_hours_override TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    notes TEXT
                );
                """)

    def _create_table_settings(self) -> None:
        """Create the settings table (key-value) if it doesn't exist."""
        with database_cursor(self.database_path) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings
                (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """)

    def _create_table_entries(self) -> None:
        """
        Create the entries table if it doesn't exist.

        This is a private method called during Database initialization.
        Establishes a foreign key relationship to the projects table.

        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entries(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    entry_type entry_type NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    created_at datetime NOT NULL,
                    edited_at datetime,
                    entry_date DATE NOT NULL,
                    begin_at datetime,
                    end_at datetime,
                    notes TEXT,
                    break_minutes INTEGER NOT NULL DEFAULT 0,
                    project_label TEXT,
                    counts_as_work BOOLEAN,
                    deleted_at datetime,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                """)
            cursor.execute("""
                           CREATE UNIQUE INDEX IF NOT EXISTS single_true_index
                               ON entries (is_active)
                               WHERE is_active = 1
                           """)


if __name__ == "__main__":
    database = Database()
    project = {
        "name": "",
        "target_hours": 0,
        "hour_type": "",
        "is_default": False,
        "workdays": "",
        "daily_hours_override": "",
        "is_active": 1,
        "notes": ""
    }
    entry = {
        "project_id": 1,
        "entry_type": "test",
        "is_active": False,
        "created_at": datetime.now(),
        "edited_at": None,
        "entry_date": date.today(),
        "begin_at": datetime.now(),
        "end_at": None,
        "notes": "dev",
    }
    database.insert_new_row(project, Tables.projects)
    database.insert_new_row(content=entry, table=Tables.entries)
    projects = database.get_all_project_ids()
    entries = {}
    for project in projects:
        _entry_id_list = []
        for entry_id in database.get_entry_ids_from_project_id(project):
            _entry_id_list.append(entry_id)
        entries.update({project: _entry_id_list})


    print(entries)