from data.database import Database, Tables, database_cursor


class SettingsRepository:
    """
    Key-Value-Speicher für gerätelokale Einstellungen.

    Bewusst nicht synchronisiert (siehe ARCHITECTURE.md 3.5). Werte werden
    als TEXT gespeichert; Aufrufer serialisieren komplexe Werte (z. B. JSON).

    Attributes:
        db: The Database instance used for persistence.
        table: The database table (Tables.settings) where settings are stored.
    """

    def __init__(self, db: Database):
        """
        Initialize the SettingsRepository.

        Args:
            db: The Database instance for persistence operations.
        """
        self.db = db
        self.table = Tables.settings

    def set(self, key: str, value: str | None) -> None:
        """Schreibt einen Wert unter einem Schlüssel (überschreibt vorhandene)."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get(self, key: str, default: str | None = None) -> str | None:
        """Liest einen Wert, mit Default bei fehlendem Schlüssel."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            return default if row is None else row[0]

    def delete(self, key: str) -> None:
        """Entfernt einen Schlüssel aus der Tabelle."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute("DELETE FROM settings WHERE key=?", (key,))

    def keys(self) -> list[str]:
        """Listet alle vorhandenen Schlüssel aufsteigend."""
        with database_cursor(self.db.database_path) as cursor:
            cursor.execute("SELECT key FROM settings ORDER BY key")
            return [row[0] for row in cursor.fetchall()]
