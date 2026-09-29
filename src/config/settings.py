"""
Application configuration settings.

All user-adjustable configuration values are centralized here.

The Settings dataclass defines code-level defaults. Persistence
functions at the bottom of this file load and save user-specific
overrides in a JSON file in the platform-appropriate config directory:

    Windows: %APPDATA%\\ReferenceChecker\\config.json
    macOS:   ~/Library/Application Support/ReferenceChecker/config.json
    Linux:   ~/.config/ReferenceChecker/config.json
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    """
    Main application configuration.

    These values are intentionally centralized so that deployment settings
    can be changed without modifying application logic.
    """

    # Application
    application_name: str = "Reference Checker"
    version: str = "0.1.0"

    # External APIs
    #
    # Providers that require configuration:
    #   - Google Books: needs an API key (keyless returns 429 with
    #     quota 0). Stored in user config, not here.
    #   - Crossref: keyless, but a contact email gets the "polite
    #     pool" with 2x-3x higher rate limits. Optional.
    #
    # Providers that are keyless and require no settings:
    #   - doi.org (DOI resolver)
    #   - TR Dizin (Turkish academic search)
    #   - OpenLibrary (book search)
    #
    # These are constructed with default arguments in runner.py.
    crossref_email: str | None = None
    google_books_api_key: str | None = None

    # Network
    request_timeout_seconds: int = 20
    max_retries: int = 3

    # Database
    database_path: Path = field(
        default_factory=lambda: Path("data/reference_checker.db")
    )

    # File locations
    output_directory: Path = field(default_factory=lambda: Path("output"))

    log_directory: Path = field(default_factory=lambda: Path("logs"))

    # Processing
    max_workers: int = 4

    # Cache
    cache_expiry_days: int = 30

    def ensure_directories(self) -> None:
        """
        Create required application directories if they do not exist.
        """

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# ---------------------------------------------------------------------------
# User settings persistence
# ---------------------------------------------------------------------------

_CONFIG_APP_DIR = "ReferenceChecker"
_CONFIG_FILENAME = "config.json"


def _config_dir() -> Path:
    """Return the platform-appropriate config directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / _CONFIG_APP_DIR
    if sys.platform == "darwin":
        return (
            Path.home() / "Library" / "Application Support" / _CONFIG_APP_DIR
        )
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / _CONFIG_APP_DIR


def config_path() -> Path:
    """Return the full path to the user config file."""
    return _config_dir() / _CONFIG_FILENAME


def load_user_config() -> dict:
    """Load the user config file. Returns {} if it does not exist."""
    path = config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_user_config(updates: dict) -> None:
    """Merge *updates* into the user config file and save."""
    current = load_user_config()
    current.update(updates)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)


def _set_or_clear(key: str, value: str | None) -> None:
    """
    Set *key* to *value* if truthy, otherwise remove it. Shared by
    the per-setting setters below.
    """
    if value and value.strip():
        save_user_config({key: value.strip()})
        return
    current = load_user_config()
    current.pop(key, None)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)


def get_google_books_api_key() -> str | None:
    """Return the stored Google Books API key, or None."""
    key = load_user_config().get("google_books_api_key")
    return key if isinstance(key, str) and key.strip() else None


def set_google_books_api_key(key: str | None) -> None:
    """Store or clear the Google Books API key."""
    _set_or_clear("google_books_api_key", key)


def get_crossref_email() -> str | None:
    """Return the stored Crossref contact email, or None."""
    email = load_user_config().get("crossref_email")
    return email if isinstance(email, str) and email.strip() else None


def set_crossref_email(email: str | None) -> None:
    """Store or clear the Crossref contact email."""
    _set_or_clear("crossref_email", email)