"""
Tests for PubMed verification provider.
"""

from models import (
    Provider,
    Reference,
    ReferenceType,
)

from verification.pubmed_provider import (
    PubMedProvider,
)


class MockPubMedClient:
    """
    Fake PubMed client for testing.
    """

    def __init__(self, records):
        self.records = records

    def search(
        self,
        reference: Reference,
    ) -> list[dict]:
        return self.records


def _reference():

    return Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
        year=2020,
    )


def test_pubmed_provider_returns_matches():

    records = [
        {
            "uid": "12345",
            "title": "Writing Research.",
            "authors": [{"name": "Smith J"}],
            "source": "J Test",
            "fulljournalname": "Journal of Testing",
            "pubdate": "2020",
            "pubtype": ["Journal Article"],
            "articleids": [
                {"idtype": "doi", "value": "10.1234/example"},
            ],
        }
    ]

    provider = PubMedProvider(
        client=MockPubMedClient(records),
    )

    matches = provider.search(_reference())

    assert len(matches) == 1

    match = matches[0]

    assert match.provider == Provider.PUBMED

    assert match.record_id == "12345"

    # PubMed titles carry a trailing period; it should be stripped.
    assert match.title == "Writing Research"

    assert match.authors == [
        "Smith J",
    ]

    assert match.journal == "Journal of Testing"

    assert match.year == 2020

    assert match.doi == "10.1234/example"

    assert match.url == "https://pubmed.ncbi.nlm.nih.gov/12345/"

    assert match.reference_type == ReferenceType.JOURNAL_ARTICLE


def test_pubmed_provider_maps_book_chapter():

    records = [
        {
            "uid": "99999",
            "title": "A Chapter.",
            "authors": [{"name": "Doe J"}],
            "pubdate": "2019",
            "pubtype": ["Book Chapter"],
            "articleids": [],
        }
    ]

    provider = PubMedProvider(
        client=MockPubMedClient(records),
    )

    matches = provider.search(_reference())

    assert matches[0].reference_type == ReferenceType.BOOK_CHAPTER


def test_pubmed_provider_returns_empty_for_no_records():

    provider = PubMedProvider(
        client=MockPubMedClient([]),
    )

    matches = provider.search(_reference())

    assert matches == []