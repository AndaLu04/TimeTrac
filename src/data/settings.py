from enum import StrEnum
from typing import Annotated


class Sync:
    """
    Marker für Einstellungen, die in einem zukünftigen Sync synchronisiert
    werden (GLOBAL). Attribute ohne diesen Marker sind automatisch LOKAL.

    Die Zuordnung ist damit rein deklarativ am Attribut gepflegt und braucht
    keine separate Liste. Auslesen zur Laufzeit über
    `typing.get_type_hints(Settings, include_extras=True)`.
    """


class Validated:
    """
    Marker für Einstellungen, die als freies Textfeld in der UI erfassbar
    sind und deshalb vor dem Speichern validiert werden müssen.

    Attribute mit diesem Marker werden in `Settings.validate()` geprüft;
    die zugehörige Validierungslogik liegt in `Settings` (siehe
    validate_*-Methoden).
    """


class Language(StrEnum):
    """Zulässige UI-Sprachen (Einstellung `language`)."""

    DE = "de"
    EN = "en"


class SyncBackend(StrEnum):
    """Zulässige Sync-Backends (Einstellung `sync_backend`)."""

    NONE = "none"
    WEBDAV = "webdav"
    GDRIVE = "gdrive"
    FILE = "file"


class Theme(StrEnum):
    """Zulässige Farbschemas (Einstellung `ui_theme`)."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class StartScreen(StrEnum):
    """Zulässige Screens beim Programmstart (Einstellung `start_screen`)."""

    DASHBOARD = "dashboard"
    VERLAUF = "verlauf"
    EINTRAEGE = "eintraege"
    PROJEKTE = "projekte"
    EINSTELLUNGEN = "einstellungen"


class Settings:
    """
    Alle gerätelokalen Einstellungen der Anwendung (ARCHITECTURE.md 3.5).

    Konzept:
        - Die JSON-Datei `file_path` ist der persistente Speicher. Beim
          Startup werden alle Einstellungen geladen; jede Änderung wird
          sofort zurückgeschrieben (siehe `__setattr__`).
        - Der `Sync`-Marker an der Annotation markiert Einstellungen, die
          später synchronisiert werden (GLOBAL); alle übrigen sind LOKAL.
          Die Zuordnung ist hardcodiert, der Nutzer hat keinen Einfluss.
        - Der `Validated`-Marker kennzeichnet freie Textfelder, die vor
          dem Speichern über die validate_*-Methoden geprüft werden.
        - Auswahl-Einstellungen nutzen StrEnums (Language, SyncBackend,
          Theme, StartScreen): Die zulässigen Werte stehen damit direkt
          am Attribut, und die UI kann die Auswahlmöglichkeiten aus der
          Enum ableiten.

    Attributes:
        file_path: Pfad zur JSON-Datei, in der die Einstellungen liegen.
    """

    file_path: str

    # --- Metadaten (keine Nutzereinstellungen) ----------------------------

    #: Versionsnummer des Einstellungs-Schemas. Grundlage für zukünftige
    #: Migrationen: Liegt die geladene Datei auf einer älteren Version,
    #: führt `migrate()` die Datei schrittweise auf den aktuellen Stand.
    settings_version: int = 1
    #: App-Version, die die Datei zuletzt geschrieben hat (Fehlersuche,
    #: Erkennung von Downgrades).
    app_version: str = "0.0.0"
    #: UUID des Geräts; dient dem späteren Sync als Konflikt-Kennung
    #: (Last-Writer-Wins pro Einstellung).
    device_id: str = ""
    #: ISO-Zeitstempel der letzten Änderung an den Einstellungen
    #: (Konfliktlösung beim Sync).
    updated_at: str | None = None

    # --- Einstellungen laut ARCHITECTURE.md 3.5 ---------------------------

    #: UI-Sprache.
    language: Annotated[Language, Sync] = Language.DE
    #: Vorausgewähltes Projekt beim Einstempeln.
    active_project_id: Annotated[int | None, Sync] = None
    #: Standard-Pausendauer in Minuten.
    default_break_minutes: Annotated[int, Sync] = 0
    #: CSV-Trennzeichen, frei eintragbar (Textfeld).
    csv_delimiter: Annotated[str, Validated] = ","
    #: Dezimaltrennzeichen im CSV-Export, frei eintragbar (Textfeld).
    csv_decimal_separator: Annotated[str, Validated] = "."
    #: Sync-Backend.
    sync_backend: SyncBackend = SyncBackend.NONE
    #: Sync-Konfiguration (URL, Zugangsdaten).
    sync_config: dict | None = None
    #: ISO-Zeitstempel des letzten Backups.
    last_backup_at: str | None = None
    #: ISO-Zeitstempel des letzten Syncs.
    last_sync_at: Annotated[str | None, Sync] = None
    #: Sichtbare Kacheln + Reihenfolge im Dashboard.
    dashboard_layout: Annotated[list | None, Sync] = None

    # --- Ergänzende, potenziell benötigte Einstellungen -------------------

    #: Farbschema der Oberfläche.
    ui_theme: Theme = Theme.LIGHT
    #: Screen, der beim Start angezeigt wird.
    start_screen: StartScreen = StartScreen.DASHBOARD
    #: Überstundenstand in Stunden, ab dem gewarnt wird.
    overtime_warning_threshold: Annotated[float, Sync, Validated] = 0.0

    def __init__(self, file_path: str) -> None:
        """
        Initialisiert die Einstellungen und lädt sie beim Startup aus JSON.

        Args:
            file_path: Pfad zur JSON-Datei. Existiert sie nicht, werden die
                Default-Werte verwendet und die Datei beim ersten Speichern
                angelegt.
        """
        self.file_path = file_path
        # Load + Migration hier implementieren.

    def __setattr__(self, name: str, value) -> None:
        """
        Zentraler Hook für jede Änderung einer Einstellung.

        Prüft Validated-Attribute über die zugehörige validate_*-Methode,
        aktualisiert `updated_at` und schreibt die Änderung sofort in die
        JSON-Datei.

        Args:
            name: Name des Attributs.
            value: Neuer Wert.

        Raises:
            ValueError: Wenn der Wert eine Validierung nicht besteht.
        """

    # --- Persistenz --------------------------------------------------------

    def load(self) -> None:
        """
        Liest alle Einstellungen aus der JSON-Datei.

        Fehlende Schlüssel behalten ihre Default-Werte; eine fehlende oder
        korrupte Datei führt zu den Defaults (kein Absturz beim Startup).
        """

    def save(self) -> None:
        """
        Schreibt alle Einstellungen atomar in die JSON-Datei.
        """

    # --- Migration ----------------------------------------------------------

    def migrate(self, from_version: int) -> None:
        """
        Wandelt eine ältere Einstellungsdatei auf die aktuelle
        `settings_version` um.

        Wird von `load()` aufgerufen, wenn die Datei eine ältere
        `settings_version` trägt. Jede Version zwischen from_version und
        `settings_version` wird nacheinander angewendet; danach wird die
        Datei einmal gespeichert.

        Args:
            from_version: Versionsnummer der geladenen Datei.
        """

    # --- Validierung (freie Textfelder) ------------------------------------

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
        Liefert nur die GLOBALen (Sync-markierten) Einstellungen.

        Returns:
            Wörterbuch mit allen Einstellungen, deren Annotation den
            Sync-Marker trägt.
        """

    def apply_sync_payload(self, payload: dict) -> None:
        """
        Übernimmt empfangene globale Einstellungen (Last-Writer-Wins).

        Args:
            payload: Wörterbuch mit globalen Einstellungen vom Sync-Backend.
        """
