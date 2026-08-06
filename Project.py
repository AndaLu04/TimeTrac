from constants import HourType
from database import Database, Tables
from Entry import Entry

class Project:
    """
    Represents a project in the time tracking system.

    This class models a single project with lazy loading for all properties.
    Properties are loaded from the database only when first accessed, and all
    modifications are automatically persisted to the database.

    Attributes:
        id: The unique database ID of this project.
        db: The Database instance used for persistence.
        table: The database table (Tables.projects) where projects are stored.
    """

    def __init__(self, db: Database, project_id: int | None = None, name: str = "",
                 target_hours: float= 0, hour_type: HourType | None = HourType.WEEKLY, is_default: bool | None = False):
        #ToDo: implement Type Checking like in Entry.py
        """
        Initialize a new or existing Project.

        If project_id is provided, loads the existing project with that ID.
        Otherwise, creates a new project in the database with the provided parameters.

        Args:
            db: The Database instance for persistence operations.
            project_id: Optional existing project ID to load. If None, a new project is created.
            name: The name of the project. Defaults to empty string.
            target_hours: The target hours for this project. Defaults to 0.
            hour_type: The type of hour tracking (from HourType enum). Defaults to None.
            is_default: Whether this is the default project. Defaults to None.
        """
        self.db = db
        self.table = Tables.projects
        self._name: str | None = None
        self._target_hours: float | None = None
        self._hour_type: HourType | None = None
        self._is_default: bool | None = None
        self._init: bool = False

        if project_id is not None:
            self.id = project_id
        else:
            self._init = True
            self.name = name
            self.target_hours = target_hours
            self.hour_type = hour_type
            self.is_default = is_default
            self._init= False

            self.id = self.db.insert_new_row(
                content={"name": name, "target_hours": target_hours, "hour_type": hour_type, "is_default": is_default},
                table=self.table,
            )

        self.entry_list: list[Entry] = [Entry(self.db, entry_id) for entry_id in db.get_entry_ids_from_project_id(self.id)]
        #self.entry_list: list[Entry] = []
        #for entry_id in db.get_entry_ids_from_project_id(self.id):
        #    self.entry_list.append(Entry(self.db, entry_id))

    @property
    def name(self) -> str:
        """
        Get the name of this project.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The project name as a string.
        """
        if self._name is None:
            self._name = self.db.get(self.table, self.id, "name")
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the name of this project.

        Automatically persists the change to the database.

        Args:
            value: The new project name.
        """
        if isinstance(value, str):
            self._name = value
            if not self._init:
                self.db.set(self.table, self.id, "name", value)
        else:
            raise TypeError(f"'name' must be str but is {value.__class__.__name__}")

    @property
    def target_hours(self) -> float | int:
        """
        Get the target hours for this project.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The target hours as a float or int.
        """
        if self._target_hours is None:
            self._target_hours = self.db.get(self.table, self.id, "target_hours")
        return self._target_hours

    @target_hours.setter
    def target_hours(self, value: float) -> None:
        """
        Set the target hours for this project.

        Automatically persists the change to the database.

        Args:
            value: The new target hours value.
        """
        if isinstance(value, float) or isinstance(value, int):
            self._target_hours = value
            if not self._init:
                self.db.set(self.table, self.id, "target_hours", value)
        else:
            raise TypeError(f"'target_hours' must be float but is {value.__class__.__name__}")

    @property
    def hour_type(self) -> HourType:
        """
        Get the hour type for this project.

        Lazily loads from database on first access if not already loaded.

        Returns:
            The hour type as a HourType enum value.
        """
        if self._hour_type is None:
            self._hour_type = self.db.get(self.table, self.id, "hour_type")
        return self._hour_type

    @hour_type.setter
    def hour_type(self, value: HourType) -> None:
        """
        Set the hour type for this project.

        Automatically persists the change to the database.

        Args:
            value: The new hour_type value (HourType enum).
        """
        if isinstance(value, HourType):
            self._hour_type = value
            if not self._init:
                self.db.set(self.table, self.id, "hour_type", value)
        else:
            raise TypeError(f"'hour_type' must be HourType enum but is {value.__class__.__name__}")

    @property
    def is_default(self) -> bool:
        """
        Get whether this is the default project.

        Lazily loads from database on first access if not already loaded.

        Returns:
            True if this is the default project, False otherwise.
        """
        if self._is_default is None:
            self._is_default = self.db.get(self.table, self.id, "is_default")
        return self._is_default

    @is_default.setter
    def is_default(self, value: bool) -> None:
        """
        Set whether this is the default project.

        Automatically persists the change to the database.

        Args:
            value: The new is_default value (boolean).
        """
        if isinstance(value, bool):
            self._is_default = value
            if not self._init:
                self.db.set(self.table, self.id, "is_default", value)
        else:
            raise TypeError(f"'is_default' must be bool but is {value.__class__.__name__}")


if __name__ == '__main__':
    database = Database()
    project = Project(database, None, "test", 20)
    print(project.id, project.name, project.target_hours, project.hour_type, project.is_default)