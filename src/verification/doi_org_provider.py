"""
doi.org verification provider.

Resolves a reference's DOI via doi.org and converts the returned
CSL-JSON into a ReferenceMatch. Only runs for references that carry
a DOI — declared via the `supports` hook used by the cascade.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .doi_org_client import DoiOrgClient
from .provider import VerificationProvider


class DoiOrgProvider(VerificationProvider):
    """
    Verification provider using doi.org resolution.
    """

    def __init__(self, client: DoiOrgClient | None = None):
        self.client = client if client is not None else DoiOrgClient()

    @property
    def name(self) -> str:
        return "doi_org"

    def supports(self, reference: Reference) -> bool:
        """
        Only run when the reference carries a DOI.
        """
        return bool(reference.doi)

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        """
        Resolve the reference's DOI. Returns a single-element list on
        success, or an empty list if the DOI does not resolve.
        """
        if not reference.doi:
            return []

        try:
            record = self.client.resolve(reference.doi)
        except Exception:
            return []

        if not record:
            return []

        return [self._convert_record(record)]

    def _convert_record(self, record: dict) -> ReferenceMatch:
        return ReferenceMatch(
            provider=Provider.DOI_ORG,
            reference_type=self._reference_type(record),
            record_id=record.get("DOI"),
            title=self._title(record),
            authors=self._authors(record),
            journal=self._journal(record),
            publisher=record.get("publisher"),
            year=self._year(record),
            doi=record.get("DOI"),
            url=record.get("URL"),
            isbn=self._isbn(record),
        )

    @staticmethod
    def _reference_type(record: dict) -> ReferenceType:
        mapping = {
            "journal-article": ReferenceType.JOURNAL_ARTICLE,
            "book": ReferenceType.BOOK,
            "book-chapter": ReferenceType.BOOK_CHAPTER,
            "proceedings-article": ReferenceType.CONFERENCE_PROCEEDING,
            "report": ReferenceType.REPORT,
            "dissertation": ReferenceType.THESIS,
        }
        return mapping.get(record.get("type"), ReferenceType.UNKNOWN)

    @staticmethod
    def _title(record: dict) -> str | None:
        # CSL-JSON title is a plain string, not a list.
        title = record.get("title")
        if isinstance(title, list):
            return title[0] if title else None
        return title

    @staticmethod
    def _journal(record: dict) -> str | None:
        container = record.get("container-title")
        if isinstance(container, list):
            return container[0] if container else None
        return container

    @staticmethod
    def _authors(record: dict) -> list[str]:
        authors = []
        for author in record.get("author", []):
            # CSL-JSON allows "literal" for institutional authors.
            literal = author.get("literal")
            if literal:
                authors.append(literal)
                continue
            name = " ".join(
                filter(None, [author.get("given"), author.get("family")])
            )
            if name:
                authors.append(name)
        return authors

    @staticmethod
    def _year(record: dict) -> int | None:
        # Prefer "issued" (canonical publication date in CSL-JSON).
        issued = record.get("issued") or record.get("published-print")
        if not issued:
            return None
        parts = issued.get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
        return None

    @staticmethod
    def _isbn(record: dict) -> str | None:
        isbn = record.get("ISBN")
        if isinstance(isbn, list):
            return isbn[0] if isbn else None
        return isbn