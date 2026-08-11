"""
Crossref verification provider.

Converts Crossref records into ReferenceMatch objects.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .crossref_client import CrossrefClient
from .provider import VerificationProvider


class CrossrefProvider(VerificationProvider):
    """
    Verification provider using Crossref metadata.
    """

    def __init__(
        self,
        client: CrossrefClient | None = None,
    ):
        """
        Initialize Crossref provider.

        Args:
            client:
                Crossref API client.
        """

        self.client = (
            client
            if client is not None
            else CrossrefClient()
        )

    @property
    def name(
        self,
    ) -> str:
        """
        Provider identifier.

        Returns:
            Provider name.
        """

        return "crossref"

    def search(
        self,
        reference: Reference,
    ) -> list[ReferenceMatch]:
        """
        Search Crossref for matching references.

        Args:
            reference:
                Parsed reference.

        Returns:
            Candidate matches.
        """

        response = self.client.search(
            reference.title
            or reference.book_title
            or reference.raw_text
        )

        items = (
            response
            .get("message", {})
            .get("items", [])
        )

        matches = []

        for item in items:
            matches.append(
                self._convert_item(item)
            )

        return matches

    def _convert_item(
        self,
        item: dict,
    ) -> ReferenceMatch:
        """
        Convert Crossref record into ReferenceMatch.
        """

        return ReferenceMatch(
            provider=Provider.CROSSREF,
            reference_type=self._reference_type(item),
            record_id=item.get("DOI"),
            title=self._first_title(item),
            authors=self._authors(item),
            book_title=self._book_title(item),
            editors=self._editors(item),
            publisher=item.get("publisher"),
            publisher_location=item.get("publisher-location"),
            year=self._year(item),
            doi=item.get("DOI"),
            url=item.get("URL"),
            isbn=self._first_isbn(item),
            edition=self._edition(item),
        )

    @staticmethod
    def _reference_type(
        item: dict,
    ) -> ReferenceType:
        """
        Convert Crossref type into internal reference type.

        Returns:
            Matching ReferenceType enum value.
        """

        mapping = {
            "journal-article": ReferenceType.JOURNAL_ARTICLE,
            "book": ReferenceType.BOOK,
            "book-chapter": ReferenceType.BOOK_CHAPTER,
            "proceedings-article": ReferenceType.CONFERENCE_PROCEEDING,
            "report": ReferenceType.REPORT,
            "dissertation": ReferenceType.THESIS,
        }

        return mapping.get(
            item.get("type"),
            ReferenceType.UNKNOWN,
        )

    @staticmethod
    def _first_title(
        item: dict,
    ) -> str | None:
        """
        Extract first title.
        """

        titles = item.get(
            "title",
            [],
        )

        if titles:
            return titles[0]

        return None

    @staticmethod
    def _book_title(
        item: dict,
    ) -> str | None:
        """
        Extract container title for chapters.
        """

        containers = item.get(
            "container-title",
            [],
        )

        if containers:
            return containers[0]

        return None

    @staticmethod
    def _authors(
        item: dict,
    ) -> list[str]:
        """
        Extract authors.
        """

        authors = []

        for author in item.get(
            "author",
            [],
        ):
            name = " ".join(
                filter(
                    None,
                    [
                        author.get("given"),
                        author.get("family"),
                    ],
                )
            )

            if name:
                authors.append(name)

        return authors

    @staticmethod
    def _editors(
        item: dict,
    ) -> list[str]:
        """
        Extract editors.
        """

        editors = []

        for editor in item.get(
            "editor",
            [],
        ):
            name = " ".join(
                filter(
                    None,
                    [
                        editor.get("given"),
                        editor.get("family"),
                    ],
                )
            )

            if name:
                editors.append(name)

        return editors

    @staticmethod
    def _year(
        item: dict,
    ) -> int | None:
        """
        Extract publication year.
        """

        date = (
            item.get("published-print")
            or item.get("published-online")
            or item.get("created")
        )

        if not date:
            return None

        parts = date.get(
            "date-parts",
            [],
        )

        if parts and parts[0]:
            return parts[0][0]

        return None

    @staticmethod
    def _first_isbn(
        item: dict,
    ) -> str | None:
        """
        Extract first ISBN.
        """

        isbns = item.get(
            "ISBN",
            [],
        )

        if isbns:
            return isbns[0]

        return None

    @staticmethod
    def _edition(
        item: dict,
    ) -> str | None:
        """
        Extract edition information.
        """

        return item.get("edition-number")