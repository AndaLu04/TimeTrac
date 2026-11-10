from datetime import datetime

from constants import EntryType
from data.database import Database, database_cursor
from data.entry import Entry
from data.project import Project


class TrackingError(ValueError):
    """Fachlicher Validierungsfehler des TrackingService."""


class TrackingService:
    """
    Orchestriert Ein-/Ausstempeln und CRUD auf Entries (ARCHITECTURE.md 5.2).

    Erzwingt die Invarianten aus Abschnitt 3.6:
    - genau ein aktiver Eintrag global (zusätzlich durch Unique-Index gesichert)
    - end_at > begin_at (falls gesetzt)
    - is_active = 0 impliziert end_at gesetzt
    - edited_at wird zentral hier gesetzt
    """

    def __init__(self, db: Database):
        self.db = db

    def get_active_entry(self) -> Entry | None:
        """Liefert den einzigen aktiven Eintrag oder None."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute(
                "SELECT id FROM entries WHERE is_active = 1 AND deleted_at IS NULL"
            )
            row = cursor.fetchone()
        return Entry(self.db, row[0]) if row else None

    def clock_in(
        self, project: Project, entry_type: EntryType = EntryType.ARBEIT
    ) -> Entry:
        """
        Stempelt ein: erzeugt einen neuen aktiven Eintrag für das Projekt.

        Raises:
            TrackingError: wenn bereits ein aktiver Eintrag existiert.
        """
        if self.get_active_entry() is not None:
            raise TrackingError("Es läuft bereits ein aktiver Eintrag")
        now = datetime.now()
        entry = Entry(
            self.db,
            None,
            project.id,
            entry_type=entry_type,
            is_active=True,
            entry_date=now.date(),
            begin_at=now,
        )
        return entry

    def clock_out(self, entry: Entry) -> Entry:
        """
        Stempelt aus: beendet den aktiven Eintrag mit der aktuellen Zeit.

        Raises:
            TrackingError: wenn der Eintrag nicht aktiv ist.
        """
        if not entry.is_active:
            raise TrackingError("Nur ein aktiver Eintrag kann ausgestempelt werden")
        now = datetime.now()
        entry.end_at = now
        entry.edited_at = now
        entry.is_active = False
        return entry

    def update_times(
        self, entry: Entry, begin_at: datetime, end_at: datetime | None
    ) -> Entry:
        """
        Korrigiert die Zeiten eines Eintrags mit Validierung.

        Raises:
            TrackingError: bei end_at <= begin_at oder fehlendem end_at
                für einen nicht aktiven Eintrag.
        """
        if end_at is not None and end_at <= begin_at:
            raise TrackingError("end_at muss nach begin_at liegen")
        if entry.is_active and end_at is not None:
            raise TrackingError("Ein aktiver Eintrag hat noch kein end_at")
        if not entry.is_active and end_at is None:
            raise TrackingError("Ein beendeter Eintrag braucht ein end_at")
        now = datetime.now()
        entry.begin_at = begin_at
        if end_at is not None:
            entry.end_at = end_at
        entry.edited_at = now
        return entry

    def delete_entry(self, entry: Entry) -> None:
        """Soft Delete: setzt deleted_at, entfernt nichts aus der DB."""
        now = datetime.now()
        if entry.is_active:
            entry.is_active = False
        entry.deleted_at = now
        entry.edited_at = now
