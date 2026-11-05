"""
Crossref verification provider.

Queries Crossref metadata services and converts
results into ReferenceMatch objects.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
)

from .crossref_client import CrossrefClient
from .provider import VerificationProvider


class CrossrefProvider(
    VerificationProvider,
):
    """
    Verification provider using Crossref.
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

        self.client = client if client is not None else CrossrefClient()

    @property
    def name(self) -> str:
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
                Parsed reference metadata.

        Returns:
            Candidate matches.
        """

        query = self._build_query(reference)

        if query is None:
            return []

        response = self.client.search(query)

        return self._parse_results(response)

    def _build_query(
        self,
        reference: Reference,
    ) -> str | None:
        """
        Build Crossref search query.
        """

        if reference.title:
            return reference.title

        if reference.raw_text:
            return reference.raw_text

        return None

    def _parse_results(
        self,
        response: dict,
    ) -> list[ReferenceMatch]:
        """
        Convert Crossref response items
        into ReferenceMatch objects.

        Args:
            response:
                Crossref API response.

        Returns:
            Candidate matches.
        """

        items = response.get("message", {}).get("items", [])

        matches = []

        for item in items:
            matches.append(self._create_match(item))

        return matches

    def _create_match(
        self,
        item: dict,
    ) -> ReferenceMatch:
        """
        Convert one Crossref item.

        Args:
            item:
                Crossref work record.

        Returns:
            ReferenceMatch object.
        """

        title = None

        if item.get("title"):
            title = item["title"][0]

        authors = []

        for author in item.get(
            "author",
            [],
        ):
            name_parts = [
                author.get("given"),
                author.get("family"),
            ]

            name = " ".join(part for part in name_parts if part)

            if name:
                authors.append(name)

        journal = None

        if item.get("container-title"):
            journal = item["container-title"][0]

        year = None

        published = item.get(
            "published-print",
        ) or item.get(
            "published-online",
        )

        if published:
            date_parts = published.get(
                "date-parts",
                [],
            )

            if date_parts:
                if date_parts[0]:
                    year = date_parts[0][0]

        return ReferenceMatch(
            provider=Provider.CROSSREF,
            record_id=item.get("DOI"),
            title=title,
            authors=authors or None,
            journal=journal,
            year=year,
            doi=item.get("DOI"),
            url=item.get("URL"),
        )
