from datetime import date, datetime
from typing import Iterator
from itertools import repeat

from constants import DATABASE, EntryType, HourType, Tables, ALLOWED_COLUMNS
from pathlib import Path
from contextlib import contextmanager
from sqlite3 import connect, Cursor, PARSE_DECLTYPES, PARSE_COLNAMES, register_adapter, register_converter


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
        database=db,
        detect_types=PARSE_DECLTYPES | PARSE_COLNAMES,
        autocommit=True)
    cursor = connection.cursor()
    try:
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
        return val.value

    def adapt_hour_type(val: HourType) -> str:
        return val.value

    def convert_date(val):
        """Convert ISO 8601 date to datetime.date object."""
        return date.fromisoformat(val.decode())

    def convert_datetime(val):
        """Convert ISO 8601 datetime to datetime.datetime object."""
        return datetime.fromisoformat(val.decode())

    def convert_entry_type(val):
        str_value = val.decode() if isinstance(val, bytes) else val
        return EntryType(str_value)

    def convert_hour_type(val):
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

    def __init__(self, database_path: Path=DATABASE):
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
        """
        statement = f"SELECT {key} from {table.name} where id=?"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement, (row_id,))
            return cursor.fetchone()[0]

    def get_ids(self, table: Tables) -> list[int]:
        """
        Retrieve all row IDs from a database table.

        Args:
            table: The Tables enum value for the target table.

        Returns:
            A list of integer row IDs.
        """
        statement = f"SELECT id from {table.name}"
        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement)
            return [row[0] for row in cursor.fetchall()]

    def insert_new_row(self, content: dict,  table: Tables) -> int:
        """
        Insert a new row into a database table.

        Args:
            content: Dictionary of column names and values to insert.
            table: The Tables enum value for the target table.

        Returns:
            The ID of the newly inserted row.
        """
        values: list = []
        keys: list = []
        for key, value in content.items():
            values.append(value)
            keys.append(key)


        statement: str = f"""
                         INSERT INTO {table.name} ({",".join(keys)})
                         Values ({",".join(repeat('?', times=len(values)))})
                         """

        with database_cursor(self.database_path) as cursor:
            cursor.execute(statement, values)
            row_id = cursor.lastrowid
            print(f"Inserted row into database: table:{table.name}, row_id:{row_id}")
            return row_id

    def _create_table_projects(self) -> None:
        """
        Create the projects table if it doesn't exist.

        This is a private method called during Database initialization.

        Args:
            database_path: Path to the SQLite database file. Defaults to DATABASE constant.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_hours REAL NOT NULL,
                    hour_type hour_type NOT NULL,
                    is_default BOOLEAN NOT NULL
                );
                """
            )

    def _create_table_entries(self) -> None:
        """
        Create the entries table if it doesn't exist.

        This is a private method called during Database initialization.
        Establishes a foreign key relationship to the projects table.

        Args:
            database_path: Path to the SQLite database file. Defaults to DATABASE constant.
        """
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                """
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
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                """
            )

if __name__ == "__main__":
    database = Database()
    content = {
        "project_id": 0,
        "entry_type": "test",
        "is_active": True,
        "created_at": datetime.now(),
        "edited_at": None,
        "entry_date": date.today(),
        "begin_at": datetime.now(),
        "end_at": None,
        "notes": "dev",
    }
    database.insert_new_row(content=content, table=Tables.entries)
