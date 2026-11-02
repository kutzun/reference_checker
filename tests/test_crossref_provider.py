"""
Tests for Crossref verification provider.
"""

from models import (
    Provider,
    Reference,
)

from verification.crossref_provider import (
    CrossrefProvider,
)


class MockCrossrefClient:
    """
    Fake Crossref client for testing.
    """

    def search(
        self,
        query: str,
    ) -> dict:
        return {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/example",
                        "title": [
                            "Writing Research",
                        ],
                        "author": [
                            {
                                "given": "John",
                                "family": "Smith",
                            }
                        ],
                        "publisher": "Example Publisher",
                        "published-print": {
                            "date-parts": [
                                [
                                    2020,
                                ]
                            ]
                        },
                        "ISBN": [
                            "9781234567890",
                        ],
                        "URL": "https://doi.org/10.1234/example",
                    }
                ]
            }
        }


def test_crossref_provider_returns_matches():

    reference = Reference(
        raw_text="Smith, J. (2020). Writing Research.",
        title="Writing Research",
        year=2020,
    )

    provider = CrossrefProvider(
        client=MockCrossrefClient(),
    )

    matches = provider.search(reference)

    assert len(matches) == 1

    match = matches[0]

    assert match.provider == Provider.CROSSREF

    assert match.title == "Writing Research"

    assert match.authors == [
        "John Smith",
    ]

    assert match.publisher == "Example Publisher"

    assert match.year == 2020

    assert match.isbn == "9781234567890"