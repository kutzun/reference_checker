"""
Tests for Crossref provider.
"""

from unittest.mock import Mock

from models import Reference
from verification.crossref import (
    CrossrefProvider,
)


def test_crossref_provider_name():

    provider = CrossrefProvider()

    assert provider.name == "crossref"


def test_crossref_empty_search():

    client = Mock()

    client.search.return_value = {"message": {"items": []}}

    provider = CrossrefProvider(client=client)

    reference = Reference(raw_text=("Smith, J. (2020). " "Example article."))

    result = provider.search(reference)

    assert result == []


def test_crossref_parses_results():

    client = Mock()

    client.search.return_value = {
        "message": {
            "items": [
                {
                    "DOI": "10.1234/example",
                    "title": ["Example article"],
                    "author": [
                        {
                            "given": "John",
                            "family": "Smith",
                        }
                    ],
                    "container-title": ["Example Journal"],
                    "published-print": {"date-parts": [[2020]]},
                    "URL": ("https://doi.org/" "10.1234/example"),
                }
            ]
        }
    }

    provider = CrossrefProvider(client=client)

    reference = Reference(raw_text=("Smith, J. (2020). " "Example article."))

    result = provider.search(reference)

    assert len(result) == 1

    match = result[0]

    assert match.doi == ("10.1234/example")

    assert match.title == ("Example article")

    assert match.year == 2020
