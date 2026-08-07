"""
Reference Checker enumerations.

This module contains shared enumerations used across the application.
Using enums prevents inconsistent string values throughout the codebase.
"""

from enum import StrEnum


class VerificationStatus(StrEnum):
    """
    Final classification status of a reference verification.
    """

    VERIFIED = "verified"
    MANUAL_REVIEW = "manual_review"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_PROCESSED = "not_processed"


class ReferenceType(StrEnum):
    """
    Supported bibliographic reference types.
    """

    JOURNAL_ARTICLE = "journal_article"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE_PROCEEDING = "conference_proceeding"
    THESIS = "thesis"
    REPORT = "report"
    UNKNOWN = "unknown"


class Provider(StrEnum):
    """
    External verification providers.
    """

    CROSSREF = "crossref"
    OPENALEX = "openalex"
    CACHE = "cache"


class ProcessingStatus(StrEnum):
    """
    Processing state of documents and references.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(StrEnum):
    """
    Application logging levels.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
