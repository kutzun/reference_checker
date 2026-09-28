"""
Tests for application logging.
"""

from app_logging import setup_logger
from config import Settings


def test_logger_creation(tmp_path):
    settings = Settings(
        log_directory=tmp_path / "logs",
    )

    logger = setup_logger(settings)

    logger.info("Test log message")

    log_file = tmp_path / "logs" / "reference_checker.log"

    assert log_file.exists()
