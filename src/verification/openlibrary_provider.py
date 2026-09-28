"""
OpenLibrary verification provider.

Converts OpenLibrary search results into ReferenceMatch objects.
"""

from __future__ import annotations

from models import Reference, ReferenceMatch, ReferenceType, Provider

from .openlibrary_client import OpenLibraryClient
from .provider import VerificationProvider


class OpenLibraryProvider(VerificationProvider):
    """
    Verification provider using OpenLibrary (Internet Archive).
    """

    def __init__(self, client: OpenLibraryClient | None = None) -> None:
        self.client = client or OpenLibraryClient()

    @property
    def name(self) -> str:
        return "openlibrary"

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        """
        Search OpenLibrary for matching works.
        """
        query = reference.title or reference.book_title or reference.raw_text
        if not query:
            return []

        try:
            response = self.client.search(query)
        except Exception:
            return []

        docs = response.get("docs", [])
        if not docs:
            return []

        return [self._convert(doc) for doc in docs]

    def _convert(self, doc: dict) -> ReferenceMatch:
        """
        Convert a single OpenLibrary document into a ReferenceMatch.
        """
        # Authors
        authors = doc.get("author_name") or []
        if isinstance(authors, str):
            authors = [authors]

        # Year – OpenLibrary provides "first_publish_year" as an integer
        year = doc.get("first_publish_year")
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

        # ISBN – use the first available
        isbn_list = doc.get("isbn") or []
        isbn = isbn_list[0] if isbn_list else None

        # Publisher
        publisher_list = doc.get("publisher") or []
        publisher = publisher_list[0] if publisher_list else None

        return ReferenceMatch(
            provider=Provider.OPENLIBRARY,
            reference_type=ReferenceType.BOOK,
            record_id=doc.get("key"),
            title=doc.get("title"),
            authors=authors,
            year=year,
            isbn=isbn,
            publisher=publisher,
            url=f"https://openlibrary.org{doc['key']}" if doc.get("key") else None,
        )