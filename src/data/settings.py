from dataclasses import dataclass, field


@dataclass
class Settings:
    """
    Datenklasse für alle gerätelokalen Einstellungen (ARCHITECTURE.md 3.5).

    Die JSON-Datei dient als persistenter Speicher: Beim Startup werden alle
    Einstellungen geladen; jede Änderung wird sofort zurückgeschrieben.

    Sync-Konzept (vorbereitet, in v1 ohne Sync):
        Jede Einstellung ist fest (hardcodiert) als GLOBAL (wird synchronisiert)
        oder LOKAL (wird nicht synchronisiert) klassifiziert – siehe
        SYNC_SCOPE. Der Nutzer hat darauf keinen Einfluss.

    Textfeld-Validierung:
        Einstellungen ohne festes Auswahlfeld (z. B. csv_delimiter) werden
        vor dem Speichern über die zugehörige validate_*-Methode geprüft.
    """

    # --- Persistenz ---------------------------------------------------------

    #: Pfad zur JSON-Datei, in der die Einstellungen gespeichert werden.
    file_path: str

    # --- Einstellungen laut ARCHITECTURE.md 3.5 ---------------------------

    #: UI-Sprache (de/en) – GLOBAL.
    language: str = "de"
    #: Vorausgewähltes Projekt beim Einstempeln – LOKAL.
    active_project_id: int | None = None
    #: Standard-Pausendauer in Minuten – GLOBAL.
    default_break_minutes: int = 0
    #: CSV-Trennzeichen, frei eintragbar (Textfeld) – LOKAL.
    csv_delimiter: str = ","
    #: Dezimaltrennzeichen im CSV-Export – LOKAL.
    csv_decimal_separator: str = "."
    #: Sync-Backend (none/webdav/gdrive/file) – LOKAL.
    sync_backend: str = "none"
    #: Sync-Konfiguration (URL, Zugangsdaten) – LOKAL.
    sync_config: dict = field(default_factory=dict)
    #: ISO-Zeitstempel des letzten Backups – LOKAL.
    last_backup_at: str | None = None
    #: ISO-Zeitstempel des letzten Syncs – LOKAL.
    last_sync_at: str | None = None
    #: Sichtbare Kacheln + Reihenfolge im Dashboard – LOKAL.
    dashboard_layout: list = field(default_factory=list)

    # --- Ergänzende, potenziell benötigte Einstellungen -------------------

    #: Farbschema der Oberfläche (light/dark/system) – LOKAL.
    ui_theme: str = "light"
    #: Screen, der beim Start angezeigt wird – LOKAL.
    start_screen: str = "dashboard"
    #: Überstundenstand in Stunden, ab dem gewarnt wird – GLOBAL.
    overtime_warning_threshold: float = 0.0
    #: Änderungen automatisch in die JSON-Datei schreiben – LOKAL.
    auto_save_active: bool = True

    # --- Sync-Klassifikation (hardcodiert, keine Nutzereingabe) -----------

    #: Fest definiert, welche Einstellung GLOBAL (sync) bzw. LOKAL (kein
    #: Sync) ist. Schlüssel = Attributname, Wert = "global" | "local".
    SYNC_SCOPE: dict = field(
        default_factory=lambda: {
            "language": "global",
            "active_project_id": "local",
            "default_break_minutes": "global",
            "csv_delimiter": "local",
            "csv_decimal_separator": "local",
            "sync_backend": "local",
            "sync_config": "local",
            "last_backup_at": "local",
            "last_sync_at": "local",
            "dashboard_layout": "local",
            "ui_theme": "local",
            "start_screen": "local",
            "overtime_warning_threshold": "global",
            "auto_save_active": "local",
        },
        init=False,
    )

    def __post_init__(self) -> None:
        """
        Lädt nach dem Startup alle Einstellungen aus der JSON-Datei.

        Fehlende Schlüssel behalten ihre Default-Werte; eine fehlende oder
        korrupte Datei führt zu den Defaults (kein Absturz beim Startup).
        """

    # --- Persistenz --------------------------------------------------------

    def save(self) -> None:
        """
        Schreibt alle Einstellungen atomar in die JSON-Datei.
        """

    def _persist_if_auto_save(self) -> None:
        """
        Schreibt die Einstellungen nach einer Änderung weg, sofern
        auto_save_active gesetzt ist.
        """

    # --- Validierung (Textfelder ohne Auswahlfeld) -------------------------

    def validate_csv_delimiter(self, value: str) -> bool:
        """
        Prüft ein frei eintragbares CSV-Trennzeichen.

        Args:
            value: Vorschlag für das Trennzeichen.

        Returns:
            True, wenn das Trennzeichen gültig ist (genau ein Zeichen,
            keine Ziffer, kein Anführungszeichen).
        """

    def validate_csv_decimal_separator(self, value: str) -> bool:
        """
        Prüft das Dezimaltrennzeichen.

        Args:
            value: Vorschlag für das Dezimaltrennzeichen.

        Returns:
            True, wenn das Zeichen gültig ist (nur "." oder ",").
        """

    def validate_overtime_warning_threshold(self, value: float) -> bool:
        """
        Prüft die Überstunden-Warnschwelle.

        Args:
            value: Vorschlag für die Schwelle in Stunden.

        Returns:
            True, wenn der Wert gültig ist (nicht negativ).
        """

    # --- Sync-Vorbereitung --------------------------------------------------

    def get_sync_payload(self) -> dict:
        """
        Liefert nur die GLOBALen Einstellungen für einen zukünftigen Sync.

        Returns:
            Wörterbuch mit allen Einstellungen, deren SYNC_SCOPE "global"
            ist.
        """

    def apply_sync_payload(self, payload: dict) -> None:
        """
        Übernimmt empfangene globale Einstellungen (Last-Writer-Wins).

        Args:
            payload: Wörterbuch mit globalen Einstellungen vom Sync-Backend.
        """
