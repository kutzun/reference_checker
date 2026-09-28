"""
Reference data model.

Represents a single bibliographic reference extracted from a manuscript.
"""

from dataclasses import dataclass, field

from .enums import ReferenceType


@dataclass
class Reference:
    """
    Represents one bibliographic reference.

    The object stores parsed metadata from a bibliography entry.
    Verification logic is intentionally handled elsewhere.
    """

    raw_text: str

    reference_type: ReferenceType = ReferenceType.UNKNOWN

    authors: list[str] = field(default_factory=list)

    title: str | None = None
    journal: str | None = None

    # Book and chapter metadata
    book_title: str | None = None
    editors: list[str] = field(default_factory=list)

    publisher: str | None = None
    publisher_location: str | None = None

    isbn: str | None = None
    edition: str | None = None

    year: int | None = None
    year_suffix: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None

    doi: str | None = None
    url: str | None = None

    def has_doi(self) -> bool:
        """
        Check whether the reference contains a DOI.

        Returns:
            True if DOI exists, otherwise False.
        """

        return bool(self.doi)

    def has_isbn(self) -> bool:
        """
        Check whether the reference contains an ISBN.

        Returns:
            True if ISBN exists, otherwise False.
        """

        return bool(self.isbn)

    def has_minimum_metadata(self) -> bool:
        """
        Determine whether enough information exists for verification.

        Returns:
            True if the reference has basic searchable information.
        """

        return bool(
            self.title
            or self.book_title
            or self.doi
            or self.isbn
        )