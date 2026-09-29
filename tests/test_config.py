"""
Tests for application configuration.
"""

from config import Settings


def test_default_settings():
    settings = Settings()

    assert settings.application_name == "Reference Checker"
    assert settings.version == "0.1.0"
    assert settings.request_timeout_seconds == 20


def test_directory_creation(tmp_path):
    settings = Settings(
        database_path=tmp_path / "data" / "test.db",
        output_directory=tmp_path / "output",
        log_directory=tmp_path / "logs",
    )

    settings.ensure_directories()

    assert (tmp_path / "data").exists()
    assert (tmp_path / "output").exists()
    assert (tmp_path / "logs").exists()
