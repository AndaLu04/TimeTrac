import json

import pytest

from data.settings import (
    Language,
    Settings,
    StartScreen,
    SyncBackend,
    Theme,
)


@pytest.fixture
def settings_file(tmp_path):
    return str(tmp_path / "settings.json")


def test_defaults_without_file(settings_file):
    """Ohne Datei gelten die Klassen-Defaults."""
    settings = Settings(settings_file)
    assert settings.language == Language.DE
    assert settings.default_break_minutes == 0
    assert settings.sync_backend == SyncBackend.NONE
    assert settings.ui_theme == Theme.LIGHT
    assert settings.start_screen == StartScreen.DASHBOARD


def test_change_persists_immediately(settings_file):
    """Jede Änderung wird sofort in die JSON-Datei geschrieben."""
    settings = Settings(settings_file)
    settings.language = Language.EN
    with open(settings_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert data["language"] == "en"
    assert Settings(settings_file).language == Language.EN


def test_load_roundtrip(settings_file):
    """Geladene Werte überleben den Neustart (neue Instanz)."""
    settings = Settings(settings_file)
    settings.default_break_minutes = 30
    settings.active_project_id = 42
    settings.dashboard_layout = ["week", "month"]
    reloaded = Settings(settings_file)
    assert reloaded.default_break_minutes == 30
    assert reloaded.active_project_id == 42
    assert reloaded.dashboard_layout == ["week", "month"]


def test_corrupt_file_falls_back_to_defaults(settings_file):
    """Korruptes JSON führt zu Defaults, kein Absturz."""
    with open(settings_file, "w", encoding="utf-8") as file:
        file.write("{kein valides json")
    settings = Settings(settings_file)
    assert settings.language == Language.DE


def test_invalid_enum_value_falls_back_to_default(settings_file):
    """Unbekannter Enum-Wert in der Datei -> Default, kein Absturz."""
    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump({"language": "fr"}, file)
    settings = Settings(settings_file)
    assert settings.language == Language.DE


def test_validation_rejects_invalid_delimiter(settings_file):
    """Ungültiges CSV-Trennzeichen wird abgelehnt, nichts gespeichert."""
    settings = Settings(settings_file)
    with pytest.raises(ValueError):
        settings.csv_delimiter = "5"
    with pytest.raises(ValueError):
        settings.csv_delimiter = "ab"
    with pytest.raises(ValueError):
        settings.csv_delimiter = '"'
    assert settings.csv_delimiter == ","


def test_validation_accepts_valid_delimiter(settings_file):
    settings = Settings(settings_file)
    settings.csv_delimiter = ";"
    assert settings.csv_delimiter == ";"


def test_decimal_separator_validation(settings_file):
    settings = Settings(settings_file)
    settings.csv_decimal_separator = ","
    assert settings.csv_decimal_separator == ","
    with pytest.raises(ValueError):
        settings.csv_decimal_separator = "x"


def test_overtime_threshold_validation(settings_file):
    settings = Settings(settings_file)
    with pytest.raises(ValueError):
        settings.overtime_warning_threshold = -1.0
    settings.overtime_warning_threshold = 10.5
    assert settings.overtime_warning_threshold == 10.5


def test_updated_at_set_on_change(settings_file):
    settings = Settings(settings_file)
    assert settings.updated_at is None
    settings.language = Language.EN
    assert settings.updated_at is not None


def test_device_id_generated_once(settings_file):
    settings = Settings(settings_file)
    settings.language = Language.EN
    first = settings.device_id
    assert first
    settings.language = Language.DE
    assert settings.device_id == first


def test_sync_payload_contains_only_synced(settings_file):
    settings = Settings(settings_file)
    payload = settings.get_sync_payload()
    assert payload == {
        "active_project_id": None,
        "dashboard_layout": None,
        "default_break_minutes": 0,
        "language": "de",
        "last_sync_at": None,
        "overtime_warning_threshold": 0.0,
    }


def test_apply_sync_payload(settings_file):
    settings = Settings(settings_file)
    settings.apply_sync_payload({"language": "en", "default_break_minutes": 20})
    assert settings.language == Language.EN
    assert settings.default_break_minutes == 20


def test_apply_sync_payload_ignores_local(settings_file):
    settings = Settings(settings_file)
    settings.apply_sync_payload({"ui_theme": "dark"})
    assert settings.ui_theme == Theme.LIGHT


def test_migration_bumps_version(settings_file):
    """Ältere Datei-Version wird auf die aktuelle Version gehoben."""
    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump({"settings_version": 0, "language": "en"}, file)
    settings = Settings(settings_file)
    assert settings.settings_version == Settings.settings_version
    assert settings.language == Language.EN


def test_save_is_atomic_no_tmp_leftover(settings_file):
    settings = Settings(settings_file)
    settings.language = Language.EN
    import os

    directory = os.path.dirname(settings_file)
    leftovers = [f for f in os.listdir(directory) if f.endswith(".tmp")]
    assert leftovers == []
