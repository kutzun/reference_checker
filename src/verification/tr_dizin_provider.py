"""
TR Dizin verification provider.

Queries the TR Dizin search API and converts returned records into
ReferenceMatch objects. Useful for Turkish journal articles that do
not appear in Crossref.
"""
import re
from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .provider import VerificationProvider
from .tr_dizin_client import TrDizinClient


class TrDizinProvider(VerificationProvider):
    """
    Verification provider using TR Dizin metadata.
    """

    def __init__(self, client: TrDizinClient | None = None):
        self.client = client if client is not None else TrDizinClient()

    @property
    def name(self) -> str:
        return "tr_dizin"

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        """
        Search TR Dizin for matching references.

        The query uses the reference's title if available. When there
        is no title, we fall back to raw_text but strip URLs and
        access-date markers — TR Dizin's search engine returns garbage
        (or spam) for URL-laden queries.
        """
        raw = (
            reference.title
            or reference.book_title
            or reference.raw_text
        )
        query = self._clean_query(raw)
        if not query:
            return []

        try:
            sources = self.client.search(query)
        except Exception:
            return []

        return [self._convert_source(src) for src in sources]

    @staticmethod
    def _clean_query(text: str) -> str:
        """
        Remove URL and access-date fragments from a query string.

        Examples:
            "Bis, German Music for Trombones. https://eclassical...
             Erişim Tarihi: 05.06.2026."
                -> "Bis, German Music for Trombones."
        """
        if not text:
            return ""

        # Strip http/https/ftp URLs (up to the next whitespace).
        text = re.sub(r"\b(?:https?|ftp)://\S+", " ", text)

        # Strip Turkish and English access-date markers.
        text = re.sub(
            r"\b(?:Erişim\s+Tarihi|Accessed\s+Date|Retrieved)\s*:?\s*\S+",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        # Strip URNs and other long non-word blocks.
        text = re.sub(r"\burn:\S+", " ", text)

        # Collapse whitespace.
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _convert_source(self, src: dict) -> ReferenceMatch:
        return ReferenceMatch(
            provider=Provider.TR_DIZIN,
            reference_type=self._reference_type(src),
            record_id=str(src.get("id")) if src.get("id") is not None else None,
            title=self._title(src),
            authors=self._authors(src),
            journal=self._journal(src),
            year=self._year(src),
            doi=self._doi(src),
        )

    @staticmethod
    def _reference_type(src: dict) -> ReferenceType:
        doc_type = src.get("docType")
        if doc_type == "PAPER":
            return ReferenceType.JOURNAL_ARTICLE
        if doc_type == "PROJECT":
            return ReferenceType.REPORT
        return ReferenceType.UNKNOWN

    @staticmethod
    def _title(src: dict) -> str | None:
        """
        Pick the Turkish abstract's title if present, else English.
        Never use orderTitle — it has spaces stripped.
        """
        abstracts = src.get("abstracts") or []
        for preferred in ("TUR", "ENG"):
            for ab in abstracts:
                if ab.get("language") == preferred and ab.get("title"):
                    return ab["title"]
        # Fallback: first available title.
        for ab in abstracts:
            if ab.get("title"):
                return ab["title"]
        return None

    @staticmethod
    def _authors(src: dict) -> list[str]:
        authors = []
        for a in src.get("authors", []):
            name = a.get("name")
            if name:
                authors.append(name)
        return authors

    @staticmethod
    def _journal(src: dict) -> str | None:
        journal = src.get("journal") or {}
        return journal.get("name")

    @staticmethod
    def _year(src: dict) -> int | None:
        year = src.get("publicationYear")
        if isinstance(year, int):
            return year
        return None

    @staticmethod
    def _doi(src: dict) -> str | None:
        doi = src.get("doi")
        return doi if doi else None