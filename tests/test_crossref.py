"""
Tests for Crossref provider.
"""

from models import Reference
from verification.crossref import (
    CrossrefProvider,
)


def test_crossref_provider_name():

    provider = CrossrefProvider()

    assert provider.name == "crossref"


def test_crossref_empty_search():

    provider = CrossrefProvider()

    reference = Reference(raw_text=("Smith, J. (2020). " "Example article."))

    result = provider.search(reference)

    assert result == []
