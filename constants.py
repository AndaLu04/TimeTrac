from pathlib import Path
from enum import StrEnum, Enum

PROJECT_ROOT = Path(__file__).parent
DATABASE = PROJECT_ROOT / "data" / "database.db"

class EntryType(StrEnum):
    ARBEIT = "Arbeit"
    KRANKHEIT = "Krankheit"
    URLAUB = "Urlaub"
    FEIERTAG = "Feiertag"
    PLATZHALTER = "Platzhalter"

class HourType(StrEnum):
    ALLTIME = "Alltime"
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    DAILY = "Daily"

class Tables(Enum):
    projects = "projects"
    entries = "entries"


ALLOWED_COLUMNS = {
    Tables.projects: {"name", "target_hours", "hour_type", "is_default"},
    Tables.entries: {"project_id", "entry_type", "is_active", "created_at", "edited_at", "entry_date", "begin_at", "end_at", "notes"}
}