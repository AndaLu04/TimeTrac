from pathlib import Path


from data.database import DATABASE, database_cursor


class SettingsRepository:
    """
    Key-Value-Speicher für gerätelokale Einstellungen.

    Bewusst nicht synchronisiert (siehe ARCHITECTURE.md 3.5). Werte werden
    als TEXT gespeichert; Aufrufer serialisieren komplexe Werte (z. B. JSON).
    """

    def __init__(self, database_path: Path = DATABASE):
        self.database_path: Path = database_path

    def set(self, key: str, value: str | None) -> None:
        with database_cursor(self.database_path) as cursor:
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get(self, key: str, default: str | None = None) -> str | None:
        with database_cursor(self.database_path) as cursor:
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            return default if row is None else row[0]

    def delete(self, key: str) -> None:
        with database_cursor(self.database_path) as cursor:
            cursor.execute("DELETE FROM settings WHERE key=?", (key,))

    def keys(self) -> list[str]:
        with database_cursor(self.database_path) as cursor:
            cursor.execute("SELECT key FROM settings ORDER BY key")
            return [row[0] for row in cursor.fetchall()]
