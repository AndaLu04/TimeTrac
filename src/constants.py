from enum import Enum, StrEnum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_SRC = PROJECT_ROOT / "src"
DATABASE = PROJECT_ROOT / "data" / "database.db"


class EntryType(StrEnum):
    ARBEIT = "Arbeit"
    KRANKHEIT = "Krankheit"
    URLAUB = "Urlaub"
    FEIERTAG = "Feiertag"
    ELTERNZEIT = "Elternzeit"
    UEBERSTUNDENAUSGLEICH = "Überstundenausgleich"
    SONSTIGES = "Sonstiges"
    PLATZHALTER = "Platzhalter"


class HourType(StrEnum):
    ALLTIME = "Alltime"
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    DAILY = "Daily"


class Tables(Enum):
    projects = "projects"
    entries = "entries"
    settings = "settings"


HALF_DAY_MARKER = "halber Tag"

ALLOWED_COLUMNS = {
    Tables.projects: {
        "name",
        "target_hours",
        "hour_type",
        "is_default",
        "workdays",
        "daily_hours_override",
        "is_active",
        "notes",
    },
    Tables.entries: {
        "project_id",
        "entry_type",
        "is_active",
        "created_at",
        "edited_at",
        "entry_date",
        "begin_at",
        "end_at",
        "notes",
        "break_minutes",
        "project_label",
        "counts_as_work",
        "deleted_at",
    },
    Tables.settings: {"key", "value"},
}

if __name__ == "__main__":
    print(f"PROJECT_ROOT {PROJECT_ROOT}")
    print(f"DATABASE {DATABASE}")
