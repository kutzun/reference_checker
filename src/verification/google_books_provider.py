"""
Google Books verification provider.

Queries the Google Books API and converts returned Volume resources
into ReferenceMatch objects. Best coverage for Turkish books, but
requires an API key — so the provider declares via `supports()` that
it is only available when a key is configured.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .google_books_client import GoogleBooksClient
from .provider import VerificationProvider


class GoogleBooksProvider(VerificationProvider):
    """
    Verification provider using Google Books metadata.
    """

    def __init__(
        self,
        client: GoogleBooksClient | None = None,
        api_key: str | None = None,
    ):
        self.api_key = api_key

        if client is not None:
            self.client = client
        elif api_key:
            self.client = GoogleBooksClient(api_key=api_key)
        else:
            self.client = None

    @property
    def name(self) -> str:
        return "google_books"

    def supports(self, reference: Reference) -> bool:
        """
        Only run when an API key is configured. Without a key, Google
        Books returns 429 for every request, so the cascade should
        skip this provider entirely.
        """
        return bool(self.api_key)

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        if not self.api_key or self.client is None:
            return []

        query = self._build_query(reference)
        if not query:
            return []

        try:
            response = self.client.search(query)
        except Exception:
            return []

        items = response.get("items", []) or []
        return [self._convert_volume(v) for v in items]

    def _build_query(self, reference: Reference) -> str | None:
        """
        Build a Google Books query from a reference.

        For book chapters, the chapter author is not the book author —
        the book is indexed under its editors. Query by the book title
        alone, with no inauthor filter; an inauthor filter built from
        the chapter author excludes every correct result.

        For everything else (monographs, standalone books), use the
        title and first author's surname. Google Books does its own
        fuzzy matching, so surname alone is enough and avoids issues
        with initials or name-order variations.

        Returns None if the reference has no usable title.
        """
        if reference.reference_type == ReferenceType.BOOK_CHAPTER:
            book_title = reference.book_title
            if not book_title:
                return None
            book_clean = book_title.replace('"', "").strip()
            if not book_clean:
                return None
            return f'intitle:"{book_clean}"'

        title = reference.title or reference.book_title
        if not title:
            return None

        # Quotes inside the query would break the intitle:"..." syntax.
        title_clean = title.replace('"', "").strip()
        if not title_clean:
            return None

        parts = [f'intitle:"{title_clean}"']

        if reference.authors:
            first = reference.authors[0]
            if "," in first:
                surname = first.split(",")[0].strip()
            else:
                surname = first.split()[-1] if first.split() else ""
            if surname:
                parts.append(f'inauthor:"{surname}"')

        return " ".join(parts)

    def _convert_volume(self, volume: dict) -> ReferenceMatch:
        info = volume.get("volumeInfo", {}) or {}

        return ReferenceMatch(
            provider=Provider.GOOGLE_BOOKS,
            reference_type=ReferenceType.BOOK,
            record_id=volume.get("id"),
            title=self._title(info),
            authors=list(info.get("authors", []) or []),
            publisher=info.get("publisher"),
            year=self._year(info),
            isbn=self._isbn(info),
            url=info.get("canonicalVolumeLink") or info.get("infoLink"),
        )

    @staticmethod
    def _title(info: dict) -> str | None:
        title = info.get("title")
        subtitle = info.get("subtitle")
        if title and subtitle:
            return f"{title}: {subtitle}"
        return title

    @staticmethod
    def _year(info: dict) -> int | None:
        date = info.get("publishedDate")
        if not date:
            return None
        year_str = str(date)[:4]
        if year_str.isdigit():
            return int(year_str)
        return None

    @staticmethod
    def _isbn(info: dict) -> str | None:
        """
        Prefer ISBN-13 over ISBN-10. Google Books usually provides
        both; ISBN-13 is the current standard.
        """
        identifiers = info.get("industryIdentifiers", []) or []
        isbn13 = None
        isbn10 = None
        for ident in identifiers:
            kind = ident.get("type")
            value = ident.get("identifier")
            if kind == "ISBN_13" and not isbn13:
                isbn13 = value
            elif kind == "ISBN_10" and not isbn10:
                isbn10 = value
        return isbn13 or isbn10