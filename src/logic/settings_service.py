from json import dumps, loads

from data.database import Database
from data.settings import SettingsRepository

DEFAULTS = {
    "language": "de",
    "active_project_id": None,
    "default_break_minutes": 0,
    "csv_delimiter": ",",
    "dashboard_layout": None,
    "last_backup_at": None,
}


class SettingsService:
    """Typisierter Zugriff auf gerätelokale Einstellungen (ARCHITECTURE.md 3.5)."""

    def __init__(self, db: Database):
        self.repository = SettingsRepository(db.database_path)

    def get_raw(self, key: str) -> str | None:
        """Liest einen Rohwert mit Fallback auf den konfigurierten Default."""
        return self.repository.get(key, DEFAULTS.get(key))

    def set_raw(self, key: str, value: str | None) -> None:
        """Schreibt einen Rohwert als TEXT."""
        self.repository.set(key, value)

    def get_language(self) -> str:
        """Liest die Spracheinstellung (Default: de)."""
        return self.get_raw("language") or "de"

    def set_language(self, language: str) -> None:
        """Setzt die Spracheinstellung."""
        self.set_raw("language", language)

    def get_active_project_id(self) -> int | None:
        """Liest das vorausgewählte Projekt beim Einstempeln."""
        raw = self.get_raw("active_project_id")
        return int(raw) if raw is not None else None

    def set_active_project_id(self, project_id: int | None) -> None:
        """Setzt das vorausgewählte Projekt (None leert die Auswahl)."""
        self.set_raw(
            "active_project_id", str(project_id) if project_id is not None else None
        )

    def get_default_break_minutes(self) -> int:
        """Liest die Standard-Pausendauer in Minuten."""
        return int(self.get_raw("default_break_minutes") or 0)

    def set_default_break_minutes(self, minutes: int) -> None:
        """Setzt die Standard-Pausendauer in Minuten."""
        self.set_raw("default_break_minutes", str(minutes))

    def get_csv_delimiter(self) -> str:
        """Liest das CSV-Trennzeichen (Default: Komma)."""
        return self.get_raw("csv_delimiter") or ","

    def set_csv_delimiter(self, delimiter: str) -> None:
        """Setzt das CSV-Trennzeichen."""
        self.set_raw("csv_delimiter", delimiter)

    def get_dashboard_layout(self) -> list | dict | None:
        """Liest das Dashboard-Layout als JSON-Struktur."""
        raw = self.get_raw("dashboard_layout")
        return loads(raw) if raw else None

    def set_dashboard_layout(self, layout: list | dict) -> None:
        """Setzt das Dashboard-Layout als JSON-Struktur."""
        self.set_raw("dashboard_layout", dumps(layout))

    def get_last_backup_at(self) -> str | None:
        """Liest den ISO-Zeitstempel des letzten Backups."""
        return self.get_raw("last_backup_at")

    def set_last_backup_at(self, iso_datetime: str) -> None:
        """Setzt den ISO-Zeitstempel des letzten Backups."""
        self.set_raw("last_backup_at", iso_datetime)
