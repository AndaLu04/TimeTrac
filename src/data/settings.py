import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, get_args, get_origin, get_type_hints

from constants import VERSION


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
    #: ToDo: Von der Anwendung beim Startup mit der echten Version
    #: beschreiben lassen (z. B. aus constants.py / Packaging).
    app_version: Annotated[str, Validated] = VERSION
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
        object.__setattr__(self, "_loading", True)
        object.__setattr__(self, "file_path", file_path)
        self.load()
        object.__setattr__(self, "_loading", False)

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
        if name in ("file_path", "_loading"):
            object.__setattr__(self, name, value)
            return

        validate = getattr(self, f"validate_{name}", None)
        if validate is not None and not validate(value):
            raise ValueError(f"Ungültiger Wert für '{name}': {value!r}")

        object.__setattr__(self, name, value)

        if self._loading:
            return
        object.__setattr__(
            self, "updated_at", datetime.now(timezone.utc).isoformat()
        )
        self.save()

    # --- Persistenz --------------------------------------------------------

    def load(self) -> None:
        """
        Liest alle Einstellungen aus der JSON-Datei.

        Fehlende Schlüssel behalten ihre Default-Werte; eine fehlende oder
        korrupte Datei führt zu den Defaults (kein Absturz beim Startup).
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return  # Keine (lesbare) Datei -> Defaults behalten.

        if not isinstance(data, dict):
            return  # Korruptes Format -> Defaults behalten.

        hints = get_type_hints(self.__class__, include_extras=True)
        for name in hints:
            if name in ("file_path", "_loading") or name not in data:
                continue
            setattr(self, name, self._convert(name, data[name]))

        target_version = type(self).settings_version
        file_version = data.get("settings_version", target_version)
        if isinstance(file_version, int) and file_version < target_version:
            self.migrate(file_version)

    def save(self) -> None:
        """
        Schreibt alle Einstellungen atomar in die JSON-Datei.

        Atomar heißt: Es wird in eine temporäre Datei im selben Verzeichnis
        geschrieben und diese dann per os.replace umbenannt – ein Absturz
        hinterlässt nie eine halb geschriebene Einstellungsdatei.
        """
        if not self.device_id:
            object.__setattr__(self, "device_id", str(uuid.uuid4()))

        hints = get_type_hints(self.__class__, include_extras=True)
        data = {
            name: getattr(self, name)
            for name in hints
            if name not in ("file_path", "_loading")
        }

        directory = os.path.dirname(self.file_path)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory or ".",
            prefix=".settings_",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = tmp_file.name
        os.replace(tmp_path, self.file_path)

    def _convert(self, name: str, value):
        """
        Wandelt einen geladenen JSON-Wert in den annotierten Typ um.

        StrEnum-Attribute werden aus ihrem String-Wert rekonstruiert; bei
        ungültigen Werten greift der Klassen-Default (fehlertolerant).

        Args:
            name: Name des Attributs.
            value: Rohwert aus der JSON-Datei.

        Returns:
            Der konvertierte Wert oder der Rohwert, wenn keine
            Konvertierung nötig/möglich ist (der Aufrufer verwirft
            ungültige Enum-Werte über den ValueError-Pfad nicht – stattdessen
            wird der Default beibehalten).
        """
        hint = get_type_hints(self.__class__, include_extras=True)[name]
        origin = get_origin(hint)
        if origin is Annotated:
            hint = get_args(hint)[0]

        if isinstance(hint, type) and issubclass(hint, StrEnum):
            try:
                return hint(value)
            except ValueError:
                return getattr(self.__class__, name)  # Default bei Müll.
        return value

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
        # ToDo: Zukünftige Migrationsschritte hier ergänzen, z. B.:
        #   if from_version < 2:
        #       self.csv_delimiter = ";"
        target_version = type(self).settings_version
        while from_version < target_version:
            from_version += 1
        object.__setattr__(self, "settings_version", from_version)

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
        return (
            isinstance(value, str)
            and len(value) == 1
            and not value.isalnum()
            and value not in ('"', "'")
        )

    def validate_csv_decimal_separator(self, value: str) -> bool:
        """
        Prüft das Dezimaltrennzeichen.

        Args:
            value: Vorschlag für das Dezimaltrennzeichen.

        Returns:
            True, wenn das Zeichen gültig ist (nur "." oder ",").
        """
        return value in (".", ",")

    def validate_overtime_warning_threshold(self, value: float) -> bool:
        """
        Prüft die Überstunden-Warnschwelle.

        Args:
            value: Vorschlag für die Schwelle in Stunden.

        Returns:
            True, wenn der Wert gültig ist (nicht negativ).
        """
        return isinstance(value, (int, float)) and value >= 0

    # --- Sync-Vorbereitung --------------------------------------------------

    def get_sync_payload(self) -> dict:
        """
        Liefert nur die GLOBALen (Sync-markierten) Einstellungen.

        Returns:
            Wörterbuch mit allen Einstellungen, deren Annotation den
            Sync-Marker trägt. StrEnum-Werte werden als String geliefert.
        """
        return {
            name: getattr(self, name).value
            if isinstance(getattr(self, name), StrEnum)
            else getattr(self, name)
            for name in self._names_with_marker(Sync)
        }

    def apply_sync_payload(self, payload: dict) -> None:
        """
        Übernimmt empfangene globale Einstellungen (Last-Writer-Wins).

        Args:
            payload: Wörterbuch mit globalen Einstellungen vom Sync-Backend.
        """
        for name in self._names_with_marker(Sync):
            if name in payload:
                setattr(self, name, payload[name])

    def _names_with_marker(self, marker: type) -> list[str]:
        """
        Ermittelt alle Attribute, deren Annotation den Marker trägt.

        Args:
            marker: Marker-Klasse (Sync oder Validated).

        Returns:
            Sortierte Liste der passenden Attributnamen.
        """
        hints = get_type_hints(self.__class__, include_extras=True)
        names = []
        for name, hint in hints.items():
            if name in ("file_path", "_loading"):
                continue
            if get_origin(hint) is Annotated and marker in get_args(hint)[1:]:
                names.append(name)
        return sorted(names)
