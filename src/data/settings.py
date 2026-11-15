class SettingsAdapter:
    """
    Daten-Adapter für gerätelokale Einstellungen, gesichert als JSON-Datei.

    Der Adapter ist die einzige Zugriffsschicht auf die Einstellungsdatei
    (siehe ARCHITECTURE.md 3.5). Werte werden als native JSON-Typen
    (str, int, float, bool, list, dict, None) gespeichert.

    Attributes:
        file_path: Pfad zur JSON-Datei, in der die Einstellungen liegen.
    """

    def __init__(self, file_path: str):
        """
        Initialisiert den Adapter mit dem Pfad zur Einstellungsdatei.

        Args:
            file_path: Pfad zur JSON-Datei. Existiert sie noch nicht, wird
                sie beim ersten Schreibvorgang angelegt.
        """
        self.file_path = file_path

    def get(self, key: str, default=None):
        """
        Liest den Wert eines Schlüssels.

        Args:
            key: Schlüssel des Eintrags.
            default: Rückgabewert, wenn der Schlüssel nicht existiert.

        Returns:
            Der gespeicherte Wert oder `default`.
        """

    def set(self, key: str, value) -> None:
        """
        Schreibt einen Wert unter einem Schlüssel (überschreibt vorhandene).

        Args:
            key: Schlüssel des Eintrags.
            value: Wert als nativer JSON-Typ.
        """

    def delete(self, key: str) -> None:
        """
        Entfernt einen Schlüssel aus der Datei.

        Args:
            key: Schlüssel des zu löschenden Eintrags.
        """

    def keys(self) -> list[str]:
        """
        Listet alle vorhandenen Schlüssel aufsteigend auf.

        Returns:
            Sortierte Liste aller Schlüssel.
        """

    def _load(self) -> dict:
        """
        Liest die Datei in ein Wörterbuch.

        Returns:
            Alle Einstellungen als Wörterbuch; bei fehlender oder
            korrupter Datei ein leeres Wörterbuch.
        """

    def _save(self, data: dict) -> None:
        """
        Schreibt das Wörterbuch atomar in die Datei.

        Args:
            data: Alle Einstellungen als Wörterbuch.
        """
