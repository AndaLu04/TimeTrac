from datetime import date, datetime, timedelta
from typing import Optional

from constants import EntryType
from data.database import Database, Tables


class Entry:
    """
    Represents a time tracking entry in the database.

    This class models a single entry for time recording (Zeiterfassung) with lazy loading
    from the database. Properties are loaded from the database only when first accessed,
    and all modifications are automatically persisted to the database.

    Attributes:
        id: The unique database ID of this entry.
        db: The Database instance used for persistence.
        table: The database table (Tables.entries) where entries are stored.
    """

    def __init__(
        self,
        db: Database,
        entry_id: int | None = None,
        project_id: int = None,
        entry_type: EntryType = EntryType.ARBEIT,
        is_active: bool = False,
        created_at: datetime = None,
        edited_at: datetime | None = None,
        entry_date: date = None,
        begin_at: datetime = None,
        end_at: datetime | None = None,
        notes: str | None = None,
        break_minutes: int = 0,
        project_label: str | None = None,
        counts_as_work: bool | None = None,
        deleted_at: datetime | None = None,
    ):
        """
        Initialize a new or existing Entry.

        If entry_id is provided, loads the existing entry with that ID.
        Otherwise, creates a new entry in the database with the provided parameters.

        Args:
            project_id: The ID of the project this entry belongs to.
            db: The Database instance for persistence operations.
            entry_id: Optional existing entry ID to load. If None, a new entry is created.
            entry_type: The type of entry (from EntryType enum). Defaults to EntryType.ARBEIT.
            is_active: Whether the entry is active. Defaults to False.
            created_at: When the entry was created. Defaults to current datetime.
            edited_at: When the entry was last edited. Defaults to None.
            entry_date: The date of the entry. Defaults to today.
            begin_at: When the entry begins. Defaults to current datetime.
            end_at: When the entry ends. Defaults to None (ongoing).
            notes: Optional notes for the entry. Defaults to None.
            break_minutes: Break duration in minutes. Defaults to 0.
            project_label: Optional free-text activity label. Defaults to None.
            counts_as_work: Whether this entry counts as work (None = per entry_type).
            deleted_at: Optional soft-delete timestamp. Defaults to None.
        """
        self.db = db
        self.table = Tables.entries

        self._project_id: Optional[int] = None
        self._entry_type: Optional[EntryType] = None
        self._is_active: Optional[bool] = None
        self._created_at: Optional[datetime] = None
        self._edited_at: Optional[datetime] = None
        self._entry_date: Optional[date] = None
        self._begin_at: Optional[datetime] = None
        self._end_at: Optional[datetime] = None
        self._notes: Optional[str] = None
        self._break_minutes: Optional[int] = None
        self._project_label: Optional[str] = None
        self._counts_as_work: Optional[bool] = None
        self._counts_as_work_loaded: bool = False
        self._deleted_at: Optional[datetime] = None
        self._deleted_at_loaded: bool = False
        self._duration: Optional[timedelta] = None
        self._init: bool = False

        if entry_id is not None:
            self.id = entry_id
        else:
            if project_id is None:
                raise ValueError("Project ID must be provided")
            if created_at is None:
                created_at = datetime.now()
            if entry_date is None:
                entry_date = date.today()
            if begin_at is None:
                begin_at = datetime.now()

            # Init-Modus: Setter persistieren nicht, die Zeile wird erst danach angelegt
            self._init = True
            self.project_id = project_id
            self.entry_type = entry_type
            self.is_active = is_active
            self.created_at = created_at
            self.edited_at = edited_at
            self.entry_date = entry_date
            self.begin_at = begin_at
            self.end_at = end_at
            self.notes = notes
            self.break_minutes = break_minutes
            self.project_label = project_label
            self.counts_as_work = counts_as_work
            self.deleted_at = deleted_at
            self._init = False
            self.id = self.db.insert_new_row(
                content={
                    "project_id": self._project_id,
                    "entry_type": self._entry_type,
                    "is_active": self._is_active,
                    "created_at": self._created_at,
                    "edited_at": self._edited_at,
                    "entry_date": self._entry_date,
                    "begin_at": self._begin_at,
                    "end_at": self._end_at,
                    "notes": self._notes,
                    "break_minutes": self._break_minutes,
                    "project_label": self._project_label,
                    "counts_as_work": self._counts_as_work,
                    "deleted_at": self._deleted_at,
                },
                table=self.table,
            )

    @property
    def project_id(self) -> int:
        """
        Get the project ID this entry belongs to.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The project_id as an integer.
        """
        if self._project_id is None:
            self._project_id = self.db.get(self.table, self.id, "project_id")
        return self._project_id

    @project_id.setter
    def project_id(self, value: int) -> None:
        """
        Set the project ID for this entry.

        Automatically persists the change to the database.

        Args:
            value: The new project_id value.
        """
        if isinstance(value, int):
            self._project_id = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "project_id", value)
        else:
            raise TypeError(
                f"'project_id' must be an integer but is {value.__class__.__name__}"
            )

    @property
    def entry_type(self) -> EntryType:
        """
        Get the type of this entry.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The entry_type as an EntryType enum value.
        """
        if self._entry_type is None:
            self._entry_type = self.db.get(self.table, self.id, "entry_type")
        return self._entry_type

    @entry_type.setter
    def entry_type(self, value: EntryType) -> None:
        """
        Set the type of this entry.

        Automatically persists the change to the database.

        Args:
            value: The new entry_type value (EntryType enum).
        """
        if isinstance(value, EntryType):
            self._entry_type = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "entry_type", value)
        else:
            raise TypeError(
                f"'entry_type' must be an EntryType enum but is of type {value.__class__.__name__}"
            )

    @property
    def is_active(self) -> bool:
        """
        Get whether this entry is active.

        Lazily loads from database on first access if not already loaded.

        Returns:
            True if the entry is active, False otherwise.
        """
        if self._is_active is None:
            self._is_active = self.db.get(self.table, self.id, "is_active")
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """
        Set whether this entry is active.

        Automatically persists the change to the database.

        Args:
            value: The new is_active value (boolean).
        """
        if isinstance(value, bool):
            self._is_active = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "is_active", value)
        else:
            raise TypeError(
                f"'is_active' must be True or False, but is {value.__class__.__name__}"
            )

    @property
    def created_at(self) -> datetime:
        """
        Get when this entry was created.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The creation timestamp as a datetime object.
        """
        if self._created_at is None:
            self._created_at = self.db.get(self.table, self.id, "created_at")
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime | None) -> None:
        """
        Set when this entry was created.

        Automatically persists the change to the database.

        Args:
            value: The new created_at timestamp (datetime).
        """
        if isinstance(value, datetime):
            self._created_at = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "created_at", value)
        else:
            raise TypeError(
                f"'created_at' must be datetime but is {value.__class__.__name__}"
            )

    @property
    def edited_at(self) -> datetime | None:
        """
        Get when this entry was last edited.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The last edit timestamp as a datetime object, or None if never edited.
        """
        if self._edited_at is None:
            self._edited_at = self.db.get(self.table, self.id, "edited_at")
        return self._edited_at

    @edited_at.setter
    def edited_at(self, value: datetime | None) -> None:
        """
        Set when this entry was last edited.

        Automatically persists the change to the database.

        Args:
            value: The new edited_at timestamp (datetime or None).
        """
        if isinstance(value, datetime) or value is None:
            self._edited_at = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "edited_at", value)
        else:
            raise TypeError(
                f"'edited_at' must be datetime or None, but is {value.__class__.__name__}'"
            )

    @property
    def entry_date(self) -> date | None:
        """
        Get the date of this entry.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The entry date as a date object.
        """
        if self._entry_date is None:
            self._entry_date = self.db.get(self.table, self.id, "entry_date")
        return self._entry_date

    @entry_date.setter
    def entry_date(self, value: datetime | None) -> None:
        """
        Set the date of this entry.

        Automatically persists the change to the database.

        Args:
            value: The new entry_date (datetime or None).
        """
        if isinstance(value, date):
            self._entry_date = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "entry_date", value)
        else:
            raise TypeError(
                f"'entry_date' must be date, but is {value.__class__.__name__}"
            )

    @property
    def begin_at(self) -> datetime:
        """
        Get when this entry begins.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The begin timestamp as a datetime object.
        """
        if self._begin_at is None:
            self._begin_at = self.db.get(self.table, self.id, "begin_at")
        return self._begin_at

    @begin_at.setter
    def begin_at(self, value: datetime | None) -> None:
        """
        Set when this entry begins.

        Automatically persists the change to the database.

        Args:
            value: The new begin_at timestamp (datetime or None).
        """
        if isinstance(value, datetime):
            self._begin_at = value
            self._duration = None
            if not self._init:
                self.db.set(Tables.entries, self.id, "begin_at", value)
        else:
            raise TypeError(
                f"'begin_at' must be datetime, but is {value.__class__.__name__}"
            )

    @property
    def end_at(self) -> datetime | None:
        """
        Get when this entry ends.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The end timestamp as a datetime object, or None if still ongoing.
        """
        if self._end_at is None:
            self._end_at = self.db.get(self.table, self.id, "end_at")
        return self._end_at

    @end_at.setter
    def end_at(self, value: datetime) -> None:
        """
        Set when this entry ends.

        Automatically persists the change to the database.

        Args:
            value: The new end_at timestamp (datetime or None).
        """
        if isinstance(value, datetime) or value is None:
            self._end_at = value
            if self._end_at is None:
                self._duration = None
            else:
                self._duration = self.calculate_duration(self._end_at)
            if not self._init:
                self.db.set(Tables.entries, self.id, "end_at", value)
        else:
            raise TypeError(
                f"'end_at' must be datetime or None, but is {value.__class__.__name__}"
            )

    @property
    def notes(self) -> str | None:
        """
        Get the notes for this entry.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The notes as a string, or None if no notes.
        """
        if self._notes is None:
            self._notes = self.db.get(self.table, self.id, "notes")
        return self._notes

    @notes.setter
    def notes(self, value: str | None) -> None:
        """
        Set the notes for this entry.

        Automatically persists the change to the database.

        Args:
            value: The new notes string, or None.
        """
        if isinstance(value, str) or value is None:
            self._notes = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "notes", value)
        else:
            raise TypeError(f"'notes' must be str, but is {value.__class__.__name__}")

    @property
    def break_minutes(self) -> int:
        """
        Get the break duration in minutes.

        Returns:
            The break minutes as an integer (default 0).
        """
        if self._break_minutes is None:
            self._break_minutes = self.db.get(self.table, self.id, "break_minutes")
        return self._break_minutes

    @break_minutes.setter
    def break_minutes(self, value: int) -> None:
        """Set the break duration in minutes (persists automatically)."""
        if isinstance(value, int) and value >= 0:
            self._break_minutes = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "break_minutes", value)
        else:
            raise TypeError(
                f"'break_minutes' must be a non-negative integer, but is {value.__class__.__name__}"
            )

    @property
    def project_label(self) -> str | None:
        """Get the free-text activity label (not to be confused with project_id)."""
        if self._project_label is None:
            self._project_label = self.db.get(self.table, self.id, "project_label")
        return self._project_label

    @project_label.setter
    def project_label(self, value: str | None) -> None:
        """Set the free-text activity label (persists automatically)."""
        if isinstance(value, str) or value is None:
            self._project_label = value
            if not self._init:
                self.db.set(Tables.entries, self.id, "project_label", value)
        else:
            raise TypeError(
                f"'project_label' must be str or None, but is {value.__class__.__name__}"
            )

    @property
    def counts_as_work(self) -> bool | None:
        """
        Get whether this entry counts as work time.

        None means: default per entry_type (see ARCHITECTURE.md 3.3).
        """
        if self._counts_as_work is None and not self._counts_as_work_loaded:
            self._counts_as_work = self.db.get(self.table, self.id, "counts_as_work")
            self._counts_as_work_loaded = True
        return self._counts_as_work

    @counts_as_work.setter
    def counts_as_work(self, value: bool | None) -> None:
        """Set whether this entry counts as work time (persists automatically)."""
        if isinstance(value, bool) or value is None:
            self._counts_as_work = value
            self._counts_as_work_loaded = True
            if not self._init:
                self.db.set(Tables.entries, self.id, "counts_as_work", value)
        else:
            raise TypeError(
                f"'counts_as_work' must be bool or None, but is {value.__class__.__name__}"
            )

    @property
    def deleted_at(self) -> datetime | None:
        """Get the soft-delete timestamp, or None if the entry is not deleted."""
        if self._deleted_at is None and not self._deleted_at_loaded:
            self._deleted_at = self.db.get(self.table, self.id, "deleted_at")
            self._deleted_at_loaded = True
        return self._deleted_at

    @deleted_at.setter
    def deleted_at(self, value: datetime | None) -> None:
        """Set the soft-delete timestamp (persists automatically)."""
        if isinstance(value, datetime) or value is None:
            self._deleted_at = value
            self._deleted_at_loaded = True
            if not self._init:
                self.db.set(Tables.entries, self.id, "deleted_at", value)
        else:
            raise TypeError(
                f"'deleted_at' must be datetime or None, but is {value.__class__.__name__}"
            )

    @property
    def duration(self) -> timedelta:
        """
        Calculate the duration of this entry.

        If end_at is not set (entry is ongoing), calculates duration from created_at to now.
        Otherwise, calculates duration from created_at to end_at.

        Returns:
            A timedelta representing the duration of the entry.
        """
        if self.end_at is None:
            return self.calculate_duration()
        else:
            if self._duration is None:
                self._duration = self.calculate_duration(self.end_at)
            return self._duration

    def calculate_duration(self, end_or_current_time: datetime = None) -> timedelta:
        """Berechnet die Dauer ab begin_at bis zu einem Endzeitpunkt (Default: jetzt)."""
        if end_or_current_time is None:
            end_or_current_time = datetime.now()
        return end_or_current_time - self.begin_at


if __name__ == "__main__":
    database = Database()
    entry = Entry(database, None, 3, is_active=True)
    print(
        "id:            ",
        entry.id,
        "\nproject_id:  ",
        entry.project_id,
        "\nentry_type:  ",
        entry.entry_type,
        "\ncreated_at:  ",
        entry.created_at,
        "\nentry_date:  ",
        entry.entry_date,
        "\nbegin_at:    ",
        entry.begin_at,
        "\nend_at:      ",
        entry.end_at,
        "\nnotes:       ",
        entry.notes,
        "\nduration:    ",
        entry.duration,
    )
    print(entry.entry_type.__class__.__name__)

    # for i in range(10):
    #    sleep(1)
    #    print(entry.duration)
