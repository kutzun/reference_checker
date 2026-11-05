"""
Reference match data model.

Represents a candidate match returned by an external verification provider
such as Crossref or OpenAlex.
"""

from dataclasses import dataclass

from .enums import (
    Provider,
    ReferenceType,
)


@dataclass
class ReferenceMatch:
    """
    Represents one possible match for a bibliographic reference.

    This class stores matching evidence only.
    It does not decide whether a reference is verified.
    """

    provider: Provider

    reference_type: ReferenceType = ReferenceType.UNKNOWN

    record_id: str | None = None

    title: str | None = None
    authors: list[str] | None = None

    journal: str | None = None

    # Book and chapter metadata
    book_title: str | None = None
    editors: list[str] | None = None

    publisher: str | None = None
    publisher_location: str | None = None

    isbn: str | None = None
    edition: str | None = None

    year: int | None = None

    doi: str | None = None
    url: str | None = None

    title_similarity: float | None = None
    author_similarity: float | None = None
    book_title_similarity: float | None = None
    editor_similarity: float | None = None
    publisher_similarity: float | None = None

    year_match: bool | None = None
    doi_match: bool | None = None

    overall_score: float | None = None

    evidence_weight: float | None = None

    def has_isbn(
        self,
    ) -> bool:
        """
        Check whether the match contains an ISBN.

        Returns:
            True if ISBN exists, otherwise False.
        """

        return bool(self.isbn)

    def is_strong_match(
        self,
        threshold: float = 0.90,
    ) -> bool:
        """
        Determine whether this candidate exceeds a confidence threshold.

        Args:
            threshold:
                Minimum acceptable match score.

        Returns:
            True if the match score exceeds the threshold.
        """

        if self.overall_score is None:
            return False

        return self.overall_score >= threshold