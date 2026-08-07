"""
Application logging configuration.

Provides centralized logging setup for the application.
"""

import logging

from config import Settings


def setup_logger(settings: Settings) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        settings:
            Application configuration.

    Returns:
        Configured logger instance.
    """

    logger = logging.getLogger("reference_checker")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    settings.log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = settings.log_directory / "reference_checker.log"

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )

    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
