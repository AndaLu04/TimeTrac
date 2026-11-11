from datetime import datetime
from os import replace
from pathlib import Path
from shutil import copyfile
from uuid import uuid4

from data.database import Database
from logic.settings_service import SettingsService


class BackupError(ValueError):
    """Fachlicher Fehler beim Backup/Restore."""


class BackupService:
    """Manueller DB-Export/-Import über Dateipfade (ARCHITECTURE.md 5.5)."""

    def __init__(self, db: Database):
        self.db = db
        self.settings = SettingsService(db)

    def export_backup(self, target: Path) -> Path:
        """
        Kopiert die SQLite-Datenbank an einen Zielort.

        Raises:
            BackupError: wenn die Zieldatenbank keine gültige TimeTrac-DB ist.
        """
        if not self._is_valid_database(self.db.database_path):
            raise BackupError("Die Quelldatenbank ist keine gültige TimeTrac-Datenbank")
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(self.db.database_path, target)
        self.settings.set_last_backup_at(datetime.now().isoformat())
        return target

    def import_backup(self, source: Path) -> None:
        """
        Ersetzt die aktuelle Datenbank durch eine Backup-Datei.

        Die Backupdatei wird zuerst im DB-Verzeichnis gestaged, migriert und
        validiert; erst dann ersetzt os.replace die Live-DB atomar. Bei einem
        Fehler bleibt die Live-DB unangetastet, die Staging-Datei wird entfernt.

        Raises:
            BackupError: wenn die Quelle keine gültige TimeTrac-DB ist
                oder die gestagede Kopie nach Migration ungültig ist.
        """
        source = Path(source)
        if not source.exists() or not self._is_valid_database(source):
            raise BackupError("Die Backupdatei ist keine gültige TimeTrac-Datenbank")
        staged = Path(self.db.database_path).with_name(
            f".{Path(self.db.database_path).name}.import-{uuid4().hex}.tmp"
        )
        try:
            copyfile(source, staged)
            Database(database_path=staged)
            if not self._is_valid_database(staged):
                raise BackupError(
                    "Die gestagede Backupdatei ist keine gültige TimeTrac-Datenbank"
                )
            replace(staged, self.db.database_path)
        finally:
            staged.unlink(missing_ok=True)

    def _is_valid_database(self, path) -> bool:
        """Delegiert die DB-Validierung an den Data-Layer."""
        return Database.is_valid_database(path)
