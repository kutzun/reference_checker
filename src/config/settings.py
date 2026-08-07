"""
Application configuration settings.

All user-adjustable configuration values are centralized here.
"""

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
    crossref_email: str | None = None
    openalex_api_key: str | None = None

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
