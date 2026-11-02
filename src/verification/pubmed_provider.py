"""
PubMed verification provider.

Converts PubMed (NCBI E-utilities) records into ReferenceMatch objects.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
)

from .provider import VerificationProvider
from .pubmed_client import PubMedClient


class PubMedProvider(VerificationProvider):
    """
    Verification provider using PubMed.
    """

    def __init__(
        self,
        client: PubMedClient | None = None,
        email: str | None = None,
        tool: str = "reference-checker",
    ) -> None:
        if client is not None:
            self.client = client
        else:
            self.client = PubMedClient(email=email, tool=tool)

    @property
    def name(self) -> str:
        return "pubmed"

    def search(self, reference: Reference) -> list[ReferenceMatch]:
        records = self.client.search(reference)
        return [self._convert_record(r) for r in records]

    def _convert_record(self, record: dict) -> ReferenceMatch:
        return ReferenceMatch(
            provider=Provider.PUBMED,
            reference_type=self._reference_type(record),
            record_id=record.get("uid"),
            title=self._title(record),
            authors=self._authors(record),
            journal=record.get("fulljournalname") or record.get("source"),
            year=self._year(record),
            doi=self._doi(record),
            url=self._url(record),
        )

    @staticmethod
    def _reference_type(record: dict) -> ReferenceType:
        pubtypes = record.get("pubtype", [])
        if "Book Chapter" in pubtypes:
            return ReferenceType.BOOK_CHAPTER
        if "Book" in pubtypes:
            return ReferenceType.BOOK
        # PubMed indexes biomedical literature; the overwhelming majority
        # of records are journal articles, so this is the honest default.
        return ReferenceType.JOURNAL_ARTICLE

    @staticmethod
    def _title(record: dict) -> str | None:
        title = record.get("title")
        if not title:
            return None
        return title.rstrip().rstrip(".").strip()

    @staticmethod
    def _authors(record: dict) -> list[str]:
        return [
            author["name"]
            for author in record.get("authors", [])
            if author.get("name")
        ]

    @staticmethod
    def _year(record: dict) -> int | None:
        pubdate = (record.get("pubdate") or "").strip()
        if not pubdate:
            return None
        try:
            return int(pubdate.split()[0])
        except ValueError:
            return None

    @staticmethod
    def _doi(record: dict) -> str | None:
        for aid in record.get("articleids", []):
            if aid.get("idtype") == "doi":
                return aid.get("value")
        return None

    @staticmethod
    def _url(record: dict) -> str | None:
        uid = record.get("uid")
        if uid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
        return None