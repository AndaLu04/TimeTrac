from datetime import datetime
from pathlib import Path
from shutil import copyfile

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

        Raises:
            BackupError: wenn die Quelle keine gültige TimeTrac-DB ist.
        """
        source = Path(source)
        if not source.exists() or not self._is_valid_database(source):
            raise BackupError("Die Backupdatei ist keine gültige TimeTrac-Datenbank")
        copyfile(source, self.db.database_path)

    def _is_valid_database(self, path) -> bool:
        return Database.is_valid_database(path)
